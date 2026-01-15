import argparse
import sys


def check_risk_limits(amount, asset, wallet_balance):
    """Simulates RiskManager check logic."""
    # Logic: Trade size must be < 10% of balance
    limit = wallet_balance * 0.1
    if amount > limit:
        return False, f"Trade amount {amount} exceeds 10% limit of {limit}"
    return True, "Within risk limits"


def simulate_volatility(factor):
    """Simulates market volatility check."""
    # Logic: Halt trading if volatility > 0.2
    if factor > 0.2:
        return "TRIGGERED", "Volatility circuit breaker active"
    return "OK", "Volatility targets within range"


def main():
    parser = argparse.ArgumentParser(description="Risk Management Simulation")
    parser.add_argument("--amount", type=float, help="Proposed trade amount")
    parser.add_argument("--asset", type=str, help="Asset for trade")
    parser.add_argument(
        "--scenario", choices=["volatility", "liquidity"], help="Scene to simulate"
    )
    parser.add_argument("--volatility", type=float, help="Volatility factor")

    args = parser.parse_args()

    # Static wallet balance for simulation
    MOCK_BALANCE = 10.0

    if args.amount:
        passed, msg = check_risk_limits(args.amount, args.asset, MOCK_BALANCE)
        if passed:
            print(f"SUCCESS: {msg}")
        else:
            print(f"FAILED: {msg}")
            sys.exit(1)

    if args.scenario == "volatility":
        status, msg = simulate_volatility(args.volatility or 0.1)
        print(f"Scenario Result: {status} - {msg}")
        if status == "TRIGGERED":
            sys.exit(2)


if __name__ == "__main__":
    main()
