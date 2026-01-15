---
name: chaos_tools
description: Procedures and scripts for automated chaos injection (Network/DB/Service).
---

# Chaos Tools Skill

This skill provides utilities for simulating infrastructure and application failures to verify the resilience of CryptoOrchestrator.

## Capabilities

- **Network Jitter Simulation**: Injecting latency and packet loss between services.
- **Database Latency Injection**: Simulating slow queries and locked tables.
- **Service Termination**: Randomly stopping microservices to verify self-healing (Kubernetes probes).

## Usage

Use the `inject_failure.py` script to simulate failure scenarios.

### Examples

**Inject 500ms Database Latency:**
```bash
python .agent/skills/chaos_tools/scripts/inject_failure.py --target database --type latency --value 500
```

**Simulate Network Jitter on Redis:**
```bash
python .agent/skills/chaos_tools/scripts/inject_failure.py --target redis --type jitter --value 0.15
```

## Resilience Audit Checklist

- [ ] Does the `RiskManager` correctly fallback to rule-based logic?
- [ ] Are idempotency keys preventing duplicate trades during retry?
- [ ] Do Kubernetes `livenessProbes` correctly restart the failed pods?
