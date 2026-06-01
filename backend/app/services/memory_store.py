"""
Memory Store — structured transient state container for a single plan execution.
Accumulates intermediate logs, dynamic arguments, insights, and failures.
Supports dynamic parameter resolution like $step1.output.customer_ids.
"""

import re
import time
from typing import Any, Dict, List, Optional


class MemoryStore:
    """Structured in-memory store for a single plan execution."""

    def __init__(self, plan_id: str, session_id: str):
        self.plan_id = plan_id
        self.session_id = session_id
        self.entries: Dict[str, Any] = {
            "user_context": {},      # RM query, conversation history
            "plan": {},              # Initial plan steps
            "tool_logs": [],         # Chronological list of: (step_number, tool, input, output, ts, status)
            "candidates": [],        # Intermediate customer IDs/lists
            "insights": [],          # Derived domain insights or qualitative facts
            "failures": [],          # Failed step errors and retries context
        }
        self.pinned_facts: List[Dict[str, Any]] = []  # Facts that are preserved during compaction
        self.summarized_history: Optional[str] = None

    def store(self, memory_type: str, entry: Dict[str, Any]):
        """Stores a new memory entry in the appropriate partition."""
        if memory_type in self.entries:
            if isinstance(self.entries[memory_type], list):
                self.entries[memory_type].append(entry)
            else:
                self.entries[memory_type].update(entry)
        else:
            self.entries[memory_type] = entry

        # Proactively extract and pin candidate items or critical compliance alerts
        if memory_type == "tool_logs":
            output = str(entry.get("output", ""))
            # If we see lists of customer IDs (e.g. CUST012), automatically tag them as pinned candidates
            cids = list(set(re.findall(r"CUST\d{3}", output, re.IGNORECASE)))
            if cids:
                self.pin_fact(
                    key="customer_ids",
                    value=cids,
                    source=f"step_{entry.get('step', 'unknown')}",
                    description="Pinned candidate customers found during tool execution"
                )

    def pin_fact(self, key: str, value: Any, source: str, description: str = ""):
        """Pins a critical domain fact so that it is never compressed away by the Summariser."""
        fact = {
            "key": key,
            "value": value,
            "source": source,
            "description": description,
            "pinned_at": time.time()
        }
        # Avoid duplicate pins for same key/value pair
        for pf in self.pinned_facts:
            if pf["key"] == key and pf["value"] == value:
                return
        self.pinned_facts.append(fact)

    def retrieve(self, key: str, memory_type: Optional[str] = None) -> Optional[Any]:
        """Retrieves a value from the memory partitions or pinned facts."""
        if memory_type and memory_type in self.entries:
            partition = self.entries[memory_type]
            if isinstance(partition, dict):
                return partition.get(key)
            elif isinstance(partition, list):
                return [x for x in partition if x.get("key") == key or x.get("tool") == key]

        # Check pinned facts
        for pf in self.pinned_facts:
            if pf["key"] == key:
                return pf["value"]

        # Check in entries directly
        for part in self.entries.values():
            if isinstance(part, dict) and key in part:
                return part[key]
        return None

    def get_token_count(self) -> int:
        """
        Estimates the token size of the accumulated memory logs.
        Uses a standard estimation of ~4 characters per token.
        """
        total_chars = 0
        total_chars += len(str(self.entries.get("user_context", "")))
        total_chars += len(str(self.entries.get("plan", "")))
        for log in self.entries.get("tool_logs", []):
            total_chars += len(str(log))
        total_chars += len(str(self.pinned_facts))
        if self.summarized_history:
            total_chars += len(self.summarized_history)
        return total_chars // 4

    def get_context_for_planner(self) -> str:
        """
        Builds a comprehensive textual context summary of the memory for the Planner LLM.
        This provides perfect chronological grounding of what has succeeded/failed.
        """
        lines = []
        lines.append("=== AGENT EXECUTION MEMORY ===")
        lines.append(f"Plan ID: {self.plan_id}")

        if self.summarized_history:
            lines.append(f"COMPACTED MEMORY SUMMARY: {self.summarized_history}")

        lines.append("\nPINNED CRITICAL FACTS:")
        if self.pinned_facts:
            for i, pf in enumerate(self.pinned_facts, 1):
                lines.append(f"{i}. [{pf['key']}] from {pf['source']}: {pf['value']} ({pf['description']})")
        else:
            lines.append("None")

        lines.append("\nRECENT LOGS:")
        logs = self.entries.get("tool_logs", [])
        # Show recent raw details
        if logs:
            for log in logs[-3:]:  # Focus on the most recent 3 steps for full logs
                lines.append(
                    f"Step {log.get('step')}: Tool '{log.get('tool')}' Status={log.get('status')} "
                    f"Result={str(log.get('output'))[:300]}..."
                )
        else:
            lines.append("No actions taken yet.")

        failures = self.entries.get("failures", [])
        if failures:
            lines.append("\nKNOWN EXECUTION FAILURES:")
            for f in failures:
                lines.append(f"- Step {f.get('step')}: {f.get('error')} (Retries: {f.get('retries')})")

        lines.append("=== END MEMORY ===")
        return "\n".join(lines)

    def resolve_dynamic_notation(self, value: str) -> Any:
        """
        Resolves dynamic notations like '$step1.output.customer_ids' or '$step3.output'.
        Parses results dynamically out of tool logs in this memory container.
        """
        if not isinstance(value, str) or not value.startswith("$step"):
            return value

        match = re.match(r"\$step(\d+)(?:\.output(?:\.(\w+))?)?", value)
        if not match:
            return value

        ref_step_num = int(match.group(1))
        key_name = match.group(2)

        # Look up step result in our tool logs
        ref_log = None
        for log in self.entries.get("tool_logs", []):
            if log.get("step") == ref_step_num and log.get("status") == "success":
                ref_log = log
                break

        if not ref_log:
            return value

        result_text = str(ref_log.get("output", ""))

        # Try to parse as JSON first
        import json
        try:
            parsed_data = json.loads(result_text)
            if isinstance(parsed_data, dict):
                if key_name and key_name in parsed_data:
                    return parsed_data[key_name]
                return parsed_data
            if isinstance(parsed_data, list) and not key_name:
                return parsed_data
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse customer IDs if no key or looking for customer ID lists
        customer_ids = list(set(re.findall(r"CUST\d{3}", result_text, re.IGNORECASE)))
        if customer_ids:
            if key_name == "customer_ids_csv":
                return ",".join(customer_ids)
            if key_name == "customer_ids":
                return customer_ids
            return customer_ids[0]

        return result_text

    def to_json(self) -> Dict[str, Any]:
        """Serializes current memory state to save into chat_messages DB."""
        return {
            "plan_id": self.plan_id,
            "session_id": self.session_id,
            "summarized_history": self.summarized_history,
            "pinned_facts": self.pinned_facts,
            "entries": {
                "user_context": self.entries["user_context"],
                "plan": self.entries["plan"],
                # Strip massive responses to keep message size reasonable
                "tool_logs": [
                    {
                        "step": log.get("step"),
                        "tool": log.get("tool"),
                        "status": log.get("status"),
                        "output": str(log.get("output"))[:1000] + ("..." if len(str(log.get("output"))) > 1000 else ""),
                        "ts": log.get("ts")
                    } for log in self.entries["tool_logs"]
                ],
                "failures": self.entries["failures"]
            }
        }
