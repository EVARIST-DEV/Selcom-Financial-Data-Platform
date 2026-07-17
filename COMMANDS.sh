#!/bin/bash
# SelFlow Complete Command Reference

# ============================================
# SETUP (ONE TIME ONLY)
# ============================================

# 1. On Windows Host - Setup Ollama
# Run PowerShell as Administrator:
# [Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")
# Close PowerShell and reopen
# ollama run llama2

# 2. Start Docker Services
cd ./selcom-financial-data-platform
docker compose up -d

# ============================================
# DAILY USE
# ============================================

# View all services status
docker compose ps

# Open Dashboard
# Browser: http://localhost:8501

# View logs
docker compose logs -f              # All services
docker logs selcom-backend -f       # Backend only
docker logs selcom-frontend -f      # Frontend only
docker logs selcom-postgres -f      # Database only

# ============================================
# API TESTING
# ============================================

# Test backend health
curl http://localhost:8000/health

# Test database metrics
curl http://localhost:8000/metrics

# Test Llama query (requires Ollama running)
curl -X POST http://localhost:8000/ai/query \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Show me all transactions"}'

# Interactive API docs
# Browser: http://localhost:8000/docs

# ============================================
# TROUBLESHOOTING
# ============================================

# Restart specific service
docker compose restart selcom-backend
docker compose restart selcom-frontend
docker compose restart selcom-postgres

# Rebuild images (after code changes)
docker compose build --no-cache

# Hard reset (removes volumes)
docker compose down -v
docker compose up -d

# Check if Ollama is accessible from container
docker exec selcom-backend python -c \
  "import requests; print(requests.get('http://host.docker.internal:11434/api/tags').json())"

# Database shell access
docker exec -it selcom-postgres psql -U postgres -d selcom_db

# Database query
docker exec selcom-postgres psql -U postgres -d selcom_db -c \
  "SELECT COUNT(*) as total_rows FROM staging_transactions;"

# ============================================
# DEPLOYMENT
# ============================================

# Build for production
docker compose build backend
docker compose build frontend

# Push to registry
docker tag selcom-financial-data-platform-backend:latest myregistry/backend:latest
docker tag selcom-financial-data-platform-frontend:latest myregistry/frontend:latest
docker push myregistry/backend:latest
docker push myregistry/frontend:latest

# ============================================
# OLLAMA (Windows Host PowerShell)
# ============================================

# List models
ollama list

# Download model
ollama pull llama2
ollama pull mistral
ollama pull neural-chat

# Remove model
ollama rm llama2

# Run model standalone
ollama run llama2

# ============================================
# DATABASE BACKUP/RESTORE
# ============================================

# Backup
docker exec selcom-postgres pg_dump -U postgres selcom_db > backup.sql

# Restore
cat backup.sql | docker exec -i selcom-postgres psql -U postgres -d selcom_db

# ============================================
# MONITORING
# ============================================

# Resource usage (memory, CPU, network)
docker stats

# Container logs with timestamps
docker compose logs --timestamps

# View specific number of log lines
docker logs selcom-backend --tail 100

# Follow logs in real-time
docker logs selcom-backend -f

# ============================================
# CLEANUP
# ============================================

# Stop all services
docker compose down

# Stop and remove volumes (DESTRUCTIVE)
docker compose down -v

# Clean up unused Docker resources
docker system prune -a

# Remove specific image
docker image rm selcom-financial-data-platform-backend

# ============================================
# ENVIRONMENT VARIABLES
# ============================================

# View env vars inside container
docker exec selcom-backend env | grep LOCAL_LLM

# Update .env then restart
# vim .env
docker compose restart

# ============================================
# QUICK REFERENCE
# ============================================

# All services healthy?
docker compose ps | grep healthy

# Quick health check
curl -s http://localhost:8000/health | jq .

# Frontend accessible?
curl -I http://localhost:8501

# Database accessible?
docker exec selcom-postgres pg_isready

# Llama accessible from backend?
docker exec selcom-backend curl -s http://host.docker.internal:11434/api/tags
