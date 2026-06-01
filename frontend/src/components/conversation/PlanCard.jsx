import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Zap,
  Play,
  AlertTriangle,
  Send,
  Smartphone
} from 'lucide-react'
import clsx from 'clsx'

export default function PlanCard({
  plan,
  steps = [],
  thoughts = [],
  feedback = null,
  isStreaming = false,
  onApprovePlan,
  onApproveHitl,
  messageId
}) {
  const [expandedRationale, setExpandedRationale] = useState({})
  const [expandedThoughts, setExpandedThoughts] = useState({})
  const [hitlMessage, setHitlMessage] = useState('')

  if (!plan || !plan.steps || plan.steps.length === 0) return null

  const planId = plan.plan_id
  const requiresApproval = plan.requires_approval
  const isApproved = plan.status && plan.status !== 'planning' && plan.status !== 'pending'
  const isCompleted = plan.status === 'completed'

  const toggleRationale = (num) => {
    setExpandedRationale(prev => ({ ...prev, [num]: !prev[num] }))
  }

  const toggleThoughts = (num) => {
    setExpandedThoughts(prev => ({ ...prev, [num]: !prev[num] }))
  }

  // Group steps and thoughts by step number
  const getStepStatus = (stepNum, stepObj) => {
    // If steps array has matching step_number
    const match = steps.find(s => s.step_number === stepNum || s.step === stepNum)
    if (match) {
      return match.status || (match.observation || match.output ? 'success' : 'running')
    }
    return stepObj.status || 'pending'
  }

  const getStepResult = (stepNum) => {
    const match = steps.find(s => s.step_number === stepNum || s.step === stepNum)
    return match?.observation || match?.output || match?.tool_result || null
  }

  const getStepThoughts = (stepNum) => {
    return thoughts.filter(t => t.step_number === stepNum || t.step === stepNum)
  }

  const getStepRetry = (stepNum) => {
    const match = steps.find(s => s.step_number === stepNum || s.step === stepNum)
    return match?.retry_count || 0
  }

  const getStepMaxRetry = (stepNum) => {
    const match = steps.find(s => s.step_number === stepNum || s.step === stepNum)
    return match?.max_retries || 3
  }

  return (
    <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-sm my-3 select-none max-w-xl animate-fade-in">
      <div className="flex items-center gap-2.5 mb-4 border-b border-slate-100 pb-3">
        <div className="w-6 h-6 rounded-lg bg-indigo-50 flex items-center justify-center">
          <Zap size={13} className="text-indigo-650 fill-indigo-650/15" />
        </div>
        <div>
          <h3 className="text-xs font-black text-slate-800 uppercase tracking-wider">Agentic Execution Plan</h3>
          <p className="text-[10px] text-slate-400 font-bold mt-0.5">Sequential CoT ReAct Executor Loop</p>
        </div>
        <span className={clsx(
          "text-[8px] px-2 py-0.5 rounded-full font-bold ml-auto border tracking-wide uppercase",
          isCompleted && "bg-emerald-50 text-emerald-700 border-emerald-100",
          plan.status === 'paused_hitl' && "bg-amber-50 text-amber-700 border-amber-100 animate-pulse",
          (plan.status === 'running' || isStreaming && isApproved) && "bg-blue-50 text-blue-700 border-blue-100 animate-pulse",
          (plan.status === 'planning' || plan.status === 'pending') && "bg-slate-50 text-slate-400 border-slate-100"
        )}>
          {plan.status || 'running'}
        </span>
      </div>

      {/* Rationale header if provided */}
      {plan.rationale && (
        <p className="text-xs font-semibold text-slate-600 bg-slate-50 border border-slate-200/50 p-2.5 rounded-xl mb-4 leading-relaxed italic">
          💡 "{plan.rationale}"
        </p>
      )}

      {/* Plan Steps Stepper */}
      <div className="relative space-y-3.5 mb-4">
        {/* Timeline connector bar */}
        <div className="absolute left-3.5 top-2.5 bottom-2.5 w-0.5 bg-slate-100 z-0" />

        {plan.steps.map((step, idx) => {
          const stepObj = typeof step === 'string' ? { description: step } : step
          const stepNum = stepObj.step_number || (idx + 1)
          const stepStatus = getStepStatus(stepNum, stepObj)
          const isCurrent = stepStatus === 'running' || stepStatus === 'active'
          const isDone = stepStatus === 'success'
          const isFailed = stepStatus === 'failed'
          const retryCount = getStepRetry(stepNum)
          const maxRetry = getStepMaxRetry(stepNum)
          const stepThoughts = getStepThoughts(stepNum)
          const stepResult = getStepResult(stepNum)

          const rationalExpanded = expandedRationale[stepNum]
          const thoughtsExpanded = expandedThoughts[stepNum]

          const executionMatch = steps.find(s => s.step_number === stepNum || s.step === stepNum)
          const resolvedToolName = stepObj.tool_name || executionMatch?.tool || executionMatch?.tool_name || null

          return (
            <div key={stepObj.step_id || idx} className="relative pl-7 z-10 animate-slide-up">
              {/* timeline bullet point */}
              <span className={clsx(
                "absolute left-0 top-1.5 w-3 h-3 rounded-full flex items-center justify-center shrink-0 border -translate-x-1/2 shadow-2xs transition-all duration-200 z-10",
                isDone && "bg-emerald-500 border-emerald-400 text-white",
                isFailed && "bg-rose-500 border-rose-400 text-white",
                isCurrent && "bg-amber-500 border-amber-400 text-white animate-pulse",
                !isDone && !isFailed && !isCurrent && "bg-slate-50 border-slate-200 text-slate-400"
              )}>
                {isDone && (
                  <svg className="w-1.5 h-1.5 fill-current stroke-[3]" viewBox="0 0 20 20">
                    <path d="M0 11l2-2 5 5L18 3l2 2L7 18z"/>
                  </svg>
                )}
                {isFailed && <span className="text-[6px] font-bold">✗</span>}
                {isCurrent && <span className="w-1 h-1 rounded-full bg-white animate-ping" />}
              </span>

              {/* Step Card Box */}
              <div className={clsx(
                "border rounded-xl p-3 bg-white transition-all duration-200 shadow-2xs",
                isCurrent ? "border-amber-400 bg-amber-50/5" : "border-slate-200/80",
                isDone && "border-slate-100 bg-slate-50/10"
              )}>
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-bold text-slate-400 font-mono">Step {stepNum}</span>
                  <span className={clsx(
                    "text-[8px] px-2 py-0.5 rounded-full font-bold border capitalize leading-none",
                    isDone && "bg-emerald-50 text-emerald-700 border-emerald-100",
                    isFailed && "bg-rose-50 text-rose-700 border-rose-100",
                    isCurrent && "bg-amber-50 text-amber-700 border-amber-100 animate-pulse",
                    !isDone && !isFailed && !isCurrent && "bg-slate-50 text-slate-400 border-slate-100"
                  )}>
                    {stepStatus}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-800 mt-1.5 leading-snug">
                  {stepObj.description}
                </h4>
                
                {resolvedToolName && (
                  <div className="flex items-center gap-1.5 mt-2">
                    <span className="text-[9px] bg-slate-50 text-slate-500 font-semibold px-2 py-0.5 rounded border border-slate-200/60 font-mono">
                      🔧 {resolvedToolName}
                    </span>
                    {stepObj.hitl_required && (
                      <span className="text-[8px] bg-amber-50 text-amber-600 font-bold px-1.5 py-0.5 rounded border border-amber-200/50">
                        ⚡ REQUIRES REVIEW
                      </span>
                    )}
                  </div>
                )}

                {/* Retries count */}
                {retryCount > 0 && !isDone && (
                  <div className="flex items-center gap-1.5 mt-2 text-[9px] text-rose-500 font-bold bg-rose-50/30 px-2 py-1 rounded border border-rose-150">
                    <AlertTriangle size={10} />
                    Retry Attempt #{retryCount} / {maxRetry}
                  </div>
                )}

                {/* Rationale Change of thought accordion */}
                {step.rationale && (
                  <div className="mt-2.5 border-t border-slate-100 pt-2">
                    <button
                      type="button"
                      onClick={() => toggleRationale(stepNum)}
                      className="flex items-center gap-1 text-[9px] text-indigo-650 hover:text-indigo-850 font-bold tracking-wide cursor-pointer"
                    >
                      {rationalExpanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                      Step Rationale
                    </button>
                    <AnimatePresence>
                      {rationalExpanded && (
                        <motion.p
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="text-[10px] text-slate-450 font-semibold leading-relaxed mt-1 overflow-hidden"
                        >
                          {step.rationale}
                        </motion.p>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Step thoughts and substeps (Thoughts / Observations) */}
                {stepThoughts.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => toggleThoughts(stepNum)}
                      className="flex items-center gap-1.5 text-[9px] text-emerald-600 hover:text-emerald-800 font-extrabold tracking-wide cursor-pointer"
                    >
                      {thoughtsExpanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                      🧠 Agent Thoughts ({stepThoughts.length})
                    </button>
                    <AnimatePresence>
                      {thoughtsExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="mt-2 space-y-2 pl-2 border-l border-emerald-100 overflow-hidden"
                        >
                          {stepThoughts.map((evt, eIdx) => (
                            <div key={eIdx} className="text-[10px] leading-relaxed">
                              {evt.type === 'thought' && (
                                <div className="text-slate-450 font-medium italic">
                                  💭 {evt.text}
                                </div>
                              )}
                              {evt.type === 'tool_call' && (
                                <div className="text-indigo-650 font-bold">
                                  🔧 Calling: <span className="underline font-mono">{evt.tool}</span>
                                </div>
                              )}
                              {evt.type === 'tool_result' && (
                                <div className="text-slate-500 text-[9px] bg-slate-50 p-1.5 rounded border border-slate-200 font-mono line-clamp-2 mt-1">
                                  {evt.output}
                                </div>
                              )}
                            </div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Step tool result preview */}
                {isDone && stepResult && !thoughtsExpanded && (
                  <div className="text-[9px] text-slate-400 bg-slate-50/50 p-1.5 rounded border border-slate-100 mt-2 font-mono line-clamp-1">
                    ✓ Observation: {String(stepResult)}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Plan approval banner (stops the stream and awaits user click) */}
      {!isApproved && (
        <motion.div
          initial={{ scale: 0.98, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-indigo-50/70 border border-indigo-150 rounded-xl p-3.5 flex flex-col items-center justify-center text-center gap-3 select-none"
        >
          <div className="text-xs text-indigo-950 font-bold leading-normal">
            🚦 Action Required: Approve Execution Strategy
          </div>
          <div className="flex flex-col sm:flex-row gap-2 w-full">
            <button
              type="button"
              onClick={() => onApprovePlan && onApprovePlan(planId, false)}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-white border border-slate-350 hover:bg-slate-50 text-slate-700 font-extrabold text-xs shadow-2xs transition-all active:scale-97 cursor-pointer"
            >
              <XCircle size={11} className="text-slate-500" />
              Reject & Rethink Strategy
            </button>
            <button
              type="button"
              onClick={() => onApprovePlan && onApprovePlan(planId, true)}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-700 hover:bg-indigo-800 text-white font-extrabold text-xs shadow-sm transition-all active:scale-97 cursor-pointer"
            >
              <Play size={11} className="fill-current" />
              Approve Plan & Launch
            </button>
          </div>
        </motion.div>
      )}

      {/* Inline HITL outreach message customizer block */}
      {plan.status === 'paused_hitl' && feedback && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-amber-50/60 border border-amber-200/80 rounded-xl p-4 mt-3"
        >
          <div className="flex items-center gap-2 mb-3">
            <Smartphone size={14} className="text-amber-600 animate-bounce" />
            <h4 className="text-xs font-black text-slate-800">Review & Personalize Outreach</h4>
          </div>

          <div className="flex flex-col gap-3">
            <textarea
              defaultValue={feedback.draft || hitlMessage}
              onChange={(e) => setHitlMessage(e.target.value)}
              placeholder="Outreach copy pre-drafted. You can make final personalization tweaks here..."
              className="w-full bg-white border border-slate-350 rounded-lg p-2.5 text-xs outline-none text-slate-700 font-semibold h-28 focus:border-amber-500 leading-relaxed resize-none shadow-2xs"
            />
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  const finalCopy = hitlMessage || feedback.draft
                  onApproveHitl && onApproveHitl(finalCopy)
                }}
                className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white text-xs font-bold rounded-lg transition-all shadow-sm active:scale-97 cursor-pointer"
              >
                <Send size={10} />
                Approve copy
              </button>
              <button
                onClick={() => {
                  onApproveHitl && onApproveHitl("Dismiss Message")
                }}
                className="py-2 px-3 bg-white border border-slate-350 text-slate-700 hover:bg-slate-50 text-xs font-bold rounded-lg transition-all active:scale-97 cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
