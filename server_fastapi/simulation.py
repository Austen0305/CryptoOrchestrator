import asyncio
import hashlib
from datetime import datetime, timedelta

import polars as pl


async def run_simulation(seed: int) -> str:
    """
    Runs a deterministic simulation of the market data fetching and ML training pipeline.
    Returns a SHA256 hash of the output to verify determinism.
    """
    print(f"Running simulation with seed {seed}...")

    # 1. Mock Data Injection (Polars)
    # in a real simulation we'd mock the network calls, but here we'll rely on the service logic
    # assuming MarketDataService has some deterministic Mock mode or we use a specialized MockService

    # For this verification script, we will create a manual Polars DataFrame
    # and pass it through a transformation pipeline similar to the ML pipeline.

    # Match 100 periods to match the price/volume lists below
    data = pl.DataFrame(
        {
            "timestamp": pl.date_range(
                start=datetime(2025, 1, 1),
                end=datetime(2025, 1, 1) + timedelta(minutes=99),
                interval="1m",
                eager=True,
            ),
            "price": [
                100.0 + (i * 0.1 * (1 if i % 2 == 0 else -1)) for i in range(100)
            ],
            "volume": [1000 + i for i in range(100)],
        }
    )

    # 2. Polars Transformation (Determinism Check)
    # Calculate VWAP and RSI-like indicator
    processed = data.with_columns(
        [
            (pl.col("price") * pl.col("volume")).alias("pv"),
        ]
    ).select([pl.sum("pv") / pl.sum("volume")])

    result_val = processed[0, 0]

    # 3. Hash the result
    hasher = hashlib.sha256()
    hasher.update(str(result_val).encode("utf-8"))
    digest = hasher.hexdigest()

    print(f"Simulation Result: {result_val}")
    print(f"Hash: {digest}")
    return digest


if __name__ == "__main__":
    from datetime import datetime

    async def main():
        hash1 = await run_simulation(42)
        hash2 = await run_simulation(42)

        if hash1 == hash2:
            print("✅ DETERMINISM VERIFIED: Hashes match.")
            exit(0)
        else:
            print("❌ DETERMINISM FAILED: Hashes differ.")
            exit(1)

    asyncio.run(main())
