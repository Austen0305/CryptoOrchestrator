---
name: market_surveillance
description: AI/ML logic for detecting Spoofing, Wash Trading, and Layering in high-frequency trading data.
---

# Market Surveillance Skill

This skill provides advanced surveillance capabilities to detect and mitigate market abuse in CryptoOrchestrator.

## Capabilities

- **Spoofing Detection**: Identifying large orders placed and then canceled before execution to manipulate prices.
- **Wash Trading Detection**: Detecting simultaneous buy/sell orders from the same entity to create fake volume.
- **Layering Detection**: Identifying patterns of multiple pending orders at different price levels to create a false sense of depth.

## Usage

Use the `detect_abuse.py` script to analyze order book snapshots or trade history.

### Examples

**Analyze Order Book Snapshot:**
```bash
python .agent/skills/market_surveillance/scripts/detect_abuse.py --type spoofing --data orderbook.json
```

**Detect Wash Trading in History:**
```bash
python .agent/skills/market_surveillance/scripts/detect_abuse.py --type wash_trading --data trades.csv
```

## AI Safety & Fallbacks

- Surveillance signals must be combined with deterministic rules in `RiskManager`.
- High-confidence abuse signals (>90%) MUST trigger the `circuit_breaker.py`.
