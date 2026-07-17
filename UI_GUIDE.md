# 🎨 SelFlow UI Guide - Complete Interaction Guide

## 🎯 Dashboard Overview

Your Streamlit dashboard now has **4 main tabs** with full LLM interaction and data visualization support.

---

## 📍 TAB 1: 🤖 AI Query Hub (Main Interaction)

### **What You Can Do Here:**

1. **Ask Questions in Natural Language**
   - Type any question about your data
   - Examples:
     - "Show me all transactions from today"
     - "What is the total transaction volume by type?"
     - "Count failed transactions"
     - "Show me high-value transactions"

2. **See Generated SQL**
   - Click "📝 Generated SQL" to expand
   - See exactly what SQL Llama generated
   - Useful for learning and debugging

3. **View Results**
   - Interactive table with all results
   - Sortable and searchable columns
   - Shows row count and column count

4. **Export Data**
   - Download as CSV
   - Download as JSON
   - Download as Excel (.xlsx)

5. **Try Example Queries**
   - Click any example button to auto-fill
   - Pre-written queries to learn how it works

### **How It Works:**

```
You Type Question
       ↓
Backend Receives
       ↓
Local Llama Converts to SQL
       ↓
PostgreSQL Executes
       ↓
Results Display Here
```

### **Status Indicators:**
- 🟢 Database: healthy → Connected & ready
- 🟢 API: Online → Backend responding
- 🟢 Llama: Ready → Local model available

---

## 📈 TAB 2: Analytics Dashboard

### **Real-Time Metrics:**
- Total Transactions count
- System status (Active/Inactive)
- Database status (Online/Offline)
- Live timestamp

### **Quick Analytics:**
- Pre-built queries for common analysis
- Transaction Summary
- Daily Volume
- Customer Analysis
- Top Performers

---

## 📊 TAB 3: Data Explorer

### **Database Schema**
Shows the structure of your `staging_transactions` table:
- Column names
- Data types
- Descriptions

### **Common SQL Queries**
Pre-written examples:
- Row count
- Group by transaction type
- Group by status
- Top 10 amounts

### **API Endpoints Reference**
Shows all available endpoints with URLs

---

## 📚 TAB 4: Help & Documentation

### **Getting Started Guide**
Step-by-step setup instructions

### **FAQ Section**
Common questions answered

### **Troubleshooting**
- Ollama not running
- Cannot connect to backend
- Slow response times
- No data in results

### **System Information**
Technical details about components

---

## 🚀 Quick Start

### **Step 1: Refresh Dashboard**
If you haven't already, open:
```
http://localhost:8501
```

### **Step 2: Check System Status**
Look at the **left sidebar** - All indicators should be green:
- 🟢 Database: healthy
- 🟢 API: Online
- 🟢 Llama: Ready

### **Step 3: Click "🤖 AI Query Hub" Tab**

### **Step 4: Enter a Question**
```
"Show all transactions from today"
```

### **Step 5: Click "🔍 Query Data" Button**

### **Step 6: Wait for Results**
- Shows "Llama is generating SQL..." while thinking
- Then displays results

### **Step 7: Explore Results**
- View the table
- Click "SQL" to see generated query
- Download as CSV/JSON/Excel

---

## 💡 Example Queries

### **Transaction Analysis**
```
"Show me transaction counts by type"
"What is the total transaction volume by status?"
"Count all completed transactions"
```

### **Time-Based**
```
"Show me transactions from today"
"What are the daily transaction totals?"
"Count transactions from this week"
```

### **Value Analysis**
```
"Show me all high-value transactions"
"What is the average transaction amount?"
"Top 10 largest transactions"
```

### **Customer Analysis**
```
"How many unique customers?"
"Show me customer transaction counts"
"Which customers have failed transactions?"
```

---

## 🔧 Troubleshooting UI Issues

### **"Cannot connect to backend" Error**

**Solution:**
```bash
# Check if backend is running
docker compose ps

# Should show: selcom-backend ... Up ... (healthy)
# If not, restart:
docker compose restart selcom-backend
```

### **"Ollama not running" Error**

**Solution - On Windows Host (NOT in Docker):**
```powershell
# Open PowerShell as Administrator
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")
# Close PowerShell
# Reopen PowerShell
ollama run llama2
```

### **Query Returns No Results**

**Solutions:**
1. Check if database has data:
   - In AI Query Hub, ask: "How many total transactions?"
   
2. Try different phrasing:
   - Instead of: "Give me transactions"
   - Try: "Show me all transactions"

3. Check the generated SQL:
   - Click "📝 Generated SQL" to see the query
   - May show you what Llama interpreted

### **Slow Response Times**

**Solutions:**
1. Ensure Ollama has enough resources (2GB+ free)
2. Normal Llama response time: 2-5 seconds
3. Restart Ollama: `ollama serve`
4. Try smaller model: `ollama pull orca-mini`

### **Missing Example Buttons**

**Solution:**
Refresh the page: Press F5 or Ctrl+R

---

## 🎨 UI Features Explained

### **Sidebar (Left Side)**
- System Status indicators (real-time)
- Quick stats (total records)
- Documentation links

### **Main Content Area**
- Query input text area
- Expandable SQL viewer
- Results table with metrics
- Download buttons

### **Query Button**
- Primary blue button
- Click after entering question
- Shows spinner while processing

### **Results Display**
- Formatted table
- Sortable columns
- Row count displayed
- Column count displayed

### **Export Options**
- CSV: For Excel/Google Sheets
- JSON: For API/programmatic use
- Excel: Native Excel format

---

## 📊 Data Visualization Tips

### **Create Custom Visualizations**

The AI Query Hub returns data that you can analyze. After getting results:

1. **Copy data to external tool** (Excel, Tableau, PowerBI)
2. **Or ask Llama to structure data for visualization**

Example query:
```
"Show me transaction counts by type in a table format"
```

This will return:
```
type          | count
--------------|-------
PAYMENT       | 1250
CASH_IN       | 850
CASH_OUT      | 630
```

---

## 🔒 Security Reminder

✅ **All data stays local**
- No data sent to external APIs
- Llama runs on your Windows host
- PostgreSQL runs in Docker

✅ **Query Processing**
- Llama generates SQL locally
- Database executes locally
- Results returned locally

✅ **No Cloud Dependencies**
- Works offline after initial model download
- No API keys needed
- No rate limits

---

## 📞 Getting Help

### **In-App Help**
1. Go to **📚 Help & Documentation** tab
2. Find your issue in Troubleshooting section
3. Follow the solution

### **Command Line Help**
```bash
# View backend logs
docker logs selcom-backend -f

# View frontend logs  
docker logs selcom-frontend -f

# Check service health
docker compose ps
```

### **Check API Docs**
```
http://localhost:8000/docs
```

Interactive Swagger UI showing all endpoints

---

## 💾 Data Download Guide

### **CSV Format**
- Best for: Excel, Google Sheets
- Command: Click "📥 Download CSV"
- File: `query_results.csv`

### **JSON Format**
- Best for: APIs, Python, scripting
- Command: Click "📥 Download JSON"
- File: `query_results.json`

### **Excel Format**
- Best for: Native Excel sheets
- Command: Click "📥 Download Excel"
- File: `query_results.xlsx`

---

## 🎯 Workflow Example

### **Scenario: "I want to analyze customer transactions"**

1. **Open Dashboard**: http://localhost:8501
2. **Click AI Query Hub tab**
3. **Ask Question**: "Show me all customer transactions with amounts"
4. **View Results**: Table displays all data
5. **Review SQL**: Click to see generated query
6. **Metrics**: See row count (how many records)
7. **Download**: Export as CSV for further analysis
8. **Analyze**: Use Excel/Python to create visualizations

---

## ✨ Tips & Tricks

### **Tip 1: Use Specific Column Names**
❌ Bad: "Show me data"
✅ Good: "Show me transaction_id, amount, status"

### **Tip 2: Be Clear About Filters**
❌ Bad: "High transactions"
✅ Good: "Show me transactions with amount > 1000"

### **Tip 3: Ask for Aggregations**
❌ Bad: "Count stuff"
✅ Good: "Count transactions grouped by status"

### **Tip 4: Use Time Frames**
❌ Bad: "Recent transactions"
✅ Good: "Show me transactions from the last 7 days"

### **Tip 5: Download Large Results**
- For 1000+ rows, download to CSV
- Easier to work with in Excel/Python

---

## 🚀 Next Steps

1. ✅ **Setup Ollama** on Windows host
2. ✅ **Try first query** in AI Query Hub
3. ✅ **Download results** as CSV
4. ✅ **Create visualizations** in Excel
5. ✅ **Explore different queries** to learn patterns

---

**Version:** 1.1.0 (Full UI & LLM Integration)
**Last Updated:** 2025-01-14
**Status:** ✅ Ready for Production Use

**Happy querying! 🎉**
