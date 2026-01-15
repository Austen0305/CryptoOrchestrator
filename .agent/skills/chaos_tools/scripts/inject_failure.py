import argparse
import time
import random


def inject_db_latency(ms):
    """Simulates injection of DB latency."""
    print(f"Chaos: Injecting {ms}ms latency into PostgreSQL...")
    time.sleep(ms / 1000.0)  # Simulation
    print("Chaos: Latency injection complete.")


def simulate_service_failure(service):
    """Simulates service termination."""
    print(f"Chaos: Sending SIGTERM to service '{service}'...")
    # Simulation: In a real environment, this would call k8s API or kill process
    result = random.choice(["SUCCESS", "FAILED"])
    print(f"Chaos: Service termination {result}.")


def main():
    parser = argparse.ArgumentParser(description="Chaos Injection Utility")
    parser.add_argument(
        "--target", required=True, help="Target for chaos (database/redis/web/worker)"
    )
    parser.add_argument(
        "--type", choices=["latency", "failure", "jitter"], required=True
    )
    parser.add_argument(
        "--value", type=float, default=100.0, help="Value for latency/jitter"
    )

    args = parser.parse_args()

    print(f"--- CHAOS SESSION STARTED: {args.target} ---")

    if args.target == "database" and args.type == "latency":
        inject_db_latency(args.value)
    elif args.type == "failure":
        simulate_service_failure(args.target)
    else:
        print(
            f"Chaos: Injecting {args.type} on {args.target} with value {args.value}..."
        )

    print(f"--- CHAOS SESSION COMPLETED ---")


if __name__ == "__main__":
    main()
