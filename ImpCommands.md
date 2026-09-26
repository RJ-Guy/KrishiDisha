# 🌾 KrishiDisha (कृषि दिशा) — Important Commands Reference

A quick reference guide for environment management, backend services, database migrations, frontend development, and infrastructure.

---

## 1. ⚡ UV Environment & Package Management

### Initial Sync & Setup
```bash
# Install and synchronize all dependencies from pyproject.toml into .venv
uv sync
```

### Manual Environment Activation
```powershell
# Windows (PowerShell)
.\.venv\Scripts\activate

# Windows (Command Prompt)
.\.venv\Scripts\activate.bat
```
```bash
# Linux / macOS
source .venv/bin/activate
```

### Package Operations
```bash
# Add a new package
uv add <package_name>

# Add a package with specific version constraint
uv add "<package_name>>=1.0.0"

# Add development-only dependencies
uv add --dev pytest ruff

# Remove an existing package
uv remove <package_name>

# Re-create virtual environment with Python 3.12 if needed
uv venv --python 3.12
```

---

## 2. 🚀 Backend (FastAPI) Execution

### Start API Server
```bash
# Run server with live reload via uv (recommended from project root)
uv run uvicorn app.main:app --reload --port 8000

# Run directly (if .venv is already activated)
uvicorn app.main:app --reload --port 8000

# Expose to local network (accessible from other devices / LAN)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive Documentation & Health Endpoints
- **Service Base:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **API Endpoints Prefix:** `/api`

---

## 3. 🗄️ Database & Seed Pipeline

### Initialize DB & Ingest Kaggle / Agmarknet Data
```bash
# Run database schema creation, SIH demonstration scenarios, & Kaggle CSV ingestion
uv run python -m app.database.seed_data

# Or with activated virtual environment
python -m app.database.seed_data
```

### Using PostgreSQL Container (Optional)
```bash
# 1. Start PostgreSQL Docker container
docker compose up -d

# 2. Point to PostgreSQL (PowerShell)
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/krishidisha"

# 3. Run database migrations / seed against PostgreSQL
uv run python -m app.database.seed_data
```

---

## 4. 💻 Frontend (React + Vite) Development

```bash
# Navigate to Frontend directory
cd Frontend

# Install node dependencies
npm install

# Start local Vite development server (http://localhost:5173)
npm run dev

# Build production bundle
npm run build

# Preview production build locally
npm run preview
```

---

## 5. 🐳 Docker & Infrastructure

```bash
# Start PostgreSQL service in detached mode
docker compose up -d

# View container logs
docker compose logs -f postgres

# Stop all container services
docker compose down

# Stop and wipe volume data (fresh start)
docker compose down -v
```
