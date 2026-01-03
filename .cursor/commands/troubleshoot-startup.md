# Troubleshoot Startup Issues

Resolve common startup issues for CryptoOrchestrator.

## Quick Diagnostics

Run comprehensive diagnostics:
```bash
npm run verify:startup
```

This checks:
- System requirements
- Dependencies
- Environment variables
- Database connection
- Service health

## Common Issues

### Port Already in Use

**Windows:**
```bash
# Find process using port
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

**Solution**: Change port in `.env` or kill the process

### Database Connection Failed

1. **Check PostgreSQL is running**
   ```bash
   # Windows
   services.msc  # Check PostgreSQL service

   # Linux/Mac
   sudo systemctl status postgresql
   ```

2. **Verify DATABASE_URL in `.env`**
   ```bash
   # Should be: postgresql://user:password@localhost:5432/dbname
   ```

3. **Test connection**
   ```bash
   python scripts/utilities/database-health.py
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

### Dependencies Missing

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install --legacy-peer-deps
   ```

3. **Verify dependencies**
   ```bash
   npm run setup:deps
   ```

### Environment Variables Missing

1. **Create `.env` file**
   ```bash
   cp .env.example .env
   ```

2. **Validate environment**
   ```bash
   npm run validate:env
   ```

3. **Check required variables**
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `ENVIRONMENT`

### Service Health Issues

1. **Check all services**
   ```bash
   npm run check:services
   ```

2. **Check individual services**
   ```bash
   # Backend
   curl http://localhost:8000/health

   # Frontend
   curl http://localhost:5173
   ```

3. **View service logs**
   - Backend: Check terminal output
   - Frontend: Check browser console
   - Database: Check PostgreSQL logs

## Step-by-Step Troubleshooting

1. **Run diagnostics**
   ```bash
   npm run verify:startup
   ```

2. **Check environment**
   ```bash
   npm run validate:env
   ```

3. **Check dependencies**
   ```bash
   npm run setup:deps
   ```

4. **Check database**
   ```bash
   python scripts/utilities/database-health.py
   ```

5. **Check services**
   ```bash
   npm run check:services
   ```

## Still Having Issues?

1. Check logs for specific error messages
2. Review [Troubleshooting Guide](../docs/TROUBLESHOOTING_RUNTIME.md)
3. Verify system requirements (Python 3.12+, Node.js 18+)
4. Check firewall/antivirus isn't blocking ports
5. Review recent changes to code or configuration
