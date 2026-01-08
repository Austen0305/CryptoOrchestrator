"""
Volume Profile Service
Calculates volume profile and market profile for charting terminal.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

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
        if not market_data or len(market_data) == 0:
            return {"levels": [], "total_volume": 0}

        df = pd.DataFrame(market_data)

        # Calculate price range
        min_price = df["low"].min()
        max_price = df["high"].max()
        price_range = max_price - min_price

        if price_range == 0:
            return {"levels": [], "total_volume": 0}

        # Create price bins
        bin_size = price_range / bins
        price_bins = np.arange(min_price, max_price + bin_size, bin_size)

        # Calculate volume at each price level
        volume_profile = []
        total_volume = 0

        for i in range(len(price_bins) - 1):
            bin_low = price_bins[i]
            bin_high = price_bins[i + 1]
            bin_center = (bin_low + bin_high) / 2

            # Find candles that overlap with this price bin
            overlapping = df[(df["low"] <= bin_high) & (df["high"] >= bin_low)]

            if len(overlapping) > 0:
                # Calculate volume contribution for this bin
                # Simple approach: distribute volume proportionally
                bin_volume = 0
                for _, candle in overlapping.iterrows():
                    # Price range of candle that overlaps with bin
                    overlap_low = max(bin_low, candle["low"])
                    overlap_high = min(bin_high, candle["high"])
                    overlap_range = overlap_high - overlap_low
                    candle_range = candle["high"] - candle["low"]

                    if candle_range > 0:
                        # Proportion of candle volume in this bin
                        proportion = overlap_range / candle_range
                        bin_volume += candle.get("volume", 0) * proportion

                volume_profile.append(
                    {
                        "price": bin_center,
                        "volume": bin_volume,
                        "low": bin_low,
                        "high": bin_high,
                    }
                )
                total_volume += bin_volume

        # Sort by price
        volume_profile.sort(key=lambda x: x["price"])

        # Find POC (Point of Control) - price level with highest volume
        poc = max(volume_profile, key=lambda x: x["volume"]) if volume_profile else None

        return {
            "levels": volume_profile,
            "total_volume": total_volume,
            "poc": poc["price"] if poc else None,
            "poc_volume": poc["volume"] if poc else 0,
            "price_range": {"min": min_price, "max": max_price},
        }

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
        if not market_data or len(market_data) == 0:
            return {"tpos": [], "value_area": None}

        df = pd.DataFrame(market_data)

        # Calculate price range
        min_price = df["low"].min()
        max_price = df["high"].max()
        price_range = max_price - min_price

        if price_range == 0:
            return {"tpos": [], "value_area": None}

        # Calculate TPO size
        tpo_price_size = price_range * tpo_size

        # Create TPO levels
        tpo_levels = np.arange(min_price, max_price + tpo_price_size, tpo_price_size)

        # Count TPOs at each level
        tpo_counts = {}
        for _, candle in df.iterrows():
            # Find which TPO levels this candle touches
            for level in tpo_levels:
                if candle["low"] <= level <= candle["high"]:
                    tpo_counts[level] = tpo_counts.get(level, 0) + 1

        # Convert to list format
        tpos = [
            {"price": level, "count": tpo_counts.get(level, 0)}
            for level in sorted(tpo_levels)
        ]

        # Calculate Value Area (70% of TPOs)
        total_tpos = sum(tpo_counts.values())
        value_area_target = total_tpos * 0.70

        # Find value area (price range containing 70% of TPOs)
        sorted_tpos = sorted(tpos, key=lambda x: x["count"], reverse=True)
        cumulative_count = 0
        value_area_levels = []

        for tpo in sorted_tpos:
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
