import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  Wrench,
  AlertCircle,
  Copy,
  Check,
  Sparkles,
  List,
  Play,
  CheckCircle,
  Activity,
  Database,
  Shield,
  Cpu,
  FileText,
  Loader2,
  Zap
} from 'lucide-react'
import ToolExecutionCard from '../agents/ToolExecutionCard'
import clsx from 'clsx'
import PlanCard from './PlanCard'
import InlineDataGrid from './InlineDataGrid'

function getInitials(name = '') {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'RM'
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button
      onClick={handleCopy}
      className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
      title="Copy"
    >
      {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
    </button>
  )
}

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
  if (name.includes("whatsapp") || name.includes("outreach") || name.includes("bulk")) return "Audited Copy Composer";
  return "Agent Action: " + toolName;
}

// Removed static getActionPlan function

function AIFlowPanel({ messageId, steps = [], thoughts = [], plan = [], isStreaming = false, feedback = null, onMonitorClick }) {
  const [expanded, setExpanded] = useState(false);
  
  const safeSteps = Array.isArray(steps) ? steps : [];
  const safeThoughts = Array.isArray(thoughts) ? thoughts : [];
  const safePlan = Array.isArray(plan) ? plan : [];
  
  if (!safeSteps.length && !safeThoughts.length && !safePlan.length && !isStreaming) return null;

  const totalSteps = safePlan.length || 0;
  const completedSteps = safeSteps.filter(s => s.observation || s.output || (s.type && s.type.includes("result"))).length;
  const displayCompleted = isStreaming ? Math.min(completedSteps, Math.max(0, totalSteps - 1)) : totalSteps;

  return (
    <div className="mt-3 bg-slate-50 border border-slate-200/80 rounded-xl overflow-hidden shadow-2xs animate-fade-in">
      {/* Header bar (clickable) */}
      <div 
        onClick={() => setExpanded(!expanded)}
        className="p-3 select-none flex items-center justify-between gap-3 hover:bg-slate-100/50 transition-colors cursor-pointer"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="relative flex items-center justify-center shrink-0">
            {feedback ? (
              <div className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
              </div>
            ) : isStreaming ? (
              <div className="w-5 h-5 rounded-full border-2 border-t-blue-600 border-r-transparent border-b-transparent border-l-transparent animate-spin flex items-center justify-center">
                <Zap size={10} className="text-blue-500 fill-blue-500/15" />
              </div>
            ) : (
              <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
                <CheckCircle size={12} className="text-emerald-600" />
              </div>
            )}
          </div>
          <div className="min-w-0">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider leading-none">
              Autopilot Execution
            </div>
            <p className="text-xs font-semibold text-slate-700 mt-1">
              {feedback
                ? `Paused — Awaiting RM Review (${displayCompleted}/${totalSteps || '?'})`
                : isStreaming 
                  ? `Running steps (${displayCompleted}/${totalSteps || '?'})`
                  : `Completed successfully (${displayCompleted}/${totalSteps || safeSteps.length} steps)`
              }
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onMonitorClick && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onMonitorClick && onMonitorClick(messageId);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-350 hover:bg-slate-50 hover:border-slate-450 active:scale-95 text-[11px] font-bold text-slate-700 rounded-lg transition-all shadow-2xs shrink-0 cursor-pointer"
            >
              <Zap size={11} className="text-amber-500 fill-amber-500/25 animate-pulse" />
              Monitor
            </button>
          )}
          <div className="p-1 rounded text-slate-400 hover:text-slate-655 hover:bg-slate-100 transition-colors">
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </div>
        </div>
      </div>

      {/* Accordion expanded content */}
      {expanded && (
        <div className="border-t border-slate-200 bg-white p-3 space-y-3 animate-slide-down">
          {/* Thoughts Timeline if available */}
          {safeThoughts.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Cognitive Thinking Chain
              </span>
              <div className="bg-amber-50/40 border border-amber-100 rounded-lg p-2.5 space-y-2">
                {safeThoughts.map((thought, idx) => (
                  <div key={idx} className="flex gap-2">
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-100 border border-amber-200 text-amber-800 font-bold uppercase select-none leading-none shrink-0 self-start mt-0.5">
                      THOUGHT
                    </span>
                    <p className="text-xs text-slate-650 italic leading-relaxed font-medium">
                      {thought.text || String(thought)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Steps and Tool Execution List */}
          {safeSteps.length > 0 ? (
            <div className="space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Tool Execution Pipeline
              </span>
              <div className="space-y-2">
                {safeSteps.map((step, idx) => {
                  const event = {
                    tool: step.tool || step.tool_name || 'Generic Tool',
                    input: step.input || step.tool_args || '',
                    output: step.observation || step.output || step.result || '',
                    result: step.observation || step.output || step.result || '',
                    done: !!(step.observation || step.output || step.result),
                    ts: step.ts,
                    type: (step.observation || step.output || step.result) ? 'tool_result' : 'tool_call'
                  };
                  return (
                    <ToolExecutionCard key={idx} event={event} />
                  );
                })}
              </div>
            </div>
          ) : (
            isStreaming && (
              <div className="flex items-center gap-2 py-3 text-xs text-slate-500 italic select-none">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-500" />
                Preparing analytical framework...
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}

function StreamingCursor() {
  return <span className="inline-block w-0.5 h-4 bg-blue-500 animate-blink ml-0.5 align-middle" />
}

function UserBubble({ message }) {
  return (
    <div className="flex justify-end gap-3 px-4 py-2 animate-fade-in">
      <div className="max-w-xl">
        <div className="bg-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed shadow-sm">
          {message.content}
        </div>
        {message.timestamp && (
          <div className="text-right mt-1">
            <span className="text-xs text-slate-400">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        )}
      </div>
      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
        <User size={15} className="text-blue-600" />
      </div>
    </div>
  )
}

function AssistantBubble({ message, isStreaming = false, prevUserMessage = "", onFeedbackSelect, onMonitorClick, onApprovePlan, onApproveHitl, onRetryStrategy }) {
  const content = message.content || ''
  const steps = message.steps || []
  const status = message.status

  return (
    <div className="flex justify-start gap-3 px-4 py-2 animate-fade-in">
      {/* Bot avatar */}
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
        <Bot size={15} className="text-white" />
      </div>

      <div className="max-w-2xl min-w-0 flex-1">
        {message.plan && (
          <PlanCard
            plan={message.plan}
            steps={steps}
            thoughts={message.thoughts || []}
            feedback={message.feedback}
            isStreaming={isStreaming}
            onApprovePlan={onApprovePlan}
            onApproveHitl={onApproveHitl}
            messageId={message.id}
          />
        )}

        {message.data_grid && (
          <InlineDataGrid data={message.data_grid} />
        )}

        {/* Status indicator */}
        {status && !content && !message.feedback && (
          <div className="flex items-center gap-2 mb-2">
            <div className="flex gap-0.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
            <span className="text-xs text-slate-500 italic">{status}</span>
          </div>
        )}

        {/* Error state */}
        {message.error && (
          <div className="flex flex-col gap-2.5 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm animate-fade-in shadow-2xs">
            <div className="flex items-center gap-2">
              <AlertCircle size={15} className="shrink-0" />
              <span className="font-semibold">{message.error}</span>
            </div>
            
            {message.plan && (
              <button
                type="button"
                onClick={() => onRetryStrategy && onRetryStrategy(message.plan.plan_id || message.plan.planId)}
                className="w-fit flex items-center gap-1.5 px-3 py-1.5 bg-red-700 hover:bg-red-800 text-white font-extrabold text-[11px] rounded-lg transition-all shadow-xs active:scale-97 cursor-pointer"
              >
                <Zap size={11} className="fill-current animate-pulse text-amber-300" />
                Retry Failed Strategy Execution
              </button>
            )}
          </div>
        )}

        {/* Content */}
        {content && (() => {
          const cleanContent = content
            .replace(/\\n/g, '\n')
            .replace(/\\r/g, '\r')
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/\|\|---/g, '|---')
            .replace(/\|\s*\|\s*/g, '|\n| ');

          return (
            <div className="group relative">
              <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <div className={clsx(
                  'prose prose-sm max-w-none text-slate-800',
                  'prose-headings:text-slate-900 prose-headings:font-semibold',
                  'prose-code:text-blue-700 prose-code:bg-blue-50 prose-code:px-1 prose-code:rounded',
                  'prose-pre:bg-slate-900 prose-pre:text-slate-100',
                  'prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline',
                  'prose-strong:text-slate-900',
                  'prose-li:text-slate-700',
                )}>
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-3 rounded-xl border border-slate-200 shadow-2xs bg-white">
                          <table className="min-w-full divide-y divide-slate-200" {...props} />
                        </div>
                      ),
                      thead: ({ node, ...props }) => <thead className="bg-slate-50/70 border-b border-slate-200" {...props} />,
                      tbody: ({ node, ...props }) => <tbody className="divide-y divide-slate-100 bg-white" {...props} />,
                      tr: ({ node, ...props }) => <tr className="hover:bg-slate-50/40 transition-colors duration-150" {...props} />,
                      th: ({ node, ...props }) => (
                        <th className="px-3.5 py-2.5 text-left text-xs font-bold text-slate-700 uppercase tracking-wider font-sans" {...props} />
                      ),
                      td: ({ node, ...props }) => (
                        <td className="px-3.5 py-2 text-xs text-slate-650 font-medium whitespace-normal break-words font-sans" {...props} />
                      ),
                      a: ({ node, ...props }) => (
                        <a className="text-blue-600 hover:text-blue-700 underline font-semibold transition-colors duration-150" {...props} />
                      ),
                      ul: ({ node, ...props }) => <ul className="list-disc pl-5 my-2 space-y-1" {...props} />,
                      ol: ({ node, ...props }) => <ol className="list-decimal pl-5 my-2 space-y-1" {...props} />,
                      li: ({ node, ...props }) => <li className="text-xs text-slate-700 leading-relaxed font-medium" {...props} />,
                    }}
                  >
                    {cleanContent}
                  </ReactMarkdown>
                  {isStreaming && <StreamingCursor />}
                </div>
              </div>
              {/* Copy button */}
              {!isStreaming && (
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <CopyButton text={cleanContent} />
                </div>
              )}
            </div>
          );
        })()}

        {/* Empty streaming state */}
        {isStreaming && !content && !status && (
          <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-2 h-2 rounded-full bg-slate-300 animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
              <span className="text-xs text-slate-400">Thinking…</span>
            </div>
          </div>
        )}

        {/* Human Feedback Request Card */}
        {message.feedback && (
          <div className={clsx(
            "mt-3 rounded-2xl p-4 shadow-sm animate-fade-in select-none",
            message.feedback.feedbackType === "outreach_review"
              ? "bg-emerald-50/70 border border-emerald-200/80 text-emerald-950"
              : "bg-blue-50/70 border border-blue-200/80 text-blue-900"
          )}>
            <div className="flex items-start gap-2.5">
              <AlertCircle className={clsx(
                "shrink-0 mt-0.5",
                message.feedback.feedbackType === "outreach_review" ? "text-emerald-600" : "text-blue-600"
              )} size={16} />
              <div className="space-y-3 w-full">
                <span className={clsx(
                  "text-xs font-bold uppercase tracking-wider block",
                  message.feedback.feedbackType === "outreach_review" ? "text-emerald-900" : "text-blue-900"
                )}>
                  {message.feedback.feedbackType === "outreach_review" 
                    ? "Action Required: Review Outreach Message" 
                    : "Action Required: Human Confirmation"}
                </span>
                <p className="text-sm text-slate-800 font-medium leading-relaxed">
                  {message.feedback.message}
                </p>
                {message.feedback.feedbackType === "outreach_review" ? (
                  <div className="bg-white border border-emerald-200/40 rounded-xl p-3 text-xs font-semibold text-slate-650 flex items-center gap-2 select-none shadow-xs">
                    <Sparkles className="text-amber-500 shrink-0" size={13} />
                    Personalized outreach copy drafted. Please review, edit, and approve it in the dedicated **Outreach Composer** panel on the right.
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {message.feedback.options?.map((opt, idx) => {
                      const isCancel = opt.toLowerCase().includes("cancel") || opt.toLowerCase().includes("dismiss") || opt.toLowerCase().includes("no");
                      return (
                        <button
                          key={idx}
                          onClick={() => onFeedbackSelect && onFeedbackSelect(message.id, opt)}
                          className={clsx(
                            "px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 shadow-xs flex items-center gap-1.5 cursor-pointer",
                            isCancel 
                              ? "bg-white border border-slate-350 text-slate-700 hover:bg-slate-50 hover:border-slate-450"
                              : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md hover:shadow-blue-100"
                          )}
                        >
                          {isCancel ? null : <CheckCircle size={13} />}
                          {opt}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Resolved Feedback Indicator */}
        {message.feedbackSelected && (
          <div className="mt-3 bg-emerald-50/50 border border-emerald-200/60 rounded-2xl p-3 shadow-2xs flex items-center justify-between text-xs font-semibold text-emerald-800 animate-fade-in select-none">
            <div className="flex items-center gap-2">
              <CheckCircle size={14} className="text-emerald-500" />
              <span>Confirmed: {message.feedbackSelected}</span>
            </div>
            <span className="text-[10px] uppercase font-bold text-emerald-600 bg-white border border-emerald-250/50 px-1.5 py-0.5 rounded-md">
              Resolved
            </span>
          </div>
        )}

        {/* AI Flow Panel (Plan, Executor Tool, Data) */}
        <AIFlowPanel
          messageId={message.id}
          steps={steps}
          thoughts={message.thoughts || []}
          plan={message.plan || []}
          isStreaming={isStreaming}
          feedback={message.feedback}
          onMonitorClick={onMonitorClick}
        />

        {/* Timestamp */}
        {message.timestamp && !isStreaming && (
          <div className="mt-1">
            <span className="text-xs text-slate-400">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default function MessageBubble({ message, isStreaming = false, prevUserMessage = "", onFeedbackSelect, onMonitorClick, onApprovePlan, onApproveHitl, onRetryStrategy }) {
  if (message.role === 'user') {
    return <UserBubble message={message} />
  }
  return (
    <AssistantBubble 
      message={message} 
      isStreaming={isStreaming} 
      prevUserMessage={prevUserMessage} 
      onFeedbackSelect={onFeedbackSelect}
      onMonitorClick={onMonitorClick}
      onApprovePlan={onApprovePlan}
      onApproveHitl={onApproveHitl}
      onRetryStrategy={onRetryStrategy}
    />
  )
}
