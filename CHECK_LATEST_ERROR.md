# Check Latest Startup Error

Run these commands to see the actual error:

```bash
# Get the most recent error
sudo docker logs crypto-orchestrator-backend 2>&1 | tail -50

# Check for the specific error
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -A 10 "Application startup failed" | tail -20

# Check if it's still the encryption key error
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i "encryption\|secret\|too short"

# Check if it's still the syntax error
sudo docker logs crypto-orchestrator-backend 2>&1 | grep -i "syntax\|await"
```

---

**Run these and share the output!**
