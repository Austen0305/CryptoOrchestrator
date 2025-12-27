"""
Crash recovery system
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
import json
import sqlite3
import os
import time
import uuid
import logging

logger = logging.getLogger(__name__)


class RecoveryCheckpoint(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    id: str
    timestamp: int
    state_data: Dict[str, any]
    description: str


class CrashRecoverySystem:
    """System for handling crashes and recovery"""

    def __init__(self, db_path: str = "data/crash_recovery.db"):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Initialize SQLite database and create tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    state_data TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """
            )
            logger.info(f"Crash recovery database initialized at {self.db_path}")

    async def create_checkpoint(
        self, state_data: Dict[str, any], description: str
    ) -> RecoveryCheckpoint:
        """Create a recovery checkpoint"""
        checkpoint_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)  # milliseconds

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO checkpoints (id, timestamp, state_data, description)
                    VALUES (?, ?, ?, ?)
                """,
                    (checkpoint_id, timestamp, json.dumps(state_data), description),
                )

            checkpoint = RecoveryCheckpoint(
                id=checkpoint_id,
                timestamp=timestamp,
                state_data=state_data,
                description=description,
            )
            logger.info(f"Created checkpoint {checkpoint_id}: {description}")
            return checkpoint
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise

    async def recover_from_checkpoint(
        self, checkpoint_id: str
    ) -> Optional[Dict[str, any]]:
        """Recover system state from checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT state_data FROM checkpoints WHERE id = ?
                """,
                    (checkpoint_id,),
                )
                row = cursor.fetchone()

                if row:
                    state_data = json.loads(row[0])
                    logger.info(f"Recovered state from checkpoint {checkpoint_id}")
                    return state_data
                else:
                    logger.warning(f"Checkpoint {checkpoint_id} not found")
                    return None
        except Exception as e:
            logger.error(f"Failed to recover from checkpoint {checkpoint_id}: {e}")
            return None

    async def get_latest_checkpoint(self) -> Optional[RecoveryCheckpoint]:
        """Get the most recent checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, timestamp, state_data, description
                    FROM checkpoints
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                )
                row = cursor.fetchone()

                if row:
                    return RecoveryCheckpoint(
                        id=row[0],
                        timestamp=row[1],
                        state_data=json.loads(row[2]),
                        description=row[3],
                    )
                return None
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint: {e}")
            return None

    async def list_checkpoints(self) -> List[RecoveryCheckpoint]:
        """List all available checkpoints"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, timestamp, state_data, description
                    FROM checkpoints
                    ORDER BY timestamp DESC
                """
                )
                rows = cursor.fetchall()

                checkpoints = []
                for row in rows:
                    checkpoints.append(
                        RecoveryCheckpoint(
                            id=row[0],
                            timestamp=row[1],
                            state_data=json.loads(row[2]),
                            description=row[3],
                        )
                    )
                return checkpoints
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def automatic_recovery(self) -> bool:
        """Attempt automatic recovery on startup"""
        try:
            latest_checkpoint = await self.get_latest_checkpoint()
            if latest_checkpoint:
                logger.info(
                    f"Automatic recovery initiated from checkpoint {latest_checkpoint.id}"
                )
                # Recovery logic would be implemented here based on the state data
                # For now, we just log the successful recovery attempt
                return True
            else:
                logger.info("No checkpoints available for automatic recovery")
                return False
        except Exception as e:
            logger.error(f"Automatic recovery failed: {e}")
            return False
