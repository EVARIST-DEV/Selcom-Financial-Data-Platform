import polars as pl
from backend.etl.logger import logger


class DataTransformer:
    """
    Cleans, enriches, and deduplicates financial transactions using Polars.
    """

    HIGH_VALUE_THRESHOLD = 200000

    @staticmethod
    def transform(df: pl.DataFrame) -> pl.DataFrame:
        logger.info("Transforming dataset with Polars...")

        # 1. Column Renaming Map
        rename_map = {
            "nameOrig": "sender_account",
            "nameDest": "receiver_account",
            "oldbalanceOrg": "sender_balance_before",
            "newbalanceOrig": "sender_balance_after",
            "oldbalanceDest": "receiver_balance_before",
            "newbalanceDest": "receiver_balance_after",
            "isFraud": "is_fraud",
            "isFlaggedFraud": "is_flagged_fraud",
        }

        # Filter out rename mapping keys that don't exist in the df to prevent errors
        valid_rename = {k: v for k, v in rename_map.items() if k in df.columns}
        df_renamed = df.rename(valid_rename)

        # ==========================================
        # CLEANING & DEDUPLICATION (The Core Guardrails)
        # ==========================================
        
        # A. Deduplicate: Remove exact identical records first
        original_count = df_renamed.height
        df_unique = df_renamed.unique()
        dedup_count = original_count - df_unique.height
        if dedup_count > 0:
            logger.warning(f"Deduplication: Dropped {dedup_count} exact duplicate records.")

        # B. Handle Null Values: Impute empty fields so loading doesn't fail
        df_clean = df_unique.with_columns([
            pl.col("sender_account").fill_null("UNKNOWN_SENDER").cast(pl.String),
            pl.col("receiver_account").fill_null("UNKNOWN_RECEIVER").cast(pl.String),
            pl.col("amount").fill_null(0.0).cast(pl.Float64),
        ])

        # 2. Conditional fallback for transaction_id
        # We replace the slow Python UUID list comprehension with high-speed vectorized hashes.
        if "transaction_id" in df_clean.columns:
            id_expression = pl.col("transaction_id")
        else:
            logger.info("Generating lightning-fast parallelized transaction hash IDs...")
            # Generating a unique, deterministic hash based on transaction attributes
            # This runs in milliseconds across millions of rows instead of minutes!
            id_expression = (
                (
                    pl.col("sender_account") + "_" +
                    pl.col("receiver_account") + "_" +
                    pl.col("step").cast(pl.String) + "_" +
                    pl.col("amount").cast(pl.String)
                )
                .hash(seed=42)
                .cast(pl.String)
                .alias("transaction_id")
            )

        # 3. Fast Parallel Column Evaluation
        df_transformed = df_clean.with_columns(
            # Attach or keep the transaction IDs
            id_expression,

            # Derived temporal columns matching schema requirements
            (pl.col("step") % 24).cast(pl.Int32).alias("transaction_hour"),
            ((pl.col("step") // 24) % 7 + 1).cast(pl.Int32).alias("day_of_week"),
            
            # Map the simulation step to a concrete Timestamp/Date starting from a base reference point
            (pl.datetime(2026, 1, 1) + pl.duration(hours=pl.col("step"))).alias("created_at"),
            
            # Derived high-value columns
            (pl.col("amount") >= DataTransformer.HIGH_VALUE_THRESHOLD).alias("is_high_value"),

            # Conditional tier logic matching staging schema strings
            pl.when(pl.col("amount") >= DataTransformer.HIGH_VALUE_THRESHOLD)
            .then(pl.lit("HIGH"))
            .otherwise(pl.lit("LOW"))
            .alias("value_tier"),

            # Balance changes
            (pl.col("sender_balance_before") - pl.col("sender_balance_after")).alias("sender_balance_change"),
            (pl.col("receiver_balance_after") - pl.col("receiver_balance_before")).alias("receiver_balance_change"),
        ).with_columns([
            # Extract date representation from calculated timestamp
            pl.col("created_at").dt.date().alias("transaction_date"),
            
            # Fallbacks for status and type if missing from source data mapping
            pl.col("type").fill_null("UNKNOWN") if "type" in df_clean.columns else pl.lit("UNKNOWN").alias("type"),
            pl.lit("COMPLETED").alias("status")
        ])

        # C. Primary Key Deduplication: Ensure strict ID uniqueness across dataset
        df_transformed = df_transformed.unique(subset=["transaction_id"], keep="last")

        logger.success(f"Transformation complete! Cleaned and engineered features for {df_transformed.height} items.")
        return df_transformed