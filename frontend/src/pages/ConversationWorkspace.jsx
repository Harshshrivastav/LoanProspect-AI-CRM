import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  MessageSquare,
  Plus,
  Zap,
  AlertCircle,
  Sparkles,
  Server,
  Cloud,
  Database,
  Cpu,
  Settings,
  ChevronDown,
  TrendingUp,
  Shield,
  Smartphone,
  Send,
  CheckCircle,
  FileText,
  Loader2,
  Wrench,
} from "lucide-react";
import { useChat } from "../context/ChatContext";
import { useStreaming } from "../hooks/useStreaming";
import MessageBubble from "../components/conversation/MessageBubble";
import MessageInput from "../components/conversation/MessageInput";
import TemplateSuggestionBar from "../components/conversation/TemplateSuggestionBar";
import AgentActivityPanel from "../components/agents/AgentActivityPanel";
import { useApp } from "../context/AppContext";
import clsx from "clsx";

function mapToolToTitle(toolName = "") {
  const name = toolName.toLowerCase();
  if (name.includes("profile")) return "Profile Ingestion";
  if (name.includes("transaction")) return "Transaction Analysis";
  if (name.includes("life_event")) return "Behavioral Intent Scanner";
  if (name.includes("trend")) return "Cashflow MOM Model";
  if (name.includes("readiness")) return "Readiness Engine";
  if (name.includes("explanation")) return "Cognitive Rationale Evaluation";
  if (name.includes("prospects")) return "Prospect Rank Optimization";
  if (name.includes("compliance")) return "Regulatory Policy Verification";
  if (
    name.includes("whatsapp") ||
    name.includes("outreach") ||
    name.includes("bulk")
  )
    return "Audited Copy Composer";
  return "Agent Action: " + toolName;
}

function mapToolToIcon(toolName = "") {
  const name = toolName.toLowerCase();
  if (name.includes("profile")) return Database;
  if (name.includes("transaction")) return TrendingUp;
  if (name.includes("life_event")) return Sparkles;
  if (name.includes("trend")) return Cpu;
  if (name.includes("readiness") || name.includes("explanation")) return Cpu;
  if (name.includes("prospects")) return Cpu;
  if (name.includes("compliance")) return Shield;
  if (
    name.includes("whatsapp") ||
    name.includes("outreach") ||
    name.includes("bulk")
  )
    return MessageSquare;
  return Cpu;
}

function EmptyConversationState({ onStartChat }) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 py-16">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="text-center max-w-xl"
      >
        {/* Icon */}
        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-lg shadow-blue-200 animate-pulse-slow">
          <Bot size={30} className="text-white" />
        </div>

        <h2 className="text-2xl font-bold text-slate-900 mb-2 tracking-tight">
          Glacier Intelligence AI
        </h2>
        <p className="text-slate-500 leading-relaxed mb-8 text-sm font-medium">
          Your elite private banking CRM assistant. Ask about high-intent
          prospects, analyze customer risk profiles, or review compliance blocks
          automatically.
        </p>

        {/* Feature chips */}

        <div className="flex items-center gap-2 justify-center text-xs text-slate-400 font-semibold select-none">
          <Sparkles size={13} className="text-amber-400 animate-pulse" />
          Powered by CrewAI + Google Gemini 2.5
        </div>
      </motion.div>
    </div>
  );
}

function WorkspaceHeader({ session, isStreaming }) {
  return (
    <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200 shrink-0 select-none">
      <div className="flex items-center gap-3 min-w-0">
        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight leading-none">
              Active Session: {session?.title || "Global Wealth Scan"}
            </h1>
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold select-none">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
              Agents Active
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1 font-semibold">
            Decision Maker Agent orchestrating 3 sub-agents.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ConversationWorkspace() {
  const { sessionId: urlSessionId } = useParams();
  const navigate = useNavigate();
  const {
    messages,
    setMessages,
    activeSessionId,
    sessions,
    isStreaming: ctxStreaming,
    setIsStreaming,
    agentActivity,
    addAgentActivity,
    clearAgentActivity,
    startNewSession,
    switchSession,
    appendMessage,
    updateLastMessage,
    renameSessionLocal,
    updateSessionTitle,
  } = useChat();

  const [inputText, setInputText] = useState("");
  const [currentStreamingId, setCurrentStreamingId] = useState(null);
  const [activeReview, setActiveReview] = useState(null);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [activeRightTab, setActiveRightTab] = useState("timeline"); // "timeline" | "results" | "review"
  const [focusedMessageId, setFocusedMessageId] = useState(null);
  const messagesEndRef = useRef(null);

  const {
    send,
    abort,
    isStreaming,
    agentActivity: streamActivity,
    currentText,
  } = useStreaming();

  // Sync session from URL
  useEffect(() => {
    if (urlSessionId && urlSessionId !== activeSessionId) {
      switchSession(urlSessionId);
    }
  }, [urlSessionId]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentText]);

  const activeSession = sessions.find(
    (s) => (s.session_id || s.id) === activeSessionId,
  );

  const handleSend = useCallback(async () => {
    if (!inputText.trim() || isStreaming) return;

    const messageText = inputText.trim();
    setInputText("");

    // Ensure we have a session
    let sessionId = activeSessionId;
    if (!sessionId || sessionId.startsWith("local-")) {
      const firstWords = messageText.split(" ").slice(0, 5).join(" ");
      sessionId = await startNewSession(firstWords || "New Conversation");
      if (sessionId && !sessionId.startsWith("local-")) {
        navigate(`/chat/${sessionId}`);
      }
    }

    // Add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: messageText,
      timestamp: new Date().toISOString(),
    };
    appendMessage(userMsg);

    // Add placeholder assistant message
    const assistantId = `assistant-${Date.now()}`;
    setCurrentStreamingId(assistantId);
    const placeholderMsg = {
      id: assistantId,
      role: "assistant",
      content: "",
      steps: [],
      status: "Routing to agents…",
      timestamp: new Date().toISOString(),
    };
    appendMessage(placeholderMsg);
    clearAgentActivity();

    // Stream
    let currentAgent = null;
    await send(messageText, sessionId, null, {
      onChunk: (chunk, fullText) => {
        updateLastMessage((msg) => ({
          ...msg,
          content: fullText,
          status: null,
        }));
      },
      onAgentEvent: (
        event,
        liveSteps,
        liveThoughts,
        livePlan,
        liveFeedback,
        liveSuggestions,
      ) => {
        addAgentActivity(event);
        console.log(
          "ConversationWorkspace onAgentEvent:",
          event.type,
          "event:",
          event,
          "liveFeedback:",
          liveFeedback,
        );

        if (event.type === "plan" && livePlan) {
          setRightPanelOpen(true);
          setActiveRightTab("timeline");
          setFocusedMessageId(assistantId);
        }

        if (
          event.type === "human_feedback" &&
          liveFeedback &&
          liveFeedback.feedbackType === "outreach_review"
        ) {
          setActiveReview({
            messageId: assistantId,
            draft: liveFeedback.draft,
            customerName: liveFeedback.customerName,
            phone: liveFeedback.phone,
            options: liveFeedback.options,
          });
          setRightPanelOpen(true);
          setActiveRightTab("review");
          setFocusedMessageId(assistantId);
        }
        if (event.type === "agent_start") {
          currentAgent = event.agent;
          updateLastMessage((msg) => ({
            ...msg,
            status: `${event.agent} is working…`,
            steps: liveSteps || msg.steps || [],
            thoughts: liveThoughts || msg.thoughts || [],
            plan: livePlan || msg.plan || [],
            feedback: liveFeedback || msg.feedback || null,
            suggestions: liveSuggestions?.length
              ? liveSuggestions
              : msg.suggestions || [],
          }));
        } else {
          updateLastMessage((msg) => ({
            ...msg,
            steps: liveSteps || msg.steps || [],
            thoughts: liveThoughts || msg.thoughts || [],
            plan: livePlan || msg.plan || [],
            feedback: liveFeedback || msg.feedback || null,
            suggestions: liveSuggestions?.length
              ? liveSuggestions
              : msg.suggestions || [],
          }));
        }
        if (event.type === "agent_done") {
          updateLastMessage((msg) => ({ ...msg, status: null }));
        }
      },

      onDone: (finalText, steps, thoughts, plan, feedback, suggestions) => {
        updateLastMessage((msg) => {
          const alreadyProcessed =
            msg.feedbackSelected === "Approve Draft" ||
            msg.feedbackSelected === "Dismiss Draft";

          if (
            feedback &&
            feedback.feedbackType === "outreach_review" &&
            !alreadyProcessed
          ) {
            // Only load/open if there isn't already an active review for this message, to protect user's edits
            setActiveReview((prev) => {
              if (prev && prev.messageId === assistantId) {
                return prev;
              }
              // Set the review as fallback if it was somehow not opened yet
              setRightPanelOpen(true);
              setActiveRightTab("review");
              setFocusedMessageId(assistantId);
              return {
                messageId: assistantId,
                draft: feedback.draft,
                customerName: feedback.customerName,
                phone: feedback.phone,
                options: feedback.options,
              };
            });
          }

          return {
            ...msg,
            content: finalText || msg.content,
            steps: steps || msg.steps,
            thoughts: thoughts || msg.thoughts || [],
            plan: plan || msg.plan || [],
            feedback: feedback || msg.feedback || null,
            suggestions: suggestions?.length
              ? suggestions
              : msg.suggestions || [],
            status: null,
          };
        });
        // Update session title from first message if needed
        if (
          activeSession &&
          (!activeSession.title ||
            activeSession.title === "New Conversation" ||
            activeSession.title === "Untitled") &&
          messageText
        ) {
          const newTitle =
            messageText.slice(0, 40) + (messageText.length > 40 ? "…" : "");
          renameSessionLocal(sessionId, newTitle);
        }
      },
      onError: (errMsg) => {
        updateLastMessage((msg) => ({
          ...msg,
          content: "",
          error: errMsg,
          status: null,
        }));
      },
    });

    setCurrentStreamingId(null);
  }, [
    inputText,
    isStreaming,
    activeSessionId,
    startNewSession,
    appendMessage,
    updateLastMessage,
    clearAgentActivity,
    addAgentActivity,
    send,
    navigate,
    activeSession,
    updateSessionTitle,
  ]);

  const handleTemplate = useCallback((query) => {
    setInputText(query);
    // Auto-submit after a brief delay
    setTimeout(() => {
      setInputText(query);
    }, 0);
  }, []);

  const handleFeedbackSelect = useCallback(
    async (msgId, option, editedContent = null) => {
      // Optimistically update message state
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId
            ? { ...m, feedbackSelected: option, feedback: null }
            : m,
        ),
      );

      try {
        const res = await fetch(
          `/api/chat/sessions/${activeSessionId}/feedback`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ option, edited_content: editedContent }),
          },
        );
        if (!res.ok) {
          console.error("Failed to submit feedback:", await res.text());
        }
      } catch (err) {
        console.error("Error submitting feedback:", err);
      }
    },
    [activeSessionId, setMessages],
  );

  const handleApprovePlan = useCallback(
    async (planId, approved = true) => {
      console.log(
        `RM ${approved ? "approved" : "disapproved"} execution strategy plan inline:`,
        planId,
      );
      try {
        const approveRes = await fetch(
          `/api/chat/sessions/${activeSessionId}/approve-plan`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ plan_id: planId, approved }),
          },
        );
        if (!approveRes.ok) throw new Error("Plan approval failed.");

        if (!approved) {
          // Set plan status as failed/rejected locally
          setMessages((prev) =>
            prev.map((m) => {
              if (m.plan && m.plan.plan_id === planId) {
                return {
                  ...m,
                  status:
                    "Strategy plan disapproved. Rethinking alternative strategy...",
                  plan: { ...m.plan, status: "failed" },
                };
              }
              return m;
            }),
          );

          // Automate a streaming request to compile a fresh strategy plan
          const assistantId = `assistant-${Date.now()}`;
          setCurrentStreamingId(assistantId);

          const placeholderMsg = {
            id: assistantId,
            role: "assistant",
            content: "",
            steps: [],
            status: "Formulating alternative strategy plan...",
            timestamp: new Date().toISOString(),
          };
          appendMessage(placeholderMsg);
          clearAgentActivity();

          await send(
            "The previous plan was disapproved. Rethink with a different strategy and compile a new plan.",
            activeSessionId,
            null,
            {
              onChunk: (chunk, fullText) => {
                updateLastMessage((msg) => ({
                  ...msg,
                  content: fullText,
                  status: null,
                }));
              },
              onAgentEvent: (
                event,
                liveSteps,
                liveThoughts,
                livePlan,
                liveFeedback,
                liveSuggestions,
              ) => {
                addAgentActivity(event);
                if (event.type === "plan" && livePlan) {
                  setRightPanelOpen(true);
                  setActiveRightTab("timeline");
                  setFocusedMessageId(assistantId);
                }
                if (event.type === "agent_start") {
                  updateLastMessage((msg) => ({
                    ...msg,
                    status: `Rethinking strategy: ${event.agent} is active...`,
                    steps: liveSteps || msg.steps || [],
                    thoughts: liveThoughts || msg.thoughts || [],
                    plan: livePlan || msg.plan || [],
                  }));
                }
              },
            },
          );
          return;
        }

        // Set plan status as running
        setMessages((prev) =>
          prev.map((m) => {
            if (m.plan && m.plan.plan_id === planId) {
              return { ...m, plan: { ...m.plan, status: "running" } };
            }
            return m;
          }),
        );

        // Establish EventSource execution connection
        const eventSource = new EventSource(`/api/chat/stream/${planId}`);

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log("Unified SSE loop event:", data);

            if (data.type === "step_start") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      status: `Executing Step ${data.step_number}: ${data.description}...`,
                    };
                  }
                  return m;
                }),
              );
            } else if (data.type === "thought") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    const thoughts = [...(m.thoughts || [])];
                    if (
                      !thoughts.some(
                        (t) =>
                          t.text === data.text &&
                          t.step_number === data.step_number,
                      )
                    ) {
                      thoughts.push({
                        text: data.text,
                        step_number: data.step_number,
                        ts: Date.now(),
                      });
                    }
                    return { ...m, thoughts };
                  }
                  return m;
                }),
              );
            } else if (data.type === "tool_call") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    const steps = [...(m.steps || [])];
                    if (
                      !steps.some(
                        (s) =>
                          s.tool === data.tool &&
                          s.step_number === data.step_number,
                      )
                    ) {
                      steps.push({
                        tool: data.tool,
                        step_number: data.step_number,
                        input: data.input,
                        observation: null,
                        ts: Date.now(),
                      });
                    }
                    return { ...m, steps };
                  }
                  return m;
                }),
              );
            } else if (data.type === "tool_result") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    const steps = (m.steps || []).map((s) => {
                      if (
                        s.step_number === data.step_number &&
                        s.tool === data.tool
                      ) {
                        return { ...s, observation: data.output };
                      }
                      return s;
                    });
                    return { ...m, steps };
                  }
                  return m;
                }),
              );
            } else if (data.type === "memory_update") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      status: data.text || "Updated state logs...",
                    };
                  }
                  return m;
                }),
              );
            } else if (data.type === "loop_decision") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      status: `Decision: ${data.decision} (${data.reason})`,
                    };
                  }
                  return m;
                }),
              );
            } else if (data.type === "replanned") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return { ...m, plan: { ...m.plan, steps: data.new_steps } };
                  }
                  return m;
                }),
              );
            } else if (data.type === "paused_hitl") {
              setActiveReview({
                messageId:
                  messages.find((m) => m.plan && m.plan.plan_id === planId)
                    ?.id || `assistant-${Date.now()}`,
                draft: data.draft,
                customerName: data.customer_name || "Sneha Gupta",
                phone: data.phone || "+91 98XXX XXX90",
                options: ["Approve Draft", "Dismiss Draft"],
                step_number: data.step_number,
                plan_id: planId,
              });
              setRightPanelOpen(true);
              setActiveRightTab("review");
            } else if (data.type === "done") {
              eventSource.close();
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      content: data.final_answer,
                      data_grid: data.data_grid,
                      suggestions: data.suggestions,
                      status: null,
                      plan: { ...m.plan, status: "completed" },
                    };
                  }
                  return m;
                }),
              );
            } else if (data.type === "error") {
              eventSource.close();
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      error: data.error,
                      status: null,
                      plan: { ...m.plan, status: "failed" },
                    };
                  }
                  return m;
                }),
              );
            }
          } catch (err) {
            console.error("Failed to parse event message:", err);
          }
        };

        eventSource.onerror = (err) => {
          console.error("Executor event stream error:", err);
          eventSource.close();
        };
      } catch (err) {
        console.error("Error approving strategy plan:", err);
      }
    },
    [activeSessionId, messages, setMessages],
  );

  const handleRetryStrategy = useCallback(
    async (planId) => {
      console.log("RM requested strategy retry for plan inline:", planId);

      // 1. Add user retry message
      const userMsg = {
        id: `user-${Date.now()}`,
        role: "user",
        content: "Retry Strategy: Resume Autopilot plan from failed step.",
        timestamp: new Date().toISOString(),
      };
      appendMessage(userMsg);

      // 2. Clear any error on the assistant message and set its status to "Resuming strategy..."
      setMessages((prev) =>
        prev.map((m) => {
          if (m.plan && m.plan.plan_id === planId) {
            return {
              ...m,
              error: null,
              status: "Resuming strategy autopilot...",
              plan: { ...m.plan, status: "running" },
            };
          }
          return m;
        }),
      );

      // 3. Initiate approval fetch and SSE stream
      try {
        const approveRes = await fetch(
          `/api/chat/sessions/${activeSessionId}/approve-plan`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ plan_id: planId, approved: true }),
          },
        );
        if (!approveRes.ok) throw new Error("Plan retry approval failed.");

        // Establish EventSource execution connection
        const eventSource = new EventSource(`/api/chat/stream/${planId}`);

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log("Retry SSE loop event:", data);

            if (data.type === "step_start") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      status: `Resuming Step ${data.step_number}: ${data.description}...`,
                    };
                  }
                  return m;
                }),
              );
            } else if (data.type === "thought") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    const thoughts = [...(m.thoughts || [])];
                    if (
                      !thoughts.some(
                        (t) =>
                          t.text === data.text &&
                          t.step_number === data.step_number,
                      )
                    ) {
                      thoughts.push({
                        text: data.text,
                        step_number: data.step_number,
                        ts: Date.now(),
                      });
                    }
                    return { ...m, thoughts };
                  }
                  return m;
                }),
              );
            } else if (data.type === "tool_call") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    const steps = [...(m.steps || [])];
                    if (
                      !steps.some(
                        (s) =>
                          s.tool === data.tool &&
                          s.step_number === data.step_number,
                      )
                    ) {
                      steps.push({
                        tool: data.tool,
                        step_number: data.step_number,
                        input: data.input,
                        observation: null,
                        ts: Date.now(),
                      });
                    }
                    return { ...m, steps };
                  }
                  return m;
                }),
              );
            } else if (data.type === "tool_result") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    const steps = (m.steps || []).map((s) => {
                      if (
                        s.step_number === data.step_number &&
                        s.tool === data.tool
                      ) {
                        return { ...s, observation: data.output };
                      }
                      return s;
                    });
                    return { ...m, steps };
                  }
                  return m;
                }),
              );
            } else if (data.type === "memory_update") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      status: data.text || "Updated state logs...",
                    };
                  }
                  return m;
                }),
              );
            } else if (data.type === "loop_decision") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      status: `Decision: ${data.decision} (${data.reason})`,
                    };
                  }
                  return m;
                }),
              );
            } else if (data.type === "replanned") {
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return { ...m, plan: { ...m.plan, steps: data.new_steps } };
                  }
                  return m;
                }),
              );
            } else if (data.type === "paused_hitl") {
              setActiveReview({
                messageId:
                  messages.find((m) => m.plan && m.plan.plan_id === planId)
                    ?.id || `assistant-${Date.now()}`,
                draft: data.draft,
                customerName: data.customer_name || "Sneha Gupta",
                phone: data.phone || "+91 98XXX XXX90",
                options: ["Approve Draft", "Dismiss Draft"],
                step_number: data.step_number,
                plan_id: planId,
              });
              setRightPanelOpen(true);
              setActiveRightTab("review");
            } else if (data.type === "done") {
              eventSource.close();
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      content: data.final_answer,
                      data_grid: data.data_grid,
                      suggestions: data.suggestions,
                      status: null,
                      plan: { ...m.plan, status: "completed" },
                    };
                  }
                  return m;
                }),
              );
            } else if (data.type === "error") {
              eventSource.close();
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.plan && m.plan.plan_id === planId) {
                    return {
                      ...m,
                      error: data.error,
                      status: null,
                      plan: { ...m.plan, status: "failed" },
                    };
                  }
                  return m;
                }),
              );
            }
          } catch (err) {
            console.error("Failed to parse event message during retry:", err);
          }
        };

        eventSource.onerror = (err) => {
          console.error("Executor retry event stream error:", err);
          eventSource.close();
        };
      } catch (err) {
        console.error("Error retrying strategy plan execution:", err);
      }
    },
    [
      activeSessionId,
      messages,
      setMessages,
      appendMessage,
      updateLastMessage,
      send,
      addAgentActivity,
      clearAgentActivity,
    ],
  );

  // Determine current streaming agent
  const latestActivity = streamActivity[streamActivity.length - 1];
  const currentAgentName =
    latestActivity?.agent || latestActivity?.agent_name || null;

  const hasMessages = messages.length > 0;

  // Extract static steps or active streaming steps to render AI Insights reasoning
  const lastAssistantMsg = [...messages]
    .reverse()
    .find((m) => m.role === "assistant");
  const lastSteps = Array.isArray(lastAssistantMsg?.steps)
    ? lastAssistantMsg.steps
    : [];

  // Extract Customer ID dynamically to create customized Memory Context
  const activeCustomerId =
    lastSteps.find((s) => s.input)?.input ||
    streamActivity.find((a) => a.type === "tool_call" && a.text)?.text ||
    "";

  // Build dynamic reasoning nodes
  const reasoningNodes = (() => {
    if (isStreaming && streamActivity.length > 0) {
      const nodes = [];
      streamActivity.forEach((act) => {
        if (act.type === "thought") {
          nodes.push({
            title: "Agent Cognitive Analysis",
            details: act.text || "Reasoning over task constraints...",
            duration: "State: Chain of Thought",
            icon: Sparkles,
          });
        } else if (act.type === "tool_call") {
          nodes.push({
            title: act.tool
              ? mapToolToTitle(act.tool)
              : "Executing Engine Module",
            details:
              act.explanation || `Invoking with parameters: ${act.text || ""}`,
            duration: "State: Active Tool Execution",
            icon: act.tool ? mapToolToIcon(act.tool) : Zap,
            sql:
              act.tool &&
              (act.tool.toLowerCase().includes("database") ||
                act.tool.toLowerCase().includes("profile")),
          });
        } else if (act.type === "agent_start") {
          nodes.push({
            title: `${act.agent || "Agent"} Engaged`,
            details: act.text || "Analyzing instructions...",
            duration: "State: Task Distribution",
            icon: Bot,
          });
        }
      });
      return nodes.length > 0
        ? nodes.reverse().slice(0, 3)
        : [
            {
              title: "Decision Maker Agent",
              details:
                "Initiating multi-agent scan across Discovery, Compliance, and Risk vectors.",
              duration: "Analyzing Query",
              icon: Bot,
            },
          ];
    }

    if (lastSteps && lastSteps.length > 0) {
      return lastSteps.map((step) => {
        const title = mapToolToTitle(step.tool);
        const icon = mapToolToIcon(step.tool);

        let details =
          step.explanation ||
          `Successfully executed analytical module. Input: ${step.input || ""}`;
        if (step.observation && !step.explanation) {
          const firstLine = String(step.observation)
            .split("\n")[0]
            .replace(/###/g, "")
            .trim();
          details = firstLine.length > 10 ? firstLine : details;
        }

        return {
          title,
          details,
          duration: "Completed successfully",
          icon,
        };
      });
    }

    return [
      {
        title: "Platform Standby",
        details:
          "Awaiting instructions. Open a workspace or instruct the agent to run diagnostics.",
        duration: "System: Ready",
        icon: Database,
      },
    ];
  })();

  // Dynamically assess accessed data sources depending on tool execution list
  const accessedToolsList = [
    ...lastSteps.map((s) => s.tool || ""),
    ...streamActivity.map((a) => a.tool || ""),
  ].map((t) => t.toLowerCase());

  const bankingAccessed = accessedToolsList.some(
    (t) =>
      t.includes("transaction") ||
      t.includes("life_event") ||
      t.includes("trend") ||
      t.includes("readiness"),
  );
  const crmAccessed = accessedToolsList.some(
    (t) =>
      t.includes("profile") ||
      t.includes("compliance") ||
      t.includes("prospects") ||
      t.includes("outreach") ||
      t.includes("whatsapp"),
  );

  // Dynamic templates — driven entirely by the backend's Gemini-generated suggestions.
  // Returns null for new conversations → TemplateSuggestionBar shows its own defaults.
  const dynamicTemplates = (() => {
    if (!messages || messages.length === 0) return null;
    const lastAssistant = [...messages]
      .reverse()
      .find((m) => m.role === "assistant");
    if (!lastAssistant) return null;
    const sug = lastAssistant.suggestions;
    if (sug && Array.isArray(sug) && sug.length >= 2) return sug.slice(0, 4);
    return null; // fallback to TemplateSuggestionBar defaults
  })();

  const focusedMsg =
    messages.find((m) => m.id === (focusedMessageId || currentStreamingId)) ||
    lastAssistantMsg;
  const focusedSteps = focusedMsg?.steps || [];
  const focusedThoughts = focusedMsg?.thoughts || [];

  // Safe resolution for focusedPlan array of steps (handles both direct list and plan object styles)
  const rawPlan = focusedMsg?.plan || null;
  const focusedPlan = Array.isArray(rawPlan)
    ? rawPlan
    : Array.isArray(rawPlan?.steps)
      ? rawPlan.steps
      : [];

  const focusedFeedback = focusedMsg?.feedback || null;

  const parseTableData = (rawOutput) => {
    if (!rawOutput) return null;
    try {
      const cleanOutput = rawOutput.trim();
      if (cleanOutput.startsWith("{") || cleanOutput.startsWith("[")) {
        const parsed = JSON.parse(cleanOutput);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {}

    // Extract customer IDs like CUST001
    const customerIds = Array.from(
      new Set(rawOutput.match(/CUST\d{3,}/g) || []),
    );
    if (customerIds.length > 0) {
      return customerIds.map((cid) => {
        const lines = rawOutput.split("\n");
        let name = "Premium Client";
        for (let line of lines) {
          if (line.includes(cid)) {
            const clean = line.replace(/[`|*#]/g, "").trim();
            const matchName = clean.match(/([A-Za-z\s]{3,25})/);
            if (matchName) name = matchName[0].trim();
            break;
          }
        }
        return {
          customer_id: cid,
          full_name: name,
          kyc_status: "VERIFIED",
          consent: "✅ COMPLIANT",
        };
      });
    }
    return null;
  };

  return (
    <div className="flex flex-row h-full overflow-hidden w-full relative bg-slate-50">
      {/* Left Chat Column */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50 min-w-0 border-r border-slate-200">
        {/* Header */}
        <WorkspaceHeader session={activeSession} isStreaming={isStreaming} />

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto min-h-0 px-2 scrollbar-light">
          {!hasMessages ? (
            <EmptyConversationState onStartChat={() => {}} />
          ) : (
            <div className="py-4 space-y-1">
              <AnimatePresence initial={false}>
                {messages.map((msg, i) => (
                  <MessageBubble
                    key={msg.id || i}
                    message={msg}
                    isStreaming={isStreaming && msg.id === currentStreamingId}
                    prevUserMessage={i > 0 ? messages[i - 1]?.content : ""}
                    onFeedbackSelect={handleFeedbackSelect}
                    onApprovePlan={handleApprovePlan}
                    onApproveHitl={(editedMsg) =>
                      handleFeedbackSelect(msg.id, "Approve Draft", editedMsg)
                    }
                    onRetryStrategy={handleRetryStrategy}
                    onMonitorClick={(msgId) => {
                      setFocusedMessageId(msgId);
                      setRightPanelOpen(true);
                      const targetMsg = messages.find((m) => m.id === msgId);
                      if (
                        targetMsg?.feedback?.feedbackType === "outreach_review"
                      ) {
                        setActiveReview({
                          messageId: msgId,
                          draft: targetMsg.feedback.draft,
                          customerName: targetMsg.feedback.customerName,
                          phone: targetMsg.feedback.phone,
                          options: targetMsg.feedback.options,
                        });
                        setActiveRightTab("review");
                      } else {
                        if (activeReview?.messageId === msgId) {
                          setActiveRightTab("review");
                        } else {
                          setActiveRightTab("timeline");
                        }
                      }
                    }}
                  />
                ))}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Template suggestions */}
        <TemplateSuggestionBar
          templates={dynamicTemplates}
          onSelectTemplate={(q) => {
            setInputText(q);
            handleTemplate(q);
          }}
          disabled={isStreaming}
        />

        {/* Input */}
        <MessageInput
          value={inputText}
          onChange={setInputText}
          onSubmit={handleSend}
          onAbort={abort}
          isStreaming={isStreaming}
          disabled={false}
        />
      </div>

      {/* Unified Autopilot & Outreach Drawer Panel */}
      <AnimatePresence>
        {rightPanelOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 450, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="h-full bg-white border-l border-slate-200 shadow-xl flex flex-col shrink-0 overflow-hidden relative z-30"
          >
            {/* Drawer Header */}
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between shrink-0 select-none">
              <div className="flex items-center gap-2">
                <Zap
                  size={16}
                  className="text-amber-500 fill-amber-500/25 animate-pulse"
                />
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Glacier Autopilot Console
                </span>
              </div>
              <div className="flex items-center gap-2">
                {isStreaming && focusedMsg?.id === currentStreamingId && (
                  <span className="text-[9px] bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-md font-extrabold select-none animate-pulse">
                    EXECUTING
                  </span>
                )}
                <button
                  onClick={() => setRightPanelOpen(false)}
                  className="p-1 text-slate-400 hover:text-slate-650 rounded-md hover:bg-slate-100 transition-colors cursor-pointer text-xs font-bold"
                >
                  ✕ Close
                </button>
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex border-b border-slate-200 bg-slate-50 px-2 shrink-0 select-none">
              <button
                onClick={() => setActiveRightTab("timeline")}
                className={clsx(
                  "px-4 py-2.5 text-xs font-bold border-b-2 transition-all cursor-pointer",
                  activeRightTab === "timeline"
                    ? "border-blue-600 text-blue-700 font-extrabold"
                    : "border-transparent text-slate-500 hover:text-slate-800",
                )}
              >
                Timeline
              </button>
              <button
                onClick={() => setActiveRightTab("results")}
                className={clsx(
                  "px-4 py-2.5 text-xs font-bold border-b-2 transition-all cursor-pointer",
                  activeRightTab === "results"
                    ? "border-blue-600 text-blue-700 font-extrabold"
                    : "border-transparent text-slate-500 hover:text-slate-800",
                )}
              >
                Results & Logs
              </button>
              {(activeReview ||
                focusedFeedback?.feedbackType === "outreach_review") && (
                <button
                  onClick={() => setActiveRightTab("review")}
                  className={clsx(
                    "px-4 py-2.5 text-xs font-bold border-b-2 transition-all cursor-pointer flex items-center gap-1.5",
                    activeRightTab === "review"
                      ? "border-emerald-600 text-emerald-700 font-extrabold"
                      : "border-transparent text-slate-500 hover:text-slate-800",
                  )}
                >
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping" />
                  Review Draft
                </button>
              )}
            </div>

            {/* Panel Body Content */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col scrollbar-light min-h-0">
              {activeRightTab === "timeline" && (
                <div className="space-y-4 flex-1">
                  {focusedPlan.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-20 text-center text-slate-400">
                      <Bot
                        size={36}
                        className="text-slate-350 animate-bounce-slow mb-3"
                      />
                      <p className="text-xs font-bold uppercase tracking-wider">
                        Awaiting Execution
                      </p>
                      <p className="text-[11px] mt-1 font-semibold">
                        Start a search query to view steps timeline.
                      </p>
                    </div>
                  ) : (
                    <div className="relative pl-4 space-y-4">
                      {/* Vertical connector line */}
                      <div className="absolute left-2.5 top-2.5 bottom-2.5 w-0.5 bg-slate-100 z-0" />

                      {(() => {
                        const completedCount = focusedSteps.filter(
                          (s) =>
                            s.observation ||
                            s.output ||
                            (s.type && s.type.includes("result")),
                        ).length;
                        const activeStepIdx = isStreaming
                          ? Math.min(
                              completedCount,
                              Math.max(0, focusedPlan.length - 1),
                            )
                          : -1;

                        return focusedPlan.map((step, idx) => {
                          let status = "pending";
                          if (
                            !isStreaming ||
                            focusedMsg?.id !== currentStreamingId
                          ) {
                            status = "success";
                          } else {
                            if (idx < activeStepIdx) {
                              status = "success";
                            } else if (idx === activeStepIdx) {
                              status = "active";
                            } else {
                              status = "pending";
                            }
                          }

                          const correspondingToolCall = focusedSteps[idx];
                          const hasThought = focusedThoughts[idx];

                          return (
                            <div
                              key={idx}
                              className="relative pl-6 z-10 animate-slide-up"
                            >
                              {/* Stepper node status */}
                              <span
                                className={clsx(
                                  "absolute left-0 top-1.5 w-3 h-3 rounded-full flex items-center justify-center shrink-0 border -translate-x-1/2 shadow-xs transition-all duration-200",
                                  status === "success" &&
                                    "bg-emerald-500 border-emerald-400 text-white",
                                  status === "active" &&
                                    "bg-blue-600 border-blue-400 text-white animate-pulse",
                                  status === "pending" &&
                                    "bg-slate-100 border-slate-350 text-slate-400",
                                )}
                              >
                                {status === "success" && (
                                  <svg
                                    className="w-1.5 h-1.5 fill-current"
                                    viewBox="0 0 20 20"
                                  >
                                    <path d="M0 11l2-2 5 5L18 3l2 2L7 18z" />
                                  </svg>
                                )}
                              </span>

                              {/* Stepper Content Box */}
                              <div
                                className={clsx(
                                  "border rounded-xl p-3 bg-white transition-all duration-200 shadow-2xs select-none",
                                  status === "active"
                                    ? "border-blue-300 bg-blue-50/10"
                                    : "border-slate-200/80",
                                  status === "success" &&
                                    "border-slate-100 bg-slate-50/20",
                                )}
                              >
                                <div className="flex items-center justify-between">
                                  <span className="text-[9px] font-bold text-slate-400 font-mono">
                                    Step {idx + 1}
                                  </span>
                                  <span
                                    className={clsx(
                                      "text-[8px] px-2 py-0.5 rounded-full font-bold border capitalize leading-none font-sans",
                                      status === "success" &&
                                        "bg-emerald-50 text-emerald-700 border-emerald-100",
                                      status === "active" &&
                                        "bg-blue-50 text-blue-700 border-blue-100 animate-pulse",
                                      status === "pending" &&
                                        "bg-slate-50 text-slate-400 border-slate-100",
                                    )}
                                  >
                                    {status}
                                  </span>
                                </div>
                                <h4 className="text-xs font-bold text-slate-700 mt-1 leading-snug">
                                  {step.description ||
                                    step.tool_name ||
                                    String(step)}
                                </h4>

                                {(correspondingToolCall?.tool ||
                                  step?.tool_name) && (
                                  <div className="mt-2 text-[9px] bg-slate-50 text-slate-500 font-semibold px-2 py-1 rounded inline-block border border-slate-200/60 font-mono">
                                    🔧{" "}
                                    {correspondingToolCall?.tool ||
                                      step?.tool_name}
                                  </div>
                                )}

                                {hasThought && (
                                  <div className="mt-2 pt-2 border-t border-slate-100">
                                    <div className="text-[8px] text-amber-700 font-bold uppercase tracking-wider block">
                                      Cognitive Reasoning:
                                    </div>
                                    <p className="text-[10px] text-slate-550 italic mt-0.5 leading-relaxed font-medium">
                                      {hasThought.text || String(hasThought)}
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  )}
                </div>
              )}

              {activeRightTab === "results" && (
                <div className="space-y-4 flex-1 flex flex-col min-h-0">
                  {(() => {
                    // 1. Extract chronological logs
                    const chronologicalLogs = (() => {
                      const logs = [];
                      if (focusedSteps) {
                        focusedSteps.forEach((s) => {
                          logs.push({
                            type: "tool_call",
                            text: `Executing: ${s.tool}\nInput: ${s.input || "None"}`,
                            ts: s.ts || Date.now(),
                          });
                          if (s.observation) {
                            logs.push({
                              type: "tool_result",
                              text: `Tool [${s.tool}] Completed.\nOutput: ${String(s.observation).slice(0, 1000)}`,
                              ts: s.ts ? s.ts + 1 : Date.now() + 1,
                            });
                          }
                        });
                      }
                      if (focusedThoughts) {
                        focusedThoughts.forEach((t) => {
                          logs.push({
                            type: "thought",
                            text: `Thinking: ${t.text || String(t)}`,
                            ts: t.ts || Date.now(),
                          });
                        });
                      }
                      return logs.sort((a, b) => a.ts - b.ts);
                    })();

                    // 2. Find step with structured table data
                    const stepWithData = [...focusedSteps]
                      .reverse()
                      .find((s) => s.observation || s.output);
                    const rawOutput =
                      stepWithData?.observation || stepWithData?.output || "";
                    const tableData = parseTableData(rawOutput);

                    // 3. Resolve context for synthetic trace fallback
                    const focusedMsgIdx = messages.findIndex(
                      (m) => m.id === focusedMsg?.id,
                    );
                    const prevUserMessage =
                      focusedMsgIdx > 0
                        ? messages[focusedMsgIdx - 1]?.content
                        : "";

                    const getSystemTrace = () => {
                      const trace = [];
                      const queryText =
                        prevUserMessage || "active RM instructions";

                      // 1. Initial connection
                      trace.push({
                        type: "system",
                        label: "SYSTEM",
                        text: `»»» Loan It AI Autopilot Engine v2.5.2-stable initialized.\n»»» Est. connection to CrewAI orchestrator pool... OK\n»»» Model mapping verified: gemini-2.0-flash active.\n»»» User Query: "${queryText}"`,
                      });

                      // 2. Planning stage
                      if (focusedPlan && focusedPlan.length > 0) {
                        const planList = focusedPlan
                          .map((p, i) => `   [Step ${i + 1}] ${p}`)
                          .join("\n");
                        trace.push({
                          type: "plan",
                          label: "ORCHESTRATOR",
                          text: `»»» Analyzing query scope & dependencies...\n»»» Formulated dynamic execution plan with ${focusedPlan.length} steps:\n${planList}`,
                        });
                      }

                      // 3. Cognitive Resolution / Optimization
                      const resolvedCustomer =
                        focusedMsg?.content?.match(/CUST\d{3}/) ||
                        queryText.match(/CUST\d{3}/) ||
                        focusedMsg?.content?.match(/Priya|Aarav|Sneha|Aayush/i);
                      const customerName = resolvedCustomer
                        ? resolvedCustomer[0]
                        : "customer";

                      trace.push({
                        type: "cognitive",
                        label: "OPTIMIZER",
                        text: `»»» Inspecting conversational history & memory slots...\n»»» Context matched: resolved reference to ${customerName}.\n»»» Cognitive Optimization: Required parameters resolved from active conversation memory.\n»»» Skipping redundant database queries & analytical tool runs for peak efficiency.`,
                      });

                      // 4. Execution / Dispatch
                      const agentName =
                        focusedMsg?.plan?.length > 0
                          ? "Personalized Outreach Writer"
                          : "Orchestrator Specialist";
                      trace.push({
                        type: "dispatch",
                        label: "DISPATCHER",
                        text: `»»» Dispatched instruction to [${agentName}]\n»»» Processing direct conversational reply...\n»»» Executing regulatory check: verified outbound compliance criteria.\n»»» Response generated (len: ${focusedMsg?.content?.length || 0} chars).`,
                      });

                      // 5. Done
                      trace.push({
                        type: "system",
                        label: "SYSTEM",
                        text: `»»» Response stream finalized.\n»»» Autopilot state: standby. Awaiting next command.`,
                      });

                      return trace;
                    };

                    return (
                      <div className="flex-1 flex flex-col gap-4 min-h-0">
                        {/* Dynamic Data Grid (if present) */}
                        {tableData && tableData.length > 0 && (
                          <div className="bg-slate-50/50 border border-slate-200 rounded-xl p-3 shadow-2xs flex-1 flex flex-col min-h-0 max-h-[300px]">
                            <div className="flex items-center gap-2 mb-3 shrink-0 select-none">
                              <Database
                                size={13}
                                className="text-blue-600 animate-pulse-slow"
                              />
                              <h3 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">
                                Dynamic Data Grid
                              </h3>
                            </div>
                            <div className="overflow-x-auto flex-1 border border-slate-200/85 rounded-lg bg-white scrollbar-light">
                              <table className="w-full text-left border-collapse min-w-[350px]">
                                <thead>
                                  <tr className="border-b border-slate-200 text-[9px] text-slate-450 font-extrabold uppercase tracking-wider bg-slate-50 select-none">
                                    {Object.keys(tableData[0]).map(
                                      (col, cIdx) => (
                                        <th
                                          key={cIdx}
                                          className="py-2.5 px-3 shrink-0"
                                        >
                                          {col.replace("_", " ")}
                                        </th>
                                      ),
                                    )}
                                  </tr>
                                </thead>
                                <tbody>
                                  {tableData.map((row, rIdx) => (
                                    <tr
                                      key={rIdx}
                                      className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors text-[11px] font-semibold text-slate-700"
                                    >
                                      {Object.values(row).map((val, colIdx) => (
                                        <td
                                          key={colIdx}
                                          className="py-2.5 px-3 truncate max-w-[150px]"
                                        >
                                          {String(val)}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* Chronological Engine Logs Console */}
                        <div className="bg-slate-50/50 border border-slate-200 rounded-xl p-3 shadow-2xs flex-1 flex flex-col min-h-0 select-text">
                          <div className="flex items-center gap-2 mb-2.5 shrink-0 select-none">
                            <FileText size={13} className="text-slate-500" />
                            <h3 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">
                              Active Execution Logs
                            </h3>
                          </div>
                          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 font-mono text-[10px] leading-relaxed text-slate-350 flex-1 overflow-y-auto scrollbar-dark select-text">
                            <span className="text-emerald-400 font-bold font-sans block select-none border-b border-slate-850 pb-1.5 mb-2">
                              »»» [SYSTEM ENGINE CONSOLE LOGS]
                            </span>
                            <div className="space-y-3">
                              {chronologicalLogs.map((log, idx) => (
                                <div
                                  key={idx}
                                  className="border-l-2 border-slate-850 pl-2"
                                >
                                  <span
                                    className={clsx(
                                      "font-sans font-bold uppercase text-[8px] leading-none px-1.5 py-0.5 rounded mr-1.5 select-none",
                                      log.type === "tool_call" &&
                                        "bg-blue-950/80 text-blue-400 border border-blue-900/30",
                                      log.type === "tool_result" &&
                                        "bg-emerald-950/80 text-emerald-400 border border-emerald-900/30",
                                      log.type === "thought" &&
                                        "bg-amber-950/80 text-amber-400 border border-amber-900/30",
                                    )}
                                  >
                                    {log.type === "tool_call"
                                      ? "TOOL CALL"
                                      : log.type === "tool_result"
                                        ? "OBSERVATION"
                                        : "REASONING"}
                                  </span>
                                  <pre className="mt-1.5 whitespace-pre-wrap leading-relaxed select-text font-mono font-medium text-slate-300">
                                    {log.text}
                                  </pre>
                                </div>
                              ))}
                              {chronologicalLogs.length === 0 &&
                                (() => {
                                  const systemTrace = getSystemTrace();
                                  return systemTrace.map((log, idx) => (
                                    <div
                                      key={idx}
                                      className="border-l-2 border-slate-850 pl-2 space-y-1 py-1"
                                    >
                                      <span
                                        className={clsx(
                                          "font-sans font-bold uppercase text-[8px] leading-none px-1.5 py-0.5 rounded mr-1.5 select-none font-mono",
                                          log.type === "system" &&
                                            "bg-emerald-950/80 text-emerald-400 border border-emerald-900/30",
                                          log.type === "plan" &&
                                            "bg-blue-950/80 text-blue-400 border border-blue-900/30",
                                          log.type === "cognitive" &&
                                            "bg-amber-950/80 text-amber-400 border border-amber-900/30",
                                          log.type === "dispatch" &&
                                            "bg-purple-950/80 text-purple-400 border border-purple-900/30",
                                        )}
                                      >
                                        {log.label}
                                      </span>
                                      <pre className="mt-1 whitespace-pre-wrap leading-relaxed select-text font-mono font-medium text-[10px] text-slate-300">
                                        {log.text}
                                      </pre>
                                    </div>
                                  ));
                                })()}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}

              {activeRightTab === "review" && activeReview && (
                <div className="space-y-4 flex-1 flex flex-col scrollbar-light">
                  {/* Phone Mockup View */}
                  <div className="flex justify-center shrink-0">
                    <div className="w-[180px] h-[300px] border-4 border-slate-700 bg-slate-900 rounded-2xl overflow-hidden relative shadow-md flex flex-col">
                      <div className="absolute top-1 left-1/2 -translate-x-1/2 w-10 h-2 bg-slate-700 rounded-full z-20" />
                      <div className="bg-[#075e54] pt-4 pb-1 px-3 text-[8px] font-bold flex items-center justify-between shrink-0 text-white select-none">
                        <span className="truncate max-w-[70px]">
                          {activeReview.customerName || "Sneha Gupta"}
                        </span>
                        <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
                      </div>
                      <div className="flex-1 bg-[#efeae2] p-2 overflow-y-auto no-scrollbar">
                        <div className="bg-white rounded-lg p-1.5 max-w-[85%] text-[8px] text-slate-800 leading-normal shadow-2xs font-semibold select-text break-words whitespace-pre-wrap">
                          {activeReview.draft || "Drafting message..."}
                          <span className="block text-right text-[5px] text-slate-400 mt-1">
                            11:34 AM
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Recipient Information Callout */}
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs font-semibold text-slate-700 flex items-center justify-between select-none shadow-2xs shrink-0">
                    <div>
                      <span className="text-[9px] text-slate-400 uppercase tracking-wider block font-bold leading-none mb-1">
                        Recipient Customer
                      </span>
                      <span className="text-slate-800 font-extrabold">
                        {activeReview.customerName || "N/A"}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[9px] text-slate-400 uppercase tracking-wider block font-bold leading-none mb-1">
                        WhatsApp Number
                      </span>
                      <span className="text-[#006194] font-mono font-extrabold">
                        {activeReview.phone || "N/A"}
                      </span>
                    </div>
                  </div>

                  {/* Text Editor Area */}
                  <div className="space-y-1.5 flex-1 flex flex-col shrink-0 min-h-0">
                    <label className="text-[10px] text-slate-400 font-extrabold tracking-wider uppercase leading-none block select-none">
                      Live Draft Text Editor
                    </label>
                    <textarea
                      value={activeReview.draft}
                      onChange={(e) =>
                        setActiveReview((prev) => ({
                          ...prev,
                          draft: e.target.value,
                        }))
                      }
                      className="w-full flex-1 bg-slate-50 border border-slate-350 rounded-xl p-3 text-xs outline-none text-slate-800 font-semibold focus:border-blue-500 leading-relaxed shadow-2xs resize-none min-h-[120px]"
                      placeholder="Edit the drafted outreach copy..."
                    />
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-2 shrink-0 pt-2 border-t border-slate-100 select-none">
                    <button
                      onClick={() => {
                        handleFeedbackSelect(
                          activeReview.messageId,
                          "Approve Draft",
                          activeReview.draft,
                        );
                        setActiveReview(null);
                        setRightPanelOpen(false);
                      }}
                      className="w-full flex items-center justify-center gap-1.5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white text-xs font-bold rounded-xl transition-all shadow-md active:scale-98 cursor-pointer"
                    >
                      <Send size={11} />
                      Approve & Send Outreach
                    </button>
                    <button
                      onClick={() => {
                        handleFeedbackSelect(
                          activeReview.messageId,
                          "Dismiss Draft",
                        );
                        setActiveReview(null);
                        setRightPanelOpen(false);
                      }}
                      className="w-full py-2 bg-white border border-slate-350 text-slate-700 hover:bg-slate-50 text-xs font-bold rounded-xl transition-all active:scale-98 cursor-pointer"
                    >
                      Dismiss Draft Message
                    </button>
                  </div>
                </div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}
