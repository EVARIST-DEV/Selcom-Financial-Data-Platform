import os
import json
import re
import requests
from loguru import logger

LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://host.docker.internal:11434/api/generate")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama3")

# We upgrade the Schema Context to enforce JSON response payloads
SCHEMA_CONTEXT = """
You are a strict PostgreSQL and Analytics assistant for the SelFlow Financial Data Platform.
Your job is to translate the user's natural language question into an optimized SQL query and define how to visualize the results.

You must ALWAYS return your output in a raw JSON format (do NOT wrap it in markdown code blocks).

### JSON Schema Output Format:
{
  "sql": "The raw PostgreSQL query, ending with a semicolon.",
  "chart_type": "BAR" | "LINE" | "SCATTER" | "METRIC" | "NONE",
  "x_axis": "column_name_for_x_axis or null",
  "y_axis": "column_name_for_y_axis or null",
  "chart_title": "Descriptive title for the chart"
}

Rules:
1. To protect memory on our 6,000,000+ record dataset, always aggregate your data (e.g., using SUM, COUNT, AVG, GROUP BY) when asked about trends.
2. If the user request implies raw records, always include a 'LIMIT 100' clause.
3. If they ask for a single statistic, use chart_type 'METRIC'.

Here is the database schema for the table 'staging_transactions':
- transaction_id (VARCHAR) - Primary Key
- amount (DOUBLE PRECISION) - Transaction amount
- type (VARCHAR) - Transaction type (e.g., 'PAYMENT', 'CASH_IN', 'CASH_OUT')
- status (VARCHAR) - Transaction status (e.g., 'COMPLETED', 'FAILED', 'PENDING')
- created_at (TIMESTAMP) - Timestamp of transaction
- customer_id (VARCHAR) - Customer identifier
- transaction_hour (INTEGER) - Derived hour (0-23)
- day_of_week (INTEGER) - Derived day (0=Monday, 6=Sunday)
- transaction_date (DATE) - Derived transaction date (YYYY-MM-DD)
- value_tier (VARCHAR) - Value segmentation ('HIGH_VALUE', 'NORMAL')
"""

class LlamaCopilot:
    @staticmethod
    def generate_analytics_payload(user_prompt: str) -> dict:
        """
        Sends user query to Ollama, returns parsed JSON query and visualization details.
        """
        full_prompt = (
            f"### Context:\n{SCHEMA_CONTEXT}\n\n"
            f"### User Request:\n\"{user_prompt}\"\n\n"
            f"### JSON Output (Strict raw JSON only):"
        )
        
        try:
            response = requests.post(
                LOCAL_LLM_URL,
                json={
                    "model": LLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                    }
                },
                timeout=30
            )
            
            raw_text = response.json().get("response", "").strip()
            
            # Defensive markdown stripping
            raw_text = re.sub(r"```(?:json)?", "", raw_text).strip()
            
            # Parse the JSON directive
            payload = json.loads(raw_text)
            logger.info(f"Generated AI Analytics Payload: {payload}")
            return payload
            
        except Exception as e:
            logger.error(f"Failed to generate analytics payload: {e}")
            # Safe default fallback
            return {
                "sql": "SELECT * FROM staging_transactions LIMIT 10;",
                "chart_type": "NONE",
                "x_axis": None,
                "y_axis": None,
                "chart_title": "Fallback Data View"
            }