import io
import polars as pl
from sqlalchemy import create_engine, text
from sqlalchemy_utils import database_exists, create_database

from backend.etl.logger import logger


class PostgresLoader:
    def __init__(self, connection_uri: str):
        self.connection_uri = connection_uri
        self.engine = create_engine(connection_uri)
        
    def init_schema(self):
        """
        Initializes database and schema structure with appropriate keys and indices.
        Ensures IDEMPOTENCY by creating tables safely.
        """
        if not database_exists(self.engine.url):
            logger.info("Database does not exist. Creating...")
            create_database(self.engine.url)
            logger.success("Database created successfully.")

        # Target table schema definition (matches PostgreSQL production naming conventions)
        schema_sql = """
        CREATE TABLE IF NOT EXISTS staging_transactions (
            transaction_id VARCHAR(100),
            amount DOUBLE PRECISION,
            type VARCHAR(50),
            status VARCHAR(50),
            created_at TIMESTAMP,
            customer_id VARCHAR(100),
            transaction_hour INTEGER,
            day_of_week INTEGER,
            transaction_date DATE,
            value_tier VARCHAR(20),
            PRIMARY KEY (transaction_id)
        );
        
        -- Indexes to accelerate heavy query analytics and partition pruning
        CREATE INDEX IF NOT EXISTS idx_transactions_date ON staging_transactions(transaction_date);
        CREATE INDEX IF NOT EXISTS idx_transactions_type ON staging_transactions(type);
        """
        with self.engine.begin() as conn:
            conn.execute(text(schema_sql))
        logger.info("Database schema and indexes initialized.")

    def load_data(self, df: pl.DataFrame):
        """
        Ultra-fast bulk insert using PostgreSQL's COPY protocol.
        Achieves IDEMPOTENCY by using a temporary staging table to merge data safely.
        Dynamically handles columns to ensure strict alignment.
        """
        self.init_schema()

        logger.info("Initiating high-speed bulk insert via psycopg2 copy_from...")
        
        # 1. Target Schema column map to types for dynamic Staging Table generation
        schema_column_types = {
            "transaction_id": "VARCHAR(100)",
            "amount": "DOUBLE PRECISION",
            "type": "VARCHAR(50)",
            "status": "VARCHAR(50)",
            "created_at": "TIMESTAMP",
            "customer_id": "VARCHAR(100)",
            "transaction_hour": "INTEGER",
            "day_of_week": "INTEGER",
            "transaction_date": "DATE",
            "value_tier": "VARCHAR(20)"
        }
        
        # Clean down the columns list to strictly match what actually exists in the incoming cleaned Polars DataFrame
        available_cols = [col for col in schema_column_types.keys() if col in df.columns]
        
        # 2. Convert Polars DataFrame to a fast, in-memory binary buffer (CSV format)
        buffer = io.BytesIO()
        df.select(available_cols).write_csv(buffer, include_header=False, separator=",")
        buffer.seek(0)

        # 3. Build dynamic SQL definitions based strictly on available columns
        temp_table_fields = ", ".join([f"{col} {schema_column_types[col]}" for col in available_cols])
        cols_joined = ", ".join(available_cols)
        
        # Generate the dynamic excluded set for the UPSERT block
        # It updates all fields *except* the primary key (transaction_id)
        update_set_clause = ", ".join([
            f"{col} = EXCLUDED.{col}" for col in available_cols if col != "transaction_id"
        ])

        # 4. Extract raw DBAPI connection to execute PostgreSQL COPY command
        raw_conn = self.engine.raw_connection()
        try:
            with raw_conn.cursor() as cursor:
                # Create the transaction-scoped temporary staging table matching incoming DataFrame columns
                logger.info("Creating transient staging layer matching DataFrame structure...")
                cursor.execute(f"""
                    CREATE TEMP TABLE temp_stage (
                        {temp_table_fields}
                    ) ON COMMIT DROP;
                """)
                
                # Bulk stream data directly from RAM into the Temp Table
                logger.info("Streaming dataset to Postgres memory buffer...")

                # Wrap the binary stream in a text interface for psycopg2's COPY protocol
                text_buffer = io.TextIOWrapper(buffer, encoding="utf-8")
                
                cursor.copy_from(
                    file=text_buffer,  # FIX: Pass the TextIOWrapper stream, not the raw binary BytesIO buffer
                    table="temp_stage", 
                    sep=",", 
                    null="", 
                    columns=available_cols
                )
                
                # Perform idempotent UPSERT (Insert, merge updates on conflict)
                # DISTINCT ON ensures that if any duplicates exist in the temp stage itself, Postgres collapses them
                logger.info("Merging and updating duplicate target records (UPSERT)...")
                upsert_query = f"""
                INSERT INTO staging_transactions ({cols_joined})
                SELECT DISTINCT ON (transaction_id) {cols_joined}
                FROM temp_stage
                ON CONFLICT (transaction_id) DO UPDATE SET
                    {update_set_clause};
                """
                cursor.execute(upsert_query)
                
            raw_conn.commit()
            logger.success(f"Bulk-loaded {df.height} records into 'staging_transactions' table cleanly!")
        except Exception as e:
            raw_conn.rollback()
            logger.error(f"Error during bulk insert operation: {e}")
            raise e
        finally:
            raw_conn.close()