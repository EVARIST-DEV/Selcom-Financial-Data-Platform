# SelFlow Local Llama Setup Guide

## 5-Minute Setup

### Step 1: Setup Ollama (Windows Host)
```powershell
# Run as Administrator
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")
# Close PowerShell and reopen it
ollama run llama2
```
✅ You should see model loading and running on `0.0.0.0:11434`

### Step 2: Start Docker Services
```bash
cd ./selcom-financial-data-platform
docker compose up -d
docker compose ps
```
✅ All three services should show `Up (healthy)`

### Step 3: Access Dashboard
Open: **http://localhost:8501**

---

## Test the System

### Test 1: Check Backend Health
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"online","services":{"database":"healthy","api":"healthy"}}`

### Test 2: Query Llama via API
```bash
curl -X POST http://localhost:8000/ai/query \
  -H "Content-Type: application/json" \
  -d '{"prompt":"How many total transactions?"}'
```

### Test 3: Use Streamlit Dashboard
1. Go to http://localhost:8501
2. Click **🤖 AI Query Hub** tab
3. Type: "Show me all transactions"
4. Click **Query Data**
5. ✅ You should see SQL and results

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot reach Llama" | `ollama serve` on Windows host (not in Docker) |
| Slow response | Increase Docker memory to 4GB+ |
| No results | Check `docker logs selcom-backend` |
| Frontend won't load | Try `docker compose restart selcom-frontend` |

---

## Environment Variables

Edit `.env` to customize:

```bash
# Use different Llama model
LLAMA_MODEL=mistral

# Change database password
DB_PASSWORD=yourpassword

# Adjust logging
LOG_LEVEL=DEBUG
```

Then restart: `docker compose restart`

---

## Example Queries

Try these in the AI Query Hub:

- "Total transactions today"
- "Top 5 customers by volume"
- "Transaction success rate"
- "Average transaction amount"
- "Count by transaction type"

---

## Stopping Services

```bash
# Stop all services
docker compose down

# Remove database (CAREFUL!)
docker compose down -v
```

---

**That's it! Your local Llama-powered financial platform is ready.** 🚀
