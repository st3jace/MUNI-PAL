# Muni-Pal BFMS

Bond Facility Management System - Evidence-first, advisor-grade platform for municipal bond structuring.

## Quick Start

### Backend

```bash
# Install dependencies
pip install -e ".[dev]"

# Run server (SQLite dev mode)
uvicorn munipal.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Documentation

When running in debug mode, API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
