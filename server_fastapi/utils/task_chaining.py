"""
Task Chaining and Grouping Utilities
Implements task workflows, chains, groups, and chords for complex task orchestration.
"""

import logging
from collections.abc import Callable
from typing import Any

from celery import chain, chord, group
from celery.result import AsyncResult, GroupResult

logger = logging.getLogger(__name__)


class TaskWorkflow:
    """
    Represents a workflow of chained tasks.
    """

    def __init__(self, workflow_id: str):
        """
        Initialize task workflow.

        Args:
            workflow_id: Unique workflow identifier
        """
        self.workflow_id = workflow_id
        self.tasks: list[dict[str, Any]] = []
        self.current_step = 0

    def add_task(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict[str, Any] = None,
        condition: Callable[[Any], bool] | None = None,
    ) -> "TaskWorkflow":
        """
        Add a task to the workflow.

        Args:
            task_name: Celery task name
            args: Task arguments
            kwargs: Task keyword arguments
            condition: Optional condition function to determine if task should run

        Returns:
            Self for method chaining
        """
        self.tasks.append(
            {
                "task_name": task_name,
                "args": args,
                "kwargs": kwargs or {},
                "condition": condition,
                "step": len(self.tasks),
            }
        )
        return self

    def execute(self) -> AsyncResult:
        """
        Execute workflow as a chain.

        Returns:
            AsyncResult for the workflow
        """
        if not self.tasks:
            raise ValueError("Workflow has no tasks")

        # Build chain
        task_signatures = []
        for task_info in self.tasks:
            from celery import signature

            sig = signature(
                task_info["task_name"],
                args=task_info["args"],
                kwargs=task_info["kwargs"],
            )
            task_signatures.append(sig)

        # Execute chain
        workflow_chain = chain(*task_signatures)
        return workflow_chain.apply_async()

    def execute_parallel(self) -> GroupResult:
        """
        Execute all tasks in parallel (group).

        Returns:
            GroupResult for the parallel execution
        """
        if not self.tasks:
            raise ValueError("Workflow has no tasks")

        # Build group
        task_signatures = []
        for task_info in self.tasks:
            from celery import signature

            sig = signature(
                task_info["task_name"],
                args=task_info["args"],
                kwargs=task_info["kwargs"],
            )
            task_signatures.append(sig)

        # Execute group
        workflow_group = group(*task_signatures)
        return workflow_group.apply_async()

    def execute_with_callback(
        self,
        callback_task: str,
        callback_args: tuple = (),
        callback_kwargs: dict[str, Any] = None,
    ) -> AsyncResult:
        """
        Execute workflow as a chord (parallel tasks with callback).

        Args:
            callback_task: Task to execute after all parallel tasks complete
            callback_args: Callback task arguments
            callback_kwargs: Callback task keyword arguments

        Returns:
            AsyncResult for the chord
        """
        if not self.tasks:
            raise ValueError("Workflow has no tasks")

        # Build group
        task_signatures = []
        for task_info in self.tasks:
            from celery import signature

            sig = signature(
                task_info["task_name"],
                args=task_info["args"],
                kwargs=task_info["kwargs"],
            )
            task_signatures.append(sig)

        # Build callback
        from celery import signature

        callback_sig = signature(
            callback_task, args=callback_args, kwargs=callback_kwargs or {}
        )

        # Execute chord
        workflow_chord = chord(task_signatures, callback_sig)
        return workflow_chord.apply_async()


def create_task_chain(*task_signatures) -> chain:
    """
    Create a chain of tasks.

    Args:
        *task_signatures: Celery task signatures

    Returns:
        Chain object
    """
    return chain(*task_signatures)


def create_task_group(*task_signatures) -> group:
    """
    Create a group of parallel tasks.

    Args:
        *task_signatures: Celery task signatures

    Returns:
        Group object
    """
    return group(*task_signatures)


def create_task_chord(task_group: group, callback_signature) -> chord:
    """
    Create a chord (parallel tasks with callback).

    Args:
        task_group: Group of parallel tasks
        callback_signature: Callback task signature

    Returns:
        Chord object
    """
    return chord(task_group, callback_signature)
