"""
Volume Profile Service
Calculates volume profile and market profile for charting terminal.
Refactored to use Polars for high performance.
"""

import logging
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)


class VolumeProfileService:
    """Service for calculating volume profiles and market profiles"""

    def calculate_volume_profile(
        self,
        market_data: list[dict[str, Any]],
        bins: int = 24,
    ) -> dict[str, Any]:
        """
        Calculate volume profile (Volume at Price / VAP).

        Args:
            market_data: List of OHLCV data
            bins: Number of price bins (default: 24)

        Returns:
            Dict with price levels and volumes
        """
        if not market_data:
            return {"levels": [], "total_volume": 0}

        try:
            df = pl.DataFrame(market_data)

            # Ensure columns exist and cast types
            required_cols = ["low", "high", "volume"]
            if not all(col in df.columns for col in required_cols):
                return {"levels": [], "total_volume": 0}

            df = df.with_columns(
                [
                    pl.col("low").cast(pl.Float64),
                    pl.col("high").cast(pl.Float64),
                    pl.col("volume").cast(pl.Float64),
                ]
            )

            # Calculate price range
            min_price = df["low"].min()
            max_price = df["high"].max()

            if min_price is None or max_price is None:
                return {"levels": [], "total_volume": 0}

            price_range = max_price - min_price

            if price_range == 0:
                return {"levels": [], "total_volume": 0}

            # Create price bins
            bin_size = price_range / bins

            # Generate bins manually (Polars doesn't have numpy.arange equivalent directly)
            # We use python loop here as number of bins is small (e.g. 24)
            current_level = min_price
            price_bins = []
            while current_level < max_price + bin_size:  # Ensure coverage
                price_bins.append(current_level)
                current_level += bin_size

            # Calculate volume at each price level
            volume_profile = []
            total_volume = 0.0

            # Optimizing: Calculate candle ranges once
            df = df.with_columns((pl.col("high") - pl.col("low")).alias("candle_range"))

            for i in range(len(price_bins) - 1):
                bin_low = price_bins[i]
                bin_high = price_bins[i + 1]
                bin_center = (bin_low + bin_high) / 2

                # Filter candles strictly overlapping this bin
                # Condition: low <= bin_high AND high >= bin_low
                overlapping = df.filter(
                    (pl.col("low") <= bin_high) & (pl.col("high") >= bin_low)
                )

                if overlapping.height > 0:
                    # Logic:
                    # overlap_low = Max(bin_low, candle_low)
                    # overlap_high = Min(bin_high, candle_high)
                    # overlap_range = overlap_high - overlap_low
                    # proportion = overlap_range / candle_range
                    # contribution = volume * proportion

                    # We can do this vectorized in Polars

                    # 1. Calculate overlap bounds
                    # We use pl.max/min horizontal if available, but for scalers vs cols we use simpler expressions
                    # Since bin_low is scalar, use pl.lit(bin_low) implicitly or explicitly

                    # overlap_low = max(bin_low, low) -> (low > bin_low) ? low : bin_low
                    # overlap_high = min(bin_high, high) -> (high < bin_high) ? high : bin_high

                    # Using 'when/then' for element-wise max/min with scalar
                    expr_overlap_low = (
                        pl.when(pl.col("low") > bin_low)
                        .then(pl.col("low"))
                        .otherwise(bin_low)
                    )
                    expr_overlap_high = (
                        pl.when(pl.col("high") < bin_high)
                        .then(pl.col("high"))
                        .otherwise(bin_high)
                    )

                    overlap_df = overlapping.with_columns(
                        [(expr_overlap_high - expr_overlap_low).alias("overlap_rng")]
                    )

                    # Avoid division by zero if candle range is 0 (though filter implies some overlap, but robust check)
                    # volume * (overlap_rng / candle_range)
                    # If candle_range is 0, proportion is 0 (or 1 if point match? Assuming 0 for safety)

                    bin_contribution = overlap_df.select(
                        pl.when(pl.col("candle_range") > 0)
                        .then(
                            pl.col("volume")
                            * (pl.col("overlap_rng") / pl.col("candle_range"))
                        )
                        .otherwise(0.0)
                        .sum()
                    ).item()  # scalar sum

                    volume_profile.append(
                        {
                            "price": bin_center,
                            "volume": bin_contribution,
                            "low": bin_low,
                            "high": bin_high,
                        }
                    )
                    total_volume += bin_contribution

            # Sort by price
            volume_profile.sort(key=lambda x: x["price"])

            # Find POC (Point of Control)
            poc = (
                max(volume_profile, key=lambda x: x["volume"])
                if volume_profile
                else None
            )

            return {
                "levels": volume_profile,
                "total_volume": total_volume,
                "poc": poc["price"] if poc else None,
                "poc_volume": poc["volume"] if poc else 0,
                "price_range": {"min": min_price, "max": max_price},
            }

        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return {"levels": [], "total_volume": 0}

    def calculate_market_profile(
        self,
        market_data: list[dict[str, Any]],
        tpo_size: float = 0.25,  # Time Price Opportunity size (percentage)
    ) -> dict[str, Any]:
        """
        Calculate Market Profile (TPO - Time Price Opportunity).

        Args:
            market_data: List of OHLCV data
            tpo_size: Size of TPO as percentage of price range

        Returns:
            Dict with TPO levels and counts
        """
        if not market_data:
            return {"tpos": [], "value_area": None}

        try:
            df = pl.DataFrame(market_data)

            required_cols = ["low", "high"]
            if not all(col in df.columns for col in required_cols):
                return {"tpos": [], "value_area": None}

            df = df.with_columns(
                [pl.col("low").cast(pl.Float64), pl.col("high").cast(pl.Float64)]
            )

            # Calculate price range
            min_price = df["low"].min()
            max_price = df["high"].max()

            if min_price is None or max_price is None:
                return {"tpos": [], "value_area": None}

            price_range = max_price - min_price

            if price_range == 0:
                return {"tpos": [], "value_area": None}

            # Calculate TPO size
            tpo_price_size = price_range * tpo_size

            # Bound check
            if tpo_price_size <= 0:
                tpo_price_size = 0.00000001  # prevent infinite loop

            # Create TPO levels
            # Manual loop for levels
            tpo_levels = []
            curr = min_price
            while curr <= max_price + tpo_price_size:
                tpo_levels.append(curr)
                curr += tpo_price_size

            # Count TPOs at each level
            # Vectorized approach: For each level, count rows where low <= level <= high
            tpo_counts = {}
            for level in tpo_levels:
                # Count rows where candle covers this level
                count = df.filter(
                    (pl.col("low") <= level) & (pl.col("high") >= level)
                ).height
                if count > 0:
                    tpo_counts[level] = count

            if not tpo_counts:
                return {"tpos": [], "value_area": None}

            # Convert to list format
            tpos = [
                {"price": level, "count": count}
                for level, count in sorted(tpo_counts.items())
            ]

            # Calculate Value Area (70% of TPOs)
            total_tpos = sum(tpo_counts.values())
            value_area_target = total_tpos * 0.70

            # Find value area (price range containing 70% of TPOs)
            sorted_by_count = sorted(tpos, key=lambda x: x["count"], reverse=True)
            cumulative_count = 0
            value_area_levels = []

            for tpo in sorted_by_count:
                cumulative_count += tpo["count"]
                value_area_levels.append(tpo["price"])
                if cumulative_count >= value_area_target:
                    break

            value_area = {
                "low": min(value_area_levels) if value_area_levels else None,
                "high": max(value_area_levels) if value_area_levels else None,
            }

            return {
                "tpos": tpos,
                "value_area": value_area,
                "total_tpos": total_tpos,
            }

        except Exception as e:
            logger.error(f"Error calculating market profile: {e}")
            return {"tpos": [], "value_area": None}

    def calculate_poc_and_value_areas(
        self,
        market_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Calculate POC (Point of Control) and Value Areas (VAH, VAL).

        Args:
            market_data: List of OHLCV data

        Returns:
            Dict with POC, VAH, VAL
        """
        # This reuses the already refactored method, so it is safe.
        volume_profile = self.calculate_volume_profile(market_data)

        if not volume_profile["levels"]:
            return {"poc": None, "vah": None, "val": None}

        # POC is already calculated
        poc = volume_profile["poc"]

        # Calculate Value Area High (VAH) and Value Area Low (VAL)
        # Value Area contains 70% of volume
        levels = volume_profile["levels"]
        total_volume = volume_profile["total_volume"]
        target_volume = total_volume * 0.70

        # Sort by volume descending
        sorted_levels = sorted(levels, key=lambda x: x["volume"], reverse=True)

        cumulative_volume = 0
        value_area_prices = []

        for level in sorted_levels:
            cumulative_volume += level["volume"]
            value_area_prices.append(level["price"])
            if cumulative_volume >= target_volume:
                break

        vah = max(value_area_prices) if value_area_prices else None
        val = min(value_area_prices) if value_area_prices else None

        return {
            "poc": poc,
            "vah": vah,
            "val": val,
            "volume_profile": volume_profile,
        }
