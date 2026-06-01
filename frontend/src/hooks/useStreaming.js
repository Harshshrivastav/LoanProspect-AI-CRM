// src/hooks/useStreaming.js
import { useState, useCallback, useRef } from "react";
import { streamChat } from "../api/client";

export function useStreaming() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentActivity, setAgentActivity] = useState([]); // array of {type, agent, tool, text, timestamp}
  const [currentText, setCurrentText] = useState("");
  const [steps, setSteps] = useState([]);
  const [error, setError] = useState(null);
  const abortRef = useRef(false);

  const send = useCallback(
    async (
      message,
      sessionId = null,
      customerContext = null,
      callbacksOrMode = {},
      callbacks = {},
    ) => {
      let mode = "auto";
      let actualCallbacks = callbacks;

      if (typeof callbacksOrMode === "string") {
        mode = callbacksOrMode;
        actualCallbacks = callbacks;
      } else {
        actualCallbacks = callbacksOrMode;
      }

      const {
        onChunk = null,
        onAgentEvent = null,
        onEvent = null,
        onDone = null,
        onError = null,
      } = typeof actualCallbacks === "object" && actualCallbacks !== null ? actualCallbacks : {};

      abortRef.current = false;
      setIsStreaming(true);
      setAgentActivity([]);
      setCurrentText("");
      setSteps([]);
      setError(null);

      const localSteps = [];
      const localThoughts = [];
      let localPlan = null;
      let localFeedback = null;
      let localSuggestions = [];

      const addActivity = (entry) => {
        const enriched = { ...entry, timestamp: new Date().toISOString() };
        setAgentActivity((prev) => [...prev, enriched]);
        if (onAgentEvent) onAgentEvent(enriched, [...localSteps], [...localThoughts], localPlan, localFeedback, [...localSuggestions]);
      };

      try {
        let fullText = "";

        for await (const event of streamChat(
          message,
          sessionId,
          customerContext,
          mode,
        )) {
          if (abortRef.current) break;
          if (onEvent) onEvent(event);

          switch (event.type) {
            case "suggestions":
              localSuggestions = event.suggestions || [];
              addActivity({
                type: "suggestions",
                text: `Generated ${localSuggestions.length} contextual next steps.`,
                suggestions: localSuggestions,
              });
              break;
            case "human_feedback":
              localFeedback = {
                message: event.message,
                options: event.options,
                feedbackType: event.feedback_type || "confirm",
                draft: event.draft || "",
                customerName: event.customer_name || "",
                phone: event.phone || "",
              };
              addActivity({
                type: "human_feedback",
                text: event.message,
                options: event.options,
                feedbackType: event.feedback_type || "confirm",
                draft: event.draft || "",
                customerName: event.customer_name || "",
                phone: event.phone || "",
              });
              break;
            case "paused_hitl":
              localFeedback = {
                message: `Awaiting outreach confirmation for Step ${event.step_number}`,
                options: ["Approve Draft", "Dismiss Draft"],
                feedbackType: "outreach_review",
                draft: event.draft || "",
                step_number: event.step_number,
                tool_name: event.tool_name
              };
              addActivity({
                type: "human_feedback",
                text: `Awaiting outreach confirmation for Step ${event.step_number}`,
                options: ["Approve Draft", "Dismiss Draft"],
                feedbackType: "outreach_review",
                draft: event.draft || "",
              });
              break;
            case "plan":
              localPlan = {
                plan_id: event.plan_id,
                steps: event.steps,
                complexity: event.complexity,
                requires_approval: event.requires_approval,
                status: event.requires_approval ? "planning" : "running"
              };
              addActivity({
                type: "plan",
                text: "Sequential execution plan formulated.",
                plan: localPlan
              });
              break;
            case "step_start":
              addActivity({
                type: "step_start",
                text: `Starting Step ${event.step_number}: ${event.description}`,
                step_number: event.step_number,
                tool: event.tool_name
              });
              break;
            case "thought":
              localThoughts.push({
                text: event.text,
                step_number: event.step_number,
                ts: Date.now()
              });
              addActivity({
                type: "thought",
                text: event.text,
                step_number: event.step_number
              });
              break;
            case "status":
              addActivity({
                type: "status",
                text: event.message,
                agent: event.agent || "Orchestrator",
              });
              break;
            case "agent_start":
              addActivity({
                type: "agent_start",
                agent: event.agent,
                text: event.task || "Working...",
              });
              break;
            case "tool_call":
              localSteps.push({
                step_number: event.step_number,
                tool: event.tool,
                input: event.input,
                observation: null,
                ts: Date.now(),
              });
              addActivity({
                type: "tool_call",
                tool: event.tool,
                step_number: event.step_number,
                text: String(event.input || "").slice(0, 100),
              });
              break;
            case "tool_result":
              const matchingStep = localSteps.find(s => s.step_number === event.step_number && s.tool === event.tool) || localSteps[localSteps.length - 1];
              if (matchingStep) {
                matchingStep.observation = event.output;
              }
              addActivity({
                type: "tool_result",
                tool: event.tool,
                step_number: event.step_number,
                text: String(event.output || "").slice(0, 200),
              });
              break;
            case "loop_decision":
              addActivity({
                type: "loop_decision",
                step_number: event.step_number,
                text: `Loop Decision: ${event.decision} (${event.reason})`,
                decision: event.decision,
                reason: event.reason
              });
              break;
            case "replanned":
              addActivity({
                type: "replanned",
                step_number: event.step_number,
                text: `Step failed! Dynamic re-planner triggered. Branch updated.`,
                new_steps: event.new_steps
              });
              break;
            case "memory_update":
              addActivity({
                type: "memory_update",
                step_number: event.step_number,
                text: event.summary
              });
              break;
            case "memory_summary":
              addActivity({
                type: "memory_summary",
                text: `Memory Compaction: ${event.summary}`,
                summary: event.summary
              });
              break;
            case "agent_done":
              addActivity({
                type: "agent_done",
                agent: event.agent,
                text: String(event.result || "").slice(0, 200),
              });
              break;
            case "chunk":
              fullText += event.text || "";
              setCurrentText(fullText);
              if (onChunk) onChunk(event.text, fullText);
              break;
            case "done":
              if (event.final_answer) {
                fullText = event.final_answer;
                setCurrentText(fullText);
              }
              const finalSteps = (event.steps && event.steps.length > 0) ? event.steps : localSteps;
              setSteps(finalSteps);
              if (onDone) onDone(fullText, finalSteps, localThoughts, localPlan, localFeedback, localSuggestions, event.data_grid);
              break;
            case "error":
              setError(event.error);
              addActivity({ type: "error", text: event.error });
              if (onError) onError(event.error);
              break;
          }
        }
      } catch (err) {
        setError(err.message);
        addActivity({ type: "error", text: err.message });
        if (onError) onError(err.message);
      } finally {
        setIsStreaming(false);
      }
    },
    [],
  );


  const abort = useCallback(() => {
    abortRef.current = true;
    setIsStreaming(false);
  }, []);

  return { send, abort, isStreaming, agentActivity, currentText, steps, error };
}
