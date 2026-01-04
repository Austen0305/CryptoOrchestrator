# Get Full Startup Error

The error is happening AFTER routers load. Let's see the full traceback:

```bash
# Get the complete error with traceback
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -B 30 "Application startup failed" | head -40

# Or get all errors and exceptions
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -E "ERROR|Exception|Traceback|Failed" | tail -30

# Check what happens in lifespan/startup
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i "lifespan\|startup\|database\|connection" | tail -30
```

---

**Run these to see the full error!**
