"""
Loop Controller — monitors execution progress, handles errors, and enforces safety bounds.
Determines whether to continue, re-plan dynamically, or abort execution.
"""

from typing import Tuple
from app.services.memory_store import MemoryStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoopController:
    """Monitors step execution outputs and decides continuation strategy."""

    MAX_STEPS = 10
    MAX_REPLANS = 1
    MAX_CONSECUTIVE_EMPTY = 3

    def __init__(self):
        self.replan_count = 0
        self.consecutive_empty = 0
        self.total_executed_steps = 0

    def evaluate(self, step_result: dict, memory: MemoryStore) -> Tuple[str, str]:
        """
        Evaluates step status and results to decide next control flow action.
        
        Args:
            step_result: Dict containing 'status' ('success' or 'failed'), 'output', 'retry_count'
            memory: Active MemoryStore containing logs
            
        Returns:
            Tuple[str, str]: (decision, reason)
                decision options: 'continue' | 'replan' | 'skip' | 'abort'
        """
        self.total_executed_steps += 1
        
        # Enforce maximum safety limits on overall executed steps count
        if self.total_executed_steps >= self.MAX_STEPS:
            logger.warning(f"LoopController: Aborting. Maximum step execution threshold ({self.MAX_STEPS}) exceeded.")
            return ("abort", "Safety threshold: Maximum total plan steps exceeded.")

        status = step_result.get("status", "success")
        output = str(step_result.get("output", "")).strip()

        # 1. Handle Hard Failures
        if status == "failed":
            if self.replan_count < self.MAX_REPLANS:
                self.replan_count += 1
                logger.info("LoopController: Step failure triggered re-planning.")
                return ("replan", f"Step failed. Triggering dynamic re-planner. (Replan {self.replan_count}/{self.MAX_REPLANS})")
            else:
                logger.warning("LoopController: Aborting. Step failed and maximum replan attempts are exhausted.")
                return ("abort", "Step execution failed. Maximum re-planning runs exhausted.")

        # 2. Check for Empty or Trivial Observations (Anomalous blank values)
        is_empty = (not output) or (output.lower() in ["none", "null", "[]", "{}", "empty", "no customers", "no data"])
        if is_empty:
            self.consecutive_empty += 1
            logger.warning(f"LoopController: Received empty observation (consecutive: {self.consecutive_empty}).")
            if self.consecutive_empty >= self.MAX_CONSECUTIVE_EMPTY:
                return ("abort", f"Aborted: {self.consecutive_empty} consecutive empty observation blocks received.")
            
            # If empty but we haven't hit threshold yet, choose to skip or continue with warning
            return ("continue", f"Empty result detected at step. Proceeding anyway ({self.consecutive_empty}/{self.MAX_CONSECUTIVE_EMPTY} consecutive empty warnings).")

        # Reset consecutive empty counter upon receiving a valid observation
        self.consecutive_empty = 0

        # 3. Success Path
        return ("continue", "Step successfully completed with valid outputs.")
