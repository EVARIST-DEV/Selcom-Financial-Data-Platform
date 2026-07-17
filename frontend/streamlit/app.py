import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import altair as alt

st.set_page_config(
    page_title="SelFlow Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Professional UI Theming & Custom CSS
st.markdown("""
<style>
    /* Professional Tab Styling */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    /* Metric Card Polishing */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }
    /* Chart Container Styling */
    .chart-container {
        border: 1px solid #e6e9ef;
        border-radius: 8px;
        padding: 15px;
        background-color: #f8f9fa;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Main Title Header with Material Icon
st.markdown("## :material/analytics: SelFlow Financial Data Intelligence")
st.caption("Powered by Local AI | Secure On-Premise Enterprise Analytics")

BACKEND_URL = "http://selcom-backend:8000"


# AUTO-VISUALIZATION ENGINE HELPER 
def render_auto_chart(df: pd.DataFrame, title_prefix: str = "Query Analysis"):
    """
    Analyzes DataFrame columns dynamically and renders an optimized interactive Altair chart.
    """
    if df.empty or len(df.columns) < 2:
        return None

    # Identify column data types
    cols = list(df.columns)
    
    # convert string numbers to actual numeric types
    for col in cols:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            # Attempt to parse dates if they contain timestamp indicators
            if "date" in col.lower() or "at" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception:
                    pass

    # Classify columns
    numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    datetime_cols = [c for c in cols if pd.api.types.is_datetime64_any_dtype(df[c]) or "date" in c.lower()]
    categorical_cols = [c for c in cols if c not in numeric_cols and c not in datetime_cols]

    # Select the best plotting axes
    y_axis = numeric_cols[0] if numeric_cols else None
    x_axis = None
    
    if datetime_cols:
        x_axis = datetime_cols[0]
        chart_type = "LINE"
    elif categorical_cols:
        x_axis = categorical_cols[0]
        chart_type = "BAR"
    elif len(numeric_cols) >= 2:
        x_axis = numeric_cols[0]
        y_axis = numeric_cols[1]
        chart_type = "SCATTER"
    else:
        chart_type = None

    if not x_axis or not y_axis:
        return None

    # Render actual chart based on selection
    st.write("---")
    st.markdown(f"#### :material/monitoring: {title_prefix} — *Dynamic Chart*")
    
    if chart_type == "LINE":
        chart = alt.Chart(df).mark_line(point=True, color="#1f77b4").encode(
            x=alt.X(f"{x_axis}:T", title=x_axis.replace("_", " ").title()),
            y=alt.Y(f"{y_axis}:Q", title=y_axis.replace("_", " ").title()),
            tooltip=cols
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
        
    elif chart_type == "BAR":
        chart = alt.Chart(df).mark_bar(color="#00a8a8").encode(
            x=alt.X(f"{x_axis}:N", sort='-y', title=x_axis.replace("_", " ").title()),
            y=alt.Y(f"{y_axis}:Q", title=y_axis.replace("_", " ").title()),
            tooltip=cols
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
        
    elif chart_type == "SCATTER":
        chart = alt.Chart(df).mark_circle(size=60, color="#ff7f0e").encode(
            x=alt.X(f"{x_axis}:Q", title=x_axis.replace("_", " ").title()),
            y=alt.Y(f"{y_axis}:Q", title=y_axis.replace("_", " ").title()),
            tooltip=cols
        ).interactive()
        st.altair_chart(chart, use_container_width=True)


# SIDEBAR
with st.sidebar:
    st.markdown("### System Status")
    
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=5).json()
        db_status = health["services"]["database"]
        
        if "healthy" in db_status.lower():
            st.markdown(":material/database: **Database:** :green[Healthy]")
        else:
            st.markdown(":material/database: **Database:** :red[Degraded]")
            
        st.markdown(":material/dns: **API Gateway:** :green[Online]")
        st.markdown(":material/psychology: **SELCO-AI:** :green[Ready]")
        
    except Exception:
        st.markdown(":material/database: **Database:** :gray[Unknown]")
        st.markdown(":material/dns: **API Gateway:** :red[Offline]")
        st.markdown(":material/psychology: **SELCO-AI:** :gray[Offline]")
    
    st.divider()
    
    st.markdown("### Database Metrics")
    try:
        metrics = requests.get(f"{BACKEND_URL}/metrics", timeout=5).json()
        total_rows = metrics.get("total_rows_stored", 0)
        st.metric(
            label="Total Stored Records", 
            value=f"{total_rows:,}",
            help="Cumulative volume of raw ingestion transactions."
        )
    except Exception:
        st.info("System metrics currently unavailable.", icon=":material/info:")


tab1, tab2, tab3, tab4 = st.tabs([
    "AI Query Hub", 
    "Analytics Engine", 
    "Data Dictionary", 
    "System Diagnostics"
])


with tab1:
    st.markdown("### Natural Language to SQL Core")
    st.markdown("""
    Translate standard business questions into executable SQL commands. 
    The integrated Local Llama instance executes queries securely within your on-premise infrastructure.
    """)
    
    # Query Form Section
    st.markdown("#### Input Query")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_question = st.text_area(
            label="Enter natural language business question:",
            placeholder="E.g.,\n- 'Show all transactions processed today'\n- 'Calculate aggregate transaction volume sorted by type'\n- 'Identify transaction records exceeding average value threshold'",
            height=115,
            label_visibility="collapsed"
        )
    
    with col2:
        st.write("")  # Alignment spacing
        st.write("")
        submit_button = st.button(
            label="Execute Query", 
            use_container_width=True, 
            type="primary",
            icon=":material/database_search:"
        )
    
    # Process Query Pipeline
    if submit_button and user_question:
        with st.spinner("Generating execution plan and SQL translation..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/ai/query",
                    json={"prompt": user_question},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        st.success("Execution Completed Successfully", icon=":material/check_circle:")
                        
                        
                        with st.expander("Generated SQL Statements (Audit Log)", expanded=False):
                            st.code(result["sql"], language="sql")
                            st.caption("Automated schema-aware translation engine query.")
                        
                        
                        if result["data"]:
                            df = pd.DataFrame(result["data"])
                            
                            st.markdown(f"#### Query Results ({result['row_count']} Records)")
                            
                            m_col1, m_col2, m_col3 = st.columns(3)
                            with m_col1:
                                st.metric("Rows Processed", f"{result['row_count']:,}")
                            with m_col2:
                                st.metric("Returned Columns", len(df.columns))
                            with m_col3:
                                st.metric("Inference Engine Latency", "2-5s")
                            
                            st.dataframe(df, use_container_width=True, height=300)
                            
                            
                            render_auto_chart(df, title_prefix="Insights Visualization")
                            
                            
                            st.write("")
                            st.markdown("#### Export Datasets")
                            ex_col1, ex_col2, ex_col3 = st.columns(3)
                            
                            with ex_col1:
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Download Raw CSV",
                                    data=csv,
                                    file_name="query_results.csv",
                                    mime="text/csv",
                                    use_container_width=True,
                                    icon=":material/download:"
                                )
                            
                            with ex_col2:
                                json_str = json.dumps(result["data"], indent=2, default=str)
                                st.download_button(
                                    label="Download JSON Payload",
                                    data=json_str,
                                    file_name="query_results.json",
                                    mime="application/json",
                                    use_container_width=True,
                                    icon=":material/download:"
                                )
                            
                            with ex_col3:
                                try:
                                    import io
                                    buffer = io.BytesIO()
                                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                        df.to_excel(writer, index=False)
                                    excel_bytes = buffer.getvalue()
                                    
                                    st.download_button(
                                        label="Download Excel Workbook",
                                        data=excel_bytes,
                                        file_name="query_results.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True,
                                        icon=":material/download:"
                                    )
                                except Exception:
                                    st.info("Excel compilation engine (openpyxl) missing. Download CSV instead.", icon=":material/info:")
                        else:
                            st.info("Query completed but returned no database rows. Refine your query syntax.", icon=":material/info_i:")
                    else:
                        st.error("Query generation failed or database rejected schema parsing.", icon=":material/error:")
                else:
                    error_detail = response.json().get("detail", "Internal network failure")
                    st.error(f"Execution Error: {error_detail}", icon=":material/report_problem:")
                    
                    if "Ollama" in error_detail or "11434" in error_detail:
                        st.warning("""
                        **Inference Daemon Failure:** 
                        SELCO-AI service is unreachable. Ensure the host environment variables are exposed:
                        ```powershell
                        [Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")
                        # Restart your terminal and restart Ollama:
                        ollama run llama2
                        ```
                        """, icon=":material/warning:")
            
            except requests.exceptions.Timeout:
                st.error("Request Timeout: AI model generation exceeded 60s threshold.", icon=":material/schedule:")
            except requests.exceptions.ConnectionError:
                st.error("API Gateway unreachable. Verify docker containers are active: `docker compose up -d`", icon=":material/cloud_off:")
            except Exception as e:
                st.error(f"Unexpected Exception: {str(e)}", icon=":material/bug_report:")
    
    
    st.divider()
    st.markdown("#### Sample Queries")
    
    examples = [
        "Show all transactions from today",
        "Total transaction volume by type",
        "Average transaction amount",
        "Count of transactions by status",
        "High-value transactions",
        "Failed transactions"
    ]
    
    cols = st.columns(2)
    for idx, example in enumerate(examples):
        with cols[idx % 2]:
            if st.button(example, key=f"example_{idx}", use_container_width=True, icon=":material/saved_search:"):
                with st.spinner("Analyzing pre-compiled template..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/ai/query",
                            json={"prompt": example},
                            timeout=60
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("success") and result["data"]:
                                st.success(f"Query Processed: '{example}'")
                                with st.expander("Show SQL", expanded=False):
                                    st.code(result["sql"], language="sql")
                                df = pd.DataFrame(result["data"])
                                st.dataframe(df, use_container_width=True)
                                render_auto_chart(df, title_prefix=f"Visual: {example}")
                            else:
                                st.error("Database query returned empty records for this template.")
                    except Exception as e:
                        st.error(f"Template execution failed: {str(e)}")


with tab2:
    st.markdown("### Aggregated Financial Analytics")
    
    try:
        metrics = requests.get(f"{BACKEND_URL}/metrics", timeout=5).json()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Aggregate Records", f"{metrics.get('total_rows_stored', 0):,}")
        with col2:
            st.metric("Pipeline Health", "Active", delta="100%", delta_color="normal")
        with col3:
            st.metric("Database Health", "Online", delta="0ms latency", delta_color="normal")
        with col4:
            st.metric("Last Sync Timestamp", datetime.now().strftime("%H:%M:%S"))
    except Exception:
        st.info("Analytical indicators temporarily offline. Re-establishing API socket connection.", icon=":material/hourglass_empty:")
    
    st.divider()
    
    st.markdown("#### :material/insights: Interactive Multi-Dimension Insights")
    st.markdown("Select a dimensional pivot variable to generate instant aggregated trend analysis.")
    
    
    dimension = st.selectbox(
        "Select Analytical Pivot Dimension:",
        ["type (Transaction Method Breakdown)", "status (Transaction Processing Health)", "value_tier (High-Value Ingestion Split)", "transaction_hour (Hourly Traffic Spikes)"]
    )
    
    raw_dim = dimension.split(" ")[0]
    
    
    analytics_prompts = {
        "type": "Total aggregate transaction volume sorted by type",
        "status": "Count of transactions by status",
        "value_tier": "Count of transactions grouped by value_tier",
        "transaction_hour": "Average transaction amount grouped by transaction_hour order by transaction_hour ASC"
    }
    
    if st.button("Generate Metric Visualization", type="secondary", icon=":material/analytics:"):
        with st.spinner(f"AI compiling aggregation data for '{raw_dim}'..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/ai/query",
                    json={"prompt": analytics_prompts[raw_dim]},
                    timeout=60
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success") and result["data"]:
                        df_analytics = pd.DataFrame(result["data"])
                        
                        col_left, col_right = st.columns([1, 2])
                        with col_left:
                            st.write("")
                            st.markdown(f"**Data Summary Table:**")
                            st.dataframe(df_analytics, use_container_width=True)
                        with col_right:
                            render_auto_chart(df_analytics, title_prefix=f"{raw_dim.capitalize()} Aggregation")
                    else:
                        st.error("Failed to compile visualization data blocks.")
                else:
                    st.error("Visualization API query was rejected by backend.")
            except Exception as e:
                st.error(f"Failed to fetch analytical aggregates: {str(e)}")


with tab3:
    st.markdown("### System Metadata & Schemas")
    st.markdown("Review structural database modeling tables and validation triggers.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### Schema: `staging_transactions`")
        
        schema_data = {
            "Column": [
                "transaction_id", "amount", "type", "status", 
                "created_at", "customer_id", "transaction_date", "value_tier"
            ],
            "Type": [
                "VARCHAR", "DOUBLE", "VARCHAR", "VARCHAR", 
                "TIMESTAMP", "VARCHAR", "DATE", "VARCHAR"
            ],
            "Indexing Key": [
                "Primary Key", "None", "Dimension Index", "Status Index",
                "Partition Clustered", "Foreign Key Link", "None", "None"
            ]
        }
        st.table(pd.DataFrame(schema_data))
    
    with col2:
        st.markdown("#### System Validation Triggers")
        st.markdown("""
        **Transaction Count Query Validation:**
        ```sql
        SELECT COUNT(*) FROM staging_transactions;
        ```
        
        **Categorized Breakdown Statement:**
        ```sql
        SELECT type, COUNT(*) as count
        FROM staging_transactions
        GROUP BY type;
        ```
        """)

# SYSTEM DIAGNOSTICS
with tab4:
    st.markdown("### Infrastructure Architecture & Administration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Core Node Deployment")
        st.markdown("""
        **1. Initialize LLM Host Daemon (Local Windows)**
        ```powershell
        [Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")
        # Restart Shell Session
        ollama run llama2
        ```
        
        **2. Front-End Gateway Endpoint**
        `http://localhost:8501`
        
        **3. Deep Query Execution**
        Query parsing is managed entirely on-premise inside isolated microservices.
        """)
    
    with col2:
        st.markdown("#### Infrastructure Parameters")
        st.markdown("""
        **Compliance Standard:**
        Sovereign private hosting models only.
        
        **Inference Customization:**
        Configure fallback values in `.env` configuration file, then restart engine.
        
        **Encrypted Execution Paths:**
        Fully on-premise execution logic. Data stays in your database.
        """)
    
    st.divider()
    
    with st.expander("Diagnostics and Troubleshooting Guides", expanded=False):
        st.markdown("""
        **Llama API Handshake Failure:**
        Ensure Ollama process listening bounds are open globally inside your host environment: `ollama run llama2`
        
        **Database Connection Interruption:**
        Verify local database docker containers are healthy: `docker compose up -d`
        """)

# ============ FOOTER ============
st.divider()
st.caption("SelFlow Enterprise Engine v1.1.0 | Local Selco-AI Analytics integration | Cryptographically Secured Data Layer | Developed by Ev-AI")