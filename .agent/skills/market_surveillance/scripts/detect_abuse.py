import argparse
import json
import random
import sys


def detect_spoofing(data):
    """Simulates spoofing detection logic."""
    # Logic: Large orders followed by immediate cancellation
    # Simplified for demo: Look for 'canceled' orders > 100 BTC equivalent
    print("Analyzing order patterns for spoofing...")
    score = random.uniform(0.1, 0.95)
    return score


def detect_wash_trading(data):
    """Simulates wash trading detection logic."""
    # Logic: Circular trades or near-instant offsetting positions
    print("Analyzing trade history for wash trading...")
    score = random.uniform(0.05, 0.4)
    return score


def main():
    parser = argparse.ArgumentParser(description="Market Surveillance Utility")
    parser.add_argument(
        "--type", choices=["spoofing", "wash_trading", "layering"], required=True
    )
    parser.add_argument("--data", required=True, help="Path to JSON/CSV data file")

    args = parser.parse_args()

    # Load data (simulated)
    print(f"Loading data from {args.data}...")

    if args.type == "spoofing":
        confidence = detect_spoofing(None)
    elif args.type == "wash_trading":
        confidence = detect_wash_trading(None)
    else:
        confidence = 0.5

    print(f"Abuse Signal Confidence: {confidence:.2%}")

    if confidence > 0.85:
        print("CRITICAL: Market abuse detected. Recommend triggering Circuit Breaker.")
        sys.exit(2)  # Code 2: Action Required
    elif confidence > 0.5:
        print(
            "WARNING: Elevated abuse indicators detected. Flagging for manual review."
        )
        sys.exit(0)
    else:
        print("STATUS: Markets appear normal.")
        sys.exit(0)


if __name__ == "__main__":
    main()
