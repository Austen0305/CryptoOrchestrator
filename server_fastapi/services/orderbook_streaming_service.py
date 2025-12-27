"""
Order Book Streaming Service
Provides real-time order book updates via WebSocket.
"""

import asyncio
import logging
from typing import Dict, Set, Optional, Callable
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class OrderBookStreamingService:
    """Service for streaming order book updates"""

    def __init__(self):
        self.active_streams: Dict[str, Set[Callable]] = {}
        self.last_updates: Dict[str, Dict] = {}
        self.update_intervals: Dict[str, float] = {}
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}

    async def subscribe(
        self, pair: str, callback: Callable, update_interval: float = 1.0
    ) -> str:
        """
        Subscribe to order book updates for a trading pair.

        Args:
            pair: Trading pair (e.g., "BTC/USD")
            callback: Async function to call with order book updates
            update_interval: Update interval in seconds (default: 1.0)

        Returns:
            Subscription ID
        """
        if pair not in self.active_streams:
            self.active_streams[pair] = set()
            self.update_intervals[pair] = update_interval

        subscription_id = f"{pair}_{datetime.now().timestamp()}"
        self.active_streams[pair].add(callback)

        # Start streaming if not already running
        if pair not in self._tasks or self._tasks[pair].done():
            self._tasks[pair] = asyncio.create_task(self._stream_orderbook(pair))

        logger.info(f"Subscribed to order book stream for {pair}")
        return subscription_id

    async def unsubscribe(self, pair: str, callback: Callable):
        """Unsubscribe from order book updates"""
        if pair in self.active_streams:
            self.active_streams[pair].discard(callback)

            # Stop streaming if no more subscribers
            if not self.active_streams[pair]:
                if pair in self._tasks:
                    self._tasks[pair].cancel()
                    del self._tasks[pair]
                del self.active_streams[pair]
                if pair in self.last_updates:
                    del self.last_updates[pair]
                logger.info(f"Unsubscribed from order book stream for {pair}")

    async def _stream_orderbook(self, pair: str):
        """Internal method to stream order book updates with rate limiting and error recovery"""
        from ..services.exchange_service import default_exchange

        consecutive_errors = 0
        max_consecutive_errors = 5
        backoff_seconds = 1

        try:
            while pair in self.active_streams:
                try:
                    # Fetch latest order book with timeout
                    try:
                        order_book = await asyncio.wait_for(
                            default_exchange.get_order_book(pair),
                            timeout=10.0,  # 10 second timeout
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"Order book fetch timeout for {pair}")
                        order_book = None

                    if order_book:
                        # Reset error counter on success
                        consecutive_errors = 0
                        backoff_seconds = 1

                        # Store last update
                        self.last_updates[pair] = {
                            "data": order_book,
                            "timestamp": datetime.now().isoformat(),
                        }

                        # Notify all subscribers with error handling
                        if pair in self.active_streams:
                            failed_callbacks = []
                            for callback in list(self.active_streams[pair]):
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await asyncio.wait_for(
                                            callback(order_book), timeout=5.0
                                        )
                                    else:
                                        callback(order_book)
                                except asyncio.TimeoutError:
                                    logger.warning(f"Callback timeout for {pair}")
                                    failed_callbacks.append(callback)
                                except Exception as e:
                                    logger.error(f"Error in order book callback: {e}")
                                    failed_callbacks.append(callback)

                            # Remove failed callbacks
                            for callback in failed_callbacks:
                                self.active_streams[pair].discard(callback)
                    else:
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            logger.error(
                                f"Too many consecutive errors for {pair}, stopping stream"
                            )
                            break

                    # Wait for next update interval with exponential backoff on errors
                    wait_time = self.update_intervals.get(pair, 1.0)
                    if consecutive_errors > 0:
                        wait_time = min(
                            wait_time * backoff_seconds, 30.0
                        )  # Max 30 seconds
                        backoff_seconds = min(
                            backoff_seconds * 2, 16
                        )  # Exponential backoff, max 16x

                    await asyncio.sleep(wait_time)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Error streaming order book for {pair}: {e}")
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many errors for {pair}, stopping stream")
                        break
                    await asyncio.sleep(min(backoff_seconds, 30))  # Exponential backoff
                    backoff_seconds = min(backoff_seconds * 2, 16)

        except asyncio.CancelledError:
            logger.info(f"Order book stream cancelled for {pair}")
        except Exception as e:
            logger.error(f"Fatal error in order book stream for {pair}: {e}")
        finally:
            # Cleanup on exit
            if pair in self.active_streams:
                del self.active_streams[pair]
            if pair in self._tasks:
                del self._tasks[pair]

    async def get_last_update(self, pair: str) -> Optional[Dict]:
        """Get the last order book update for a pair"""
        return self.last_updates.get(pair)

    async def stop_all(self):
        """Stop all active streams"""
        for pair in list(self._tasks.keys()):
            if pair in self._tasks:
                self._tasks[pair].cancel()
        self._tasks.clear()
        self.active_streams.clear()
        self.last_updates.clear()
        logger.info("All order book streams stopped")


# Global instance
orderbook_streaming_service = OrderBookStreamingService()
