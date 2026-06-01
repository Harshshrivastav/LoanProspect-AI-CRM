"""
Memory Summariser — compacts older Memory entries to prevent LLM context-window overload.
Uses Gemini to generate structured historical summaries while maintaining critical facts.
"""

from app.config import settings
from app.services.memory_store import MemoryStore
from app.utils.logger import get_logger
import litellm
import time

logger = get_logger(__name__)


class MemorySummariser:
    """Orchestrates memory compaction via LLM compression prompts."""

    def __init__(self, token_threshold: int = 4000):
        self.token_threshold = token_threshold

    def should_summarise(self, memory: MemoryStore) -> bool:
        """Determines if the memory size has exceeded the token threshold."""
        return memory.get_token_count() > self.token_threshold

    def compact(self, memory: MemoryStore) -> str:
        """
        Replaces older raw tool logs with a compressed, cohesive narrative summary.
        Keeps the last 2 steps fully raw in the active window (sliding window)
        and preserves pinned facts intact.
        """
        logs = memory.entries.get("tool_logs", [])
        if len(logs) <= 2:
            # Not enough logs to summarise; sliding window requires keeping at least 2
            return memory.summarized_history or ""

        # Divide logs: older logs to compact, and the recent 2 logs to keep completely raw
        logs_to_compact = logs[:-2]
        logs_to_keep = logs[-2:]

        logger.info(f"Compacting {len(logs_to_compact)} older tool execution logs in MemoryStore...")

        # Build prompt for compaction
        summary_prompt = f"""You are a senior banking strategy archivist. Your task is to compress a set of detailed technical step execution logs into a concise, high-density business-insight summary.
The banker needs to understand exactly what was discovered, what tools were called, and the final outcomes.

Older execution logs to summarize:
"""
        for log in logs_to_compact:
            summary_prompt += f"- Step {log.get('step')} ({log.get('tool')}): Input={log.get('input')} | Status={log.get('status')} | Output={str(log.get('output'))[:1000]}\n"

        summary_prompt += """
RULES:
1. Be extremely concise. Keep the summary under 150 words.
2. List the specific numerical or qualitative insights discovered (e.g. customer IDs found, credit scores, compliance risk alerts).
3. Do not lose key facts. Summarize the steps chronologically.
"""

        try:
            model_name = "gemini/gemini-2.0-flash" if "2.5" in settings.gemini_model else f"gemini/{settings.gemini_model}"
            
            # Rate-resilient LiteLLM completion
            response = litellm.completion(
                model=model_name,
                api_key=settings.gemini_api_key,
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.3,
                max_tokens=600
            )
            summary_text = response.choices[0].message.content.strip()
            
            # Append new summary to existing summary
            if memory.summarized_history:
                memory.summarized_history = (
                    f"{memory.summarized_history}\nThen, completed subsequent steps: {summary_text}"
                )
            else:
                memory.summarized_history = summary_text

            # Keep only the logs_to_keep raw in memory log partition
            memory.entries["tool_logs"] = logs_to_keep
            logger.info("Memory compaction completed successfully.")
            return memory.summarized_history

        except Exception as e:
            logger.error(f"Failed to generate memory summary compaction: {e}")
            # Fallback local compression narrative
            fallback = f"Executed {len(logs_to_compact)} steps successfully including: " + ", ".join([str(l.get("tool")) for l in logs_to_compact])
            memory.summarized_history = f"{memory.summarized_history}\n{fallback}" if memory.summarized_history else fallback
            memory.entries["tool_logs"] = logs_to_keep
            return memory.summarized_history
