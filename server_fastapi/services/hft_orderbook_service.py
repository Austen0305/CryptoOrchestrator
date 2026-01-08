"""
High-Frequency Trading Order Book Service
Provides order book snapshots with delta updates for low-latency trading
"""

import asyncio
import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


class OrderBookSnapshot:
    """Order book snapshot with timestamp"""

    def __init__(
        self,
        pair: str,
        bids: list[tuple[float, float]],
        asks: list[tuple[float, float]],
    ):
        self.pair = pair
        self.bids = bids  # List of (price, quantity) tuples, sorted descending by price
        self.asks = asks  # List of (price, quantity) tuples, sorted ascending by price
        self.timestamp = time.time_ns()  # Nanosecond precision
        self.sequence = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "pair": self.pair,
            "bids": [[float(price), float(qty)] for price, qty in self.bids],
            "asks": [[float(price), float(qty)] for price, qty in self.asks],
            "timestamp": self.timestamp,
            "sequence": self.sequence,
        }

    def get_best_bid(self) -> float | None:
        """Get best bid price"""
        return self.bids[0][0] if self.bids else None

    def get_best_ask(self) -> float | None:
        """Get best ask price"""
        return self.asks[0][0] if self.asks else None

    def get_spread(self) -> float | None:
        """Calculate bid-ask spread"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return best_ask - best_bid
        return None


class OrderBookDelta:
    """Order book delta update"""

    def __init__(self, pair: str, sequence: int):
        self.pair = pair
        self.sequence = sequence
        self.timestamp = time.time_ns()
        self.bid_updates: list[
            tuple[float, float]
        ] = []  # (price, quantity) - 0 quantity means removal
        self.ask_updates: list[
            tuple[float, float]
        ] = []  # (price, quantity) - 0 quantity means removal

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "pair": self.pair,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "bid_updates": [
                [float(price), float(qty)] for price, qty in self.bid_updates
            ],
            "ask_updates": [
                [float(price), float(qty)] for price, qty in self.ask_updates
            ],
        }


class HFTOrderBookService:
    """
    High-performance order book service with delta updates

    Features:
    - Order book snapshots
    - Delta updates (only changes)
    - Low-latency in-memory storage
    - Sequence numbers for ordering
    - Binary protocol support
    """

    def __init__(self):
        # In-memory order book storage
        self.snapshots: dict[str, OrderBookSnapshot] = {}
        self.delta_history: dict[str, deque] = {}  # Keep last N deltas per pair
        self.sequences: dict[str, int] = {}  # Sequence counter per pair
        self.subscribers: dict[str, set[asyncio.Queue]] = {}  # Subscribers per pair
        self.update_tasks: dict[str, asyncio.Task] = {}
        self.max_delta_history = 1000  # Keep last 1000 deltas

        # Performance metrics
        self.update_latencies: dict[str, deque] = {}  # Track update latencies
        self.max_latency_history = 100

    async def update_orderbook(
        self,
        pair: str,
        bids: list[tuple[float, float]],
        asks: list[tuple[float, float]],
    ) -> OrderBookDelta:
        """
        Update order book and generate delta

        Args:
            pair: Trading pair (e.g., "BTC/USD")
            bids: New bid levels [(price, quantity), ...]
            asks: New ask levels [(price, quantity), ...]

        Returns:
            OrderBookDelta with changes
        """
        start_time = time.time_ns()

        # Get current snapshot
        old_snapshot = self.snapshots.get(pair)

        # Increment sequence
        if pair not in self.sequences:
            self.sequences[pair] = 0
        self.sequences[pair] += 1
        sequence = self.sequences[pair]

        # Create new snapshot
        new_snapshot = OrderBookSnapshot(pair, bids, asks)
        new_snapshot.sequence = sequence

        # Calculate delta
        delta = OrderBookDelta(pair, sequence)

        if old_snapshot:
            # Calculate bid deltas
            old_bids_dict = {price: qty for price, qty in old_snapshot.bids}
            new_bids_dict = {price: qty for price, qty in bids}

            # Find changes
            all_bid_prices = set(old_bids_dict.keys()) | set(new_bids_dict.keys())
            for price in sorted(all_bid_prices, reverse=True):
                old_qty = old_bids_dict.get(price, 0.0)
                new_qty = new_bids_dict.get(price, 0.0)
                if old_qty != new_qty:
                    delta.bid_updates.append((price, new_qty))

            # Calculate ask deltas
            old_asks_dict = {price: qty for price, qty in old_snapshot.asks}
            new_asks_dict = {price: qty for price, qty in asks}

            # Find changes
            all_ask_prices = set(old_asks_dict.keys()) | set(new_asks_dict.keys())
            for price in sorted(all_ask_prices):
                old_qty = old_asks_dict.get(price, 0.0)
                new_qty = new_asks_dict.get(price, 0.0)
                if old_qty != new_qty:
                    delta.ask_updates.append((price, new_qty))
        else:
            # First snapshot - all levels are new
            delta.bid_updates = bids
            delta.ask_updates = asks

        # Update snapshot
        self.snapshots[pair] = new_snapshot

        # Store delta in history
        if pair not in self.delta_history:
            self.delta_history[pair] = deque(maxlen=self.max_delta_history)
        self.delta_history[pair].append(delta)

        # Track latency
        latency_ns = time.time_ns() - start_time
        if pair not in self.update_latencies:
            self.update_latencies[pair] = deque(maxlen=self.max_latency_history)
        self.update_latencies[pair].append(latency_ns)

        # Notify subscribers
        await self._notify_subscribers(pair, delta)

        return delta

    async def get_snapshot(self, pair: str) -> OrderBookSnapshot | None:
        """Get current order book snapshot"""
        return self.snapshots.get(pair)

    async def get_delta_history(
        self,
        pair: str,
        since_sequence: int | None = None,
        limit: int = 100,
    ) -> list[OrderBookDelta]:
        """
        Get delta history for a pair

        Args:
            pair: Trading pair
            since_sequence: Get deltas after this sequence number
            limit: Maximum number of deltas to return

        Returns:
            List of OrderBookDelta objects
        """
        if pair not in self.delta_history:
            return []

        deltas = list(self.delta_history[pair])

        if since_sequence is not None:
            deltas = [d for d in deltas if d.sequence > since_sequence]

        return deltas[-limit:] if len(deltas) > limit else deltas

    async def subscribe_deltas(self, pair: str) -> asyncio.Queue:
        """
        Subscribe to order book delta updates

        Args:
            pair: Trading pair to subscribe to

        Returns:
            Queue that will receive OrderBookDelta objects
        """
        if pair not in self.subscribers:
            self.subscribers[pair] = set()

        queue = asyncio.Queue(maxsize=1000)  # Buffer up to 1000 deltas
        self.subscribers[pair].add(queue)

        logger.info(f"Subscribed to order book deltas for {pair}")

        return queue

    async def unsubscribe_deltas(self, pair: str, queue: asyncio.Queue):
        """Unsubscribe from order book delta updates"""
        if pair in self.subscribers:
            self.subscribers[pair].discard(queue)
            logger.info(f"Unsubscribed from order book deltas for {pair}")

    async def _notify_subscribers(self, pair: str, delta: OrderBookDelta):
        """Notify all subscribers of a delta update"""
        if pair not in self.subscribers:
            return

        # Send delta to all subscribers (non-blocking)
        for queue in list(self.subscribers[pair]):
            try:
                queue.put_nowait(delta)
            except asyncio.QueueFull:
                logger.warning(f"Subscriber queue full for {pair}, dropping delta")
                # Remove subscriber if queue is full (likely disconnected)
                self.subscribers[pair].discard(queue)

    def get_latency_stats(self, pair: str) -> dict | None:
        """Get latency statistics for a pair"""
        if pair not in self.update_latencies or not self.update_latencies[pair]:
            return None

        latencies = list(self.update_latencies[pair])
        latencies_ms = [lat / 1_000_000 for lat in latencies]  # Convert to milliseconds

        return {
            "pair": pair,
            "count": len(latencies_ms),
            "min_ms": min(latencies_ms),
            "max_ms": max(latencies_ms),
            "avg_ms": sum(latencies_ms) / len(latencies_ms),
            "p50_ms": sorted(latencies_ms)[len(latencies_ms) // 2],
            "p95_ms": sorted(latencies_ms)[int(len(latencies_ms) * 0.95)],
            "p99_ms": sorted(latencies_ms)[int(len(latencies_ms) * 0.99)],
        }

    async def start_streaming(self, pair: str, update_interval: float = 0.1):
        """
        Start streaming order book updates for a pair

        This is a placeholder - in production, this would connect to
        exchange WebSocket feeds or DEX aggregator APIs
        """
        if pair in self.update_tasks and not self.update_tasks[pair].done():
            return  # Already streaming

        async def _stream():
            try:
                # In production, this would connect to real exchange/DEX feeds
                # For now, this is a placeholder that can be extended
                logger.info(f"Started order book streaming for {pair}")
                while True:
                    await asyncio.sleep(update_interval)
                    # Real implementation would fetch from exchange/DEX here
            except asyncio.CancelledError:
                logger.info(f"Stopped order book streaming for {pair}")

        self.update_tasks[pair] = asyncio.create_task(_stream())

    async def stop_streaming(self, pair: str):
        """Stop streaming order book updates for a pair"""
        if pair in self.update_tasks:
            self.update_tasks[pair].cancel()
            try:
                await self.update_tasks[pair]
            except asyncio.CancelledError:
                pass
            del self.update_tasks[pair]


# Global instance
hft_orderbook_service = HFTOrderBookService()
