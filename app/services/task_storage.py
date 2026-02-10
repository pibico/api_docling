#!/usr/bin/env python3
"""
Redis-based task storage for shared state across multiple workers.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import redis
from logzero import logger


class TaskStorage:
    """Redis-based task storage for multi-worker environments"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl: int = 3600):
        """
        Initialize Redis connection

        Args:
            redis_url: Redis connection URL
            ttl: Time-to-live for tasks in seconds (default: 1 hour)
        """
        self.redis_url = redis_url
        self.ttl = ttl
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _task_key(self, task_id: str) -> str:
        """Generate Redis key for a task"""
        return f"docling:task:{task_id}"

    def create_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """
        Create a new task

        Args:
            task_id: Unique task identifier
            task_data: Task data dictionary
        """
        try:
            key = self._task_key(task_id)
            task_data["task_id"] = task_id
            task_data["created_at"] = datetime.now().isoformat()

            # Store task data as JSON
            self.client.setex(
                key,
                self.ttl,
                json.dumps(task_data)
            )
            logger.info(f"Created task {task_id}")
        except Exception as e:
            logger.error(f"Error creating task {task_id}: {e}")
            raise

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task data

        Args:
            task_id: Task identifier

        Returns:
            Task data dictionary or None if not found
        """
        try:
            key = self._task_key(task_id)
            data = self.client.get(key)

            if data is None:
                return None

            return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update task data

        Args:
            task_id: Task identifier
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if task not found
        """
        try:
            task_data = self.get_task(task_id)

            if task_data is None:
                return False

            # Update fields
            task_data.update(updates)
            task_data["updated_at"] = datetime.now().isoformat()

            # Save back to Redis
            key = self._task_key(task_id)
            self.client.setex(
                key,
                self.ttl,
                json.dumps(task_data)
            )

            logger.debug(f"Updated task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            key = self._task_key(task_id)
            result = self.client.delete(key)

            if result > 0:
                logger.info(f"Deleted task {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False

    def task_exists(self, task_id: str) -> bool:
        """Check if a task exists"""
        try:
            key = self._task_key(task_id)
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking task existence {task_id}: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


# Create singleton instance
task_storage = TaskStorage()
