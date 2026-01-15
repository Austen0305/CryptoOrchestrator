# Developer Setup Guide

## Prerequisites
- **Python 3.12+** (Backend)
- **Node.js 24+** (Frontend)
- **Rust 1.80+** (Signer)
- **Docker** (Infrastructure)

## Backend Setup (Granian + Polars)

```bash
cd server_fastapi
pip install -r requirements.txt
python serve_granian.py
```

## Frontend Setup (React 19)

```bash
cd client
npm install
npm run dev
```

## Running Tests

```bash
# Backend
pytest

# Frontend
cd client && npm run test
```
