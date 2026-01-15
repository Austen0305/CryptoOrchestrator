---
name: risk_management
description: Simulation patterns for the RiskManager and safety circuit breakers.
---

# Risk Management Skill

This skill provides utilities for simulating and validating trading scenarios against the project's risk management configurations.

## Capabilities

- **RiskManager Simulation**: Dry-run trades against the internal risk engine without executing them.
- **Circuit Breaker Testing**: Simulating conditions that should trigger an immediate trading halt.
- **Balance Guard Validation**: Ensuring trades do not exceed the configured percentage of total wallet balance.

## Usage

Use the `simulate_risk.py` script to trial trade requests.

### Examples

**Simulate a High-Value Trade:**
```bash
python .agent/skills/risk_management/scripts/simulate_risk.py --amount 1.5 --asset BTC --wallet 0x...
```

**Simulate Market Volatility Scenario:**
```bash
python .agent/skills/risk_management/scripts/simulate_risk.py --scenario volatility --volatility 0.25
```

## Security Requirements

- All simulations must be isolated from the production database.
- Results of simulations should be logged to the `RiskAudit` log for pattern analysis.
