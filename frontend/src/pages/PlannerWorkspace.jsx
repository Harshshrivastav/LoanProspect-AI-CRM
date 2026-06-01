import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Zap,
  Play,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Loader2,
  Send,
  Sparkles,
  Smartphone,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  Database,
  Search,
  MessageSquare
} from 'lucide-react'
import clsx from 'clsx'

export default function PlannerWorkspace() {
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [planApproved, setPlanApproved] = useState(false)
  const [planId, setPlanId] = useState(null)
  const [plan, setPlan] = useState(null)
  
  // Streaming state
  const [sseEvents, setSseEvents] = useState([])
  const [currentStepNum, setCurrentStepNum] = useState(null)
  const [runningLog, setRunningLog] = useState('')
  const [expandedRationale, setExpandedRationale] = useState({})
  
  // Sub-step intermediate agent thought maps
  // Maps stepNumber -> array of {type, tool, text, input, output}
  const [intermediateEvents, setIntermediateEvents] = useState({})
  const [expandedSubsteps, setExpandedSubsteps] = useState({})
  
  // HITL state
  const [hitlStep, setHitlStep] = useState(null)
  const [hitlMessage, setHitlMessage] = useState('')
  
  // Dynamic Grid data
  const [tableData, setTableData] = useState(null)

  const timelineEndRef = useRef(null)

  // Quick Action Templates
  const templates = [
    "Find the top 5 personal loan candidates and draft friendly WhatsApp messages",
    "Identify bottom 10 earners, compute loan readiness, and check compliance blocks",
    "Fetch transactions for CUST015, scan for life events, and generate customized offers"
  ]

  const handleTemplateSelect = (tmpl) => {
    setInputText(tmpl)
  }

  // Helper to fetch full plan details
  const fetchPlanDetails = async (pid) => {
    try {
      const res = await fetch(`/api/chat/planner/plan/${pid}`)
      if (res.ok) {
        const data = await res.json()
        setPlan(data)
        
        // Check if plan has some successful step with tabular/list data to render in grid
        const lastSuccessStep = [...data.steps].reverse().find(s => s.status === 'success' && s.tool_result)
        if (lastSuccessStep) {
          parseAndSetGridData(lastSuccessStep.tool_result)
        }
      }
    } catch (err) {
      console.error("Failed to fetch plan details:", err)
    }
  }

  // Parse step tool output into tables
  const parseAndSetGridData = (rawOutput) => {
    try {
      // If it is JSON
      if (rawOutput.startsWith('{') || rawOutput.startsWith('[')) {
        const parsed = JSON.parse(rawOutput)
        if (Array.isArray(parsed)) {
          setTableData(parsed)
          return
        }
      }
    } catch (e) {}

    // Fallback parser: parse markdown tables or CSV customer lists
    const customerIds = Array.from(new Set(rawOutput.match(/CUST\d{3}/g) || []))
    if (customerIds.length > 0) {
      const rows = customerIds.map(cid => {
        const lines = rawOutput.split('\n')
        let name = "Loan It Client"
        for (let line of lines) {
          if (line.includes(cid)) {
            const clean = line.replace(/[`|*#]/g, '').trim()
            const matchName = clean.match(/([A-Za-z\s]{3,25})/)
            if (matchName) name = matchName[0].trim()
            break
          }
        }
        return {
          customer_id: cid,
          full_name: name,
          kyc_status: "VERIFIED",
          consent: "✅ ACTIVE"
        }
      })
      setTableData(rows)
    } else {
      setTableData(null)
    }
  }

  // Create plan (stops at review stage)
  const handleInitiatePlan = async (e) => {
    if (e) e.preventDefault()
    if (!inputText.trim()) return

    setLoading(true)
    setPlanId(null)
    setPlan(null)
    setSseEvents([])
    setIntermediateEvents({})
    setExpandedSubsteps({})
    setTableData(null)
    setHitlStep(null)
    setExecuting(false)
    setPlanApproved(false)
    setRunningLog('Orchestrator: Formulating sequential strategy plan. Please wait...')

    try {
      const res = await fetch('/api/chat/planner/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputText.trim() })
      })

      if (!res.ok) throw new Error("Plan formulation failed")
      const data = await res.json()
      setPlanId(data.plan_id)
      setPlan(data)
      setLoading(false)
      setRunningLog('📋 Strategy Plan generated! Review details below and click approve to trigger execution.')
    } catch (err) {
      setLoading(false)
      setRunningLog(`Error formulating plan: ${err.message}`)
    }
  }

  // Approved strategy plan, start SSE execution
  const handleApproveAndTrigger = async () => {
    if (!planId) return
    setPlanApproved(true)
    handleStartExecution(planId)
  }

  // Execute loop stream reader
  const handleStartExecution = async (pid) => {
    setExecuting(true)
    setHitlStep(null)
    
    try {
      const response = await fetch(`/api/chat/planner/stream/${pid}`)
      if (!response.body) throw new Error("ReadableStream not supported")
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.substring(6))
              setSseEvents(prev => [...prev, eventData])
              
              if (eventData.type === 'step_start') {
                setCurrentStepNum(eventData.step_number)
                setRunningLog(`Running Step ${eventData.step_number}: ${eventData.tool_name}...`)
                setExpandedRationale(prev => ({ ...prev, [eventData.step_number]: true }))
                setExpandedSubsteps(prev => ({ ...prev, [eventData.step_number]: true }))
              } 
              else if (eventData.type === 'thought' || eventData.type === 'tool_call' || eventData.type === 'tool_result') {
                const sNum = eventData.step_number
                if (sNum) {
                  setIntermediateEvents(prev => {
                    const existing = prev[sNum] || []
                    return { ...prev, [sNum]: [...existing, eventData] }
                  })
                }
              }
              else if (eventData.type === 'step_success') {
                setRunningLog(`Step completed successfully! Resolving parameters.`)
                fetchPlanDetails(pid)
              }
              else if (eventData.type === 'replanned') {
                setRunningLog(`🚨 Retry exhausted! Triggering adaptive re-planner... Timeline updated.`)
                fetchPlanDetails(pid)
              }
              else if (eventData.type === 'paused_hitl') {
                setRunningLog(`⏳ Paused for Relationship Manager review. Messages waiting for approval.`)
                setHitlStep({
                  step_number: eventData.step_number,
                  tool_name: eventData.tool_name
                })
                setHitlMessage(eventData.draft || '')
                fetchPlanDetails(pid)
              }
              else if (eventData.type === 'done') {
                setRunningLog(`✅ Success! Plan fully executed. Final datasets loaded.`)
                setExecuting(false)
                setCurrentStepNum(null)
                fetchPlanDetails(pid)
              }
              else if (eventData.type === 'error') {
                setRunningLog(`❌ Error: ${eventData.error}`)
                setExecuting(false)
                fetchPlanDetails(pid)
              }
            } catch (err) {
              console.error("SSE parse error", err)
            }
          }
        }
      }
    } catch (err) {
      setExecuting(false)
      setRunningLog(`Execution failed: ${err.message}`)
    }
  }

  // Approve HITL message
  const handleApproveHitl = async () => {
    if (!hitlStep || !planId) return

    try {
      const res = await fetch('/api/chat/planner/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_id: planId,
          step_number: hitlStep.step_number,
          message: hitlMessage
        })
      })

      if (res.ok) {
        setHitlStep(null)
        // Resume loop execution
        handleStartExecution(planId)
      }
    } catch (err) {
      console.error("Approval failed:", err)
    }
  }

  const toggleRationale = (num) => {
    setExpandedRationale(prev => ({ ...prev, [num]: !prev[num] }))
  }

  const toggleSubsteps = (num) => {
    setExpandedSubsteps(prev => ({ ...prev, [num]: !prev[num] }))
  }

  return (
    <div className="flex h-full bg-[#0b0f19] text-slate-100 flex-col overflow-hidden font-sans select-none">
      {/* Autopilot Glass Header */}
      <header className="px-6 py-4 bg-[#0d1527]/80 backdrop-blur-md border-b border-[#1e293b]/60 flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-amber-400 via-orange-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-900/20">
            <Zap size={18} className="text-white fill-amber-300 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold text-white tracking-tight font-display">Loan It Autopilot</h1>
              <span className="text-[9px] bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full font-bold border border-amber-500/20">AGENTIC EVENT-LOOP</span>
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5 font-medium">ReAct Change-of-Thought Sequential Executor & Dynamic Re-Planner</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
          <Sparkles size={13} className="text-amber-400" />
          CrewAI Agents + Gemini 2.0
        </div>
      </header>

      {/* Workspace Area */}
      <div className="flex flex-1 overflow-hidden relative w-full">
        {/* Left Input/timeline Column (40% width) */}
        <aside className="w-[440px] bg-[#0d1425]/90 border-r border-[#1e293b]/60 flex flex-col h-full shrink-0 overflow-y-auto no-scrollbar relative z-10">
          {/* Form wrapper */}
          <div className="p-4 border-b border-[#1e293b]/60 shrink-0 bg-[#0d1425]/60 backdrop-blur-sm sticky top-0 z-10">
            <form onSubmit={handleInitiatePlan} className="space-y-3">
              <div className="relative rounded-xl border border-[#334155]/60 bg-[#161f30] overflow-hidden focus-within:border-amber-500/60 focus-within:ring-1 focus-within:ring-amber-500/60 transition-all duration-200">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Ask Autopilot: e.g. Find top 5 personal loan candidates and draft friendly WhatsApp messages..."
                  disabled={loading || executing}
                  className="w-full bg-transparent text-slate-100 text-xs px-3 py-2.5 outline-none resize-none h-16 placeholder-slate-400 font-semibold"
                />
                <div className="flex justify-between items-center px-3 py-2 bg-[#0f172a] border-t border-[#1e293b]/60">
                  <span className="text-[9px] text-slate-400 font-bold">Auto-verifies outputs & retries</span>
                  <button
                    type="submit"
                    disabled={loading || executing || !inputText.trim()}
                    className={clsx(
                      "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold text-white transition-all shadow-md",
                      (loading || executing || !inputText.trim())
                        ? "bg-slate-700/60 cursor-not-allowed opacity-50"
                        : "bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 active:scale-95"
                    )}
                  >
                    {loading ? <Loader2 className="animate-spin" size={12} /> : <Play size={10} />}
                    Initialize Plan
                  </button>
                </div>
              </div>
            </form>

            {/* Quick Templates Suggestion Bar */}
            {!plan && !loading && (
              <div className="mt-3.5 space-y-1.5">
                <div className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider">Quick Suggestions</div>
                <div className="space-y-1">
                  {templates.map((tmpl, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleTemplateSelect(tmpl)}
                      className="w-full text-left bg-[#131b2e] border border-[#1e293b]/40 rounded-lg p-2 hover:bg-[#1a243d] hover:border-slate-500/40 text-[10px] text-slate-300 font-bold transition-all line-clamp-1"
                    >
                      {tmpl}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Stepper Timeline & Logs */}
          <div className="flex-1 px-4 py-4 space-y-4">
            {/* Action Bar for Plan Approvals */}
            {plan && !planApproved && (
              <motion.div 
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="bg-gradient-to-r from-amber-500/10 via-orange-600/15 to-amber-500/10 border-2 border-amber-500/30 rounded-xl p-4 flex flex-col items-center justify-center text-center gap-3 shadow-lg select-none"
              >
                <div className="text-xs text-amber-300 font-bold leading-relaxed">
                  🚦 Strategy Plan generated. Ready to authorize?
                </div>
                <button
                  type="button"
                  onClick={handleApproveAndTrigger}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-extrabold text-xs shadow-md transition-all active:scale-97 cursor-pointer"
                >
                  🚀 Approve Plan & Trigger Autopilot Executor
                </button>
              </motion.div>
            )}

            {/* Run State banner */}
            {(loading || executing || plan) && (
              <div className="bg-[#121c33] border border-[#22c55e]/10 rounded-xl p-3 flex gap-3 shrink-0 items-start select-none shadow-md shadow-black/20">
                <div className="w-6 h-6 bg-[#22c55e]/10 rounded-lg flex items-center justify-center shrink-0">
                  {executing ? (
                    <Loader2 size={13} className="text-emerald-400 animate-spin" />
                  ) : (
                    <CheckCircle2 size={13} className="text-emerald-400" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider leading-none">Autopilot Status</div>
                  <p className="text-[11px] text-slate-200 font-semibold leading-relaxed mt-1">{runningLog}</p>
                </div>
              </div>
            )}

            {/* Steps Timeline Grid */}
            {plan && (
              <div className="space-y-3 relative select-none">
                <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-[#1e293b]/80 z-0"></div>
                
                {plan.steps.map((step, idx) => {
                  const isCurrent = currentStepNum === step.step_number
                  const isDone = step.status === 'success'
                  const isFailed = step.status === 'failed'
                  const isRetrying = step.status === 'retrying' || step.retry_count > 0 && !isDone && !isFailed
                  const rationalExpanded = expandedRationale[step.step_number]
                  const subExpanded = expandedSubsteps[step.step_number]
                  const sEvents = intermediateEvents[step.step_number] || []

                  return (
                    <motion.div
                      key={step.step_id || idx}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="relative pl-9 z-10"
                    >
                      {/* Timeline node icon */}
                      <span className={clsx(
                        "absolute left-2.5 top-2 w-3.5 h-3.5 rounded-full flex items-center justify-center shrink-0 border -translate-x-1/2 shadow-sm transition-all duration-200",
                        isDone && "bg-emerald-500 border-emerald-400 text-emerald-950",
                        isFailed && "bg-rose-500 border-rose-400 text-rose-950",
                        isCurrent && "bg-amber-500 border-amber-400 text-amber-950 animate-pulse",
                        !isDone && !isFailed && !isCurrent && "bg-[#161f30] border-[#334155] text-slate-400"
                      )}>
                        {isDone && <CheckCircle2 size={8} className="stroke-[3]" />}
                        {isFailed && <XCircle size={8} className="stroke-[3]" />}
                        {isCurrent && <Loader2 size={8} className="animate-spin stroke-[3]" />}
                      </span>

                      {/* Timeline content box */}
                      <div className={clsx(
                        "border rounded-xl p-3 bg-[#111827]/70 backdrop-blur-xs transition-all duration-200 shadow-sm shadow-black/10 select-none",
                        isCurrent ? "border-amber-500/60 bg-[#171f33]/70" : "border-[#1e293b]/60",
                        isDone && "border-emerald-500/20 bg-[#0f1725]/40"
                      )}>
                        <div className="flex items-center justify-between select-none">
                          <span className="text-[10px] font-bold text-slate-400">Step {step.step_number}</span>
                          <span className={clsx(
                            "text-[8px] px-2 py-0.5 rounded-full font-bold border",
                            isDone && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                            isFailed && "bg-rose-500/10 text-rose-400 border-rose-500/20",
                            isCurrent && "bg-amber-500/10 text-amber-400 border-amber-500/20",
                            !isDone && !isFailed && !isCurrent && "bg-slate-500/10 text-slate-400 border-slate-500/20"
                          )}>
                            {(step.status || 'pending').toUpperCase()}
                          </span>
                        </div>
                        
                        <h4 className="text-xs font-bold text-white mt-1.5 leading-snug">{step.description}</h4>
                        <div className="text-[9px] bg-[#162035] text-slate-300 font-semibold px-2 py-0.5 rounded mt-2.5 inline-block border border-[#334155]/20 font-mono">
                          🔧 {step.tool_name}
                        </div>

                        {/* Retries Alert if active */}
                        {step.retry_count > 0 && !isDone && (
                          <div className="flex items-center gap-1.5 mt-2 text-[9px] text-amber-400 font-bold bg-amber-500/5 px-2 py-1 rounded border border-amber-500/10 select-none">
                            <AlertTriangle size={10} />
                            Retry Attempt #{step.retry_count} / {step.max_retries}
                          </div>
                        )}

                        {/* Rationale Change of thought accordion */}
                        {step.rationale && (
                          <div className="mt-2.5 border-t border-[#1e293b]/60 pt-2 select-none">
                            <button
                              type="button"
                              onClick={() => toggleRationale(step.step_number)}
                              className="flex items-center gap-1 text-[9px] text-amber-400 hover:text-amber-300 font-bold tracking-wide select-none cursor-pointer"
                            >
                              {rationalExpanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                              PLANNING THOUGHT
                            </button>
                            <AnimatePresence>
                              {rationalExpanded && (
                                <motion.p
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: "auto", opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  className="text-[10px] text-slate-400 font-semibold leading-relaxed mt-1 overflow-hidden"
                                >
                                  {step.rationale}
                                </motion.p>
                              )}
                            </AnimatePresence>
                          </div>
                        )}

                        {/* Intermediate Sub-step thoughts accordion */}
                        {sEvents.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-[#1e293b]/40 select-none">
                            <button
                              type="button"
                              onClick={() => toggleSubsteps(step.step_number)}
                              className="flex items-center gap-1.5 text-[9px] text-emerald-400 hover:text-emerald-300 font-extrabold tracking-wide select-none cursor-pointer"
                            >
                              {subExpanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                              🧠 AGENT SUB-STEPS ({sEvents.length})
                            </button>
                            <AnimatePresence>
                              {subExpanded && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: "auto", opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  className="mt-2 space-y-2 pl-2 border-l border-slate-700/60 overflow-hidden"
                                >
                                  {sEvents.map((evt, eIdx) => (
                                    <div key={eIdx} className="text-[10px] leading-relaxed">
                                      {evt.type === 'thought' && (
                                        <div className="text-slate-400 font-semibold italic">
                                          💭 {evt.text}
                                        </div>
                                      )}
                                      {evt.type === 'tool_call' && (
                                        <div className="text-amber-400 font-bold">
                                          🔧 Calling: <span className="underline font-mono">{evt.tool}</span>
                                        </div>
                                      )}
                                      {evt.type === 'tool_result' && (
                                        <div className="text-slate-400 text-[9px] bg-slate-900/60 p-1.5 rounded border border-[#1e293b]/40 font-mono line-clamp-2 mt-1">
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
                      </div>
                    </motion.div>
                  )
                })}
                <div ref={timelineEndRef} />
              </div>
            )}
          </div>
        </aside>

        {/* Right Output Dashboard (60% width) */}
        <main className="flex-1 flex flex-col h-full bg-[#080c14] relative z-0 overflow-y-auto no-scrollbar">
          {/* Background Gradient Orbs */}
          <div className="absolute top-1/4 left-1/3 w-80 h-80 rounded-full bg-blue-500/5 blur-[120px] pointer-events-none z-0 animate-pulse-slow"></div>
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-amber-500/5 blur-[120px] pointer-events-none z-0 animate-pulse-slow"></div>

          <div className="p-6 relative z-10 flex-1 flex flex-col">
            {/* Welcome banner if no plan active */}
            {!plan && !loading && (
              <div className="flex-1 flex flex-col items-center justify-center py-20 px-6 max-w-2xl mx-auto text-center select-none">
                <div className="w-16 h-16 bg-gradient-to-br from-amber-400/20 via-orange-500/20 to-red-600/20 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-black/10">
                  <Zap size={28} className="text-amber-400 fill-amber-500/10 animate-bounce-slow" />
                </div>
                <h2 className="text-2xl font-black text-white tracking-tight font-display mb-3">AI Autopilot Executor Workspace</h2>
                <p className="text-slate-400 leading-relaxed text-xs font-semibold mb-8">
                  Submit a goal and watch the orchestrator build a change-of-thought sequence. The system handles raw data extraction, validates compliance checkpoints, manages tool retries with exponential backoffs, and performs self-correcting re-plans on failures automatically.
                </p>
                <div className="grid grid-cols-3 gap-4 w-full">
                  {[
                    { title: "Plan", desc: "Formulates a sequential plan listing Change-of-Thought rationale." },
                    { title: "Self-Verify", desc: "Strictly validates tool outputs and retries up to 3 times on bugs." },
                    { title: "HITL Control", desc: "Wait checkpoints allow you to review, edit, and preview copy." }
                  ].map((feat, i) => (
                    <div key={i} className="bg-[#0f1524] border border-[#1e293b]/60 rounded-xl p-4 shadow-sm">
                      <h4 className="text-xs font-bold text-white tracking-tight">{feat.title}</h4>
                      <p className="text-[10px] text-slate-400 mt-1 font-semibold leading-relaxed">{feat.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Output Panels */}
            {plan && (
              <div className="flex-1 flex flex-col gap-6 select-none">
                {/* 1. Human-in-the-Loop Message Composer Modal / Box */}
                <AnimatePresence>
                  {hitlStep && (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -15 }}
                      className="bg-[#0e1628]/90 border border-amber-500/40 rounded-xl p-5 shadow-lg shadow-black/40 backdrop-blur-md relative"
                    >
                      <div className="flex items-center gap-2 mb-4">
                        <Smartphone size={16} className="text-amber-500 animate-bounce" />
                        <h3 className="text-sm font-extrabold text-white tracking-tight">HUMAN REVIEW: Drafted WhatsApp Offer</h3>
                        <span className="text-[8px] bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded border border-amber-500/20 font-bold ml-auto select-none">AWAITING APPROVAL</span>
                      </div>

                      <div className="grid grid-cols-12 gap-5 items-start">
                        {/* Editor Pane (Left 7 cols) */}
                        <div className="col-span-7 space-y-3">
                          <label className="text-[10px] text-slate-400 font-extrabold tracking-wider uppercase leading-none block select-none">Draft Text Editor</label>
                          <textarea
                            value={hitlMessage}
                            onChange={(e) => setHitlMessage(e.target.value)}
                            className="w-full bg-[#121b2d] border border-[#2c3d59] rounded-xl p-3 text-xs outline-none text-slate-100 font-semibold h-40 focus:border-amber-500/60 leading-relaxed"
                          />
                          <button
                            onClick={handleApproveHitl}
                            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white text-xs font-bold rounded-xl transition-all shadow-md active:scale-98 select-none cursor-pointer"
                          >
                            <Send size={12} />
                            Approve Copy & Resume Loop
                          </button>
                        </div>

                        {/* Phone Mockup Preview Pane (Right 5 cols) */}
                        <div className="col-span-5 flex justify-center">
                          <div className="w-[200px] h-[340px] border-4 border-slate-700 bg-slate-900 rounded-3xl overflow-hidden relative shadow-md shadow-black/40 flex flex-col">
                            {/* Camera notch */}
                            <div className="absolute top-1.5 left-1/2 -translate-x-1/2 w-12 h-3 bg-slate-700 rounded-full z-20"></div>
                            {/* WhatsApp Header bar */}
                            <div className="bg-[#075e54] text-white pt-5 pb-1 px-3 text-[9px] font-bold flex items-center justify-between shrink-0 select-none">
                              <span>Loan It Support</span>
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                            </div>
                            {/* Chat area bg */}
                            <div className="flex-1 bg-[#efeae2] p-2 overflow-y-auto no-scrollbar">
                              <div className="bg-white rounded-lg p-2 max-w-[85%] text-[9px] text-slate-800 leading-normal shadow-sm font-semibold select-text">
                                {hitlMessage || "Reviewing pre-approved offers..."}
                                <span className="block text-right text-[7px] text-slate-400 mt-1">11:34 AM</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* 2. Dynamic Data Grid Grid Results */}
                {tableData && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-[#0d1425]/60 border border-[#1e293b]/60 rounded-xl p-5 shadow-sm shadow-black/20 flex-1 flex flex-col"
                  >
                    <div className="flex items-center gap-2.5 mb-4 border-b border-[#1e293b]/60 pb-3">
                      <Database size={15} className="text-blue-500" />
                      <h3 className="text-sm font-extrabold text-white tracking-tight leading-none">Dynamic Data Grid</h3>
                      <span className="text-[9px] text-slate-400 font-bold">Autopilot Extracted Results</span>
                    </div>

                    <div className="overflow-x-auto flex-1 scrollbar-light">
                      <table className="w-full text-left border-collapse min-w-[500px]">
                        <thead>
                          <tr className="border-b border-[#1e293b]/80 text-[10px] text-slate-400 font-extrabold uppercase tracking-wider bg-[#0f1726]/40 select-none">
                            {Object.keys(tableData[0]).map((key, idx) => (
                              <th key={idx} className="pb-3 pt-2 px-3">{key.replace('_', ' ')}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {tableData.map((row, idx) => (
                            <tr key={idx} className="border-b border-[#1e293b]/30 hover:bg-[#161f30]/30 transition-colors text-xs font-semibold">
                              {Object.values(row).map((val, colIdx) => (
                                <td key={colIdx} className="py-2.5 px-3 truncate max-w-[200px]">{String(val)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                )}

                {/* 3. Raw Steps execution summary fallback if no visual tables parsed */}
                {!tableData && !hitlStep && plan.steps.some(s => s.status === 'success') && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-[#0d1425]/60 border border-[#1e293b]/60 rounded-xl p-5 shadow-sm"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <Database size={14} className="text-emerald-500" />
                      <h3 className="text-xs font-extrabold text-white tracking-tight leading-none">Active Logs View</h3>
                    </div>
                    <div className="bg-[#0b0f19] border border-[#1e293b]/40 rounded-lg p-4 font-mono text-[10px] leading-relaxed text-slate-300 max-h-96 overflow-y-auto no-scrollbar scrollbar-light">
                      {plan.steps
                        .filter(s => s.status === 'success' && s.tool_result)
                        .map((step, idx) => (
                          <div key={idx} className="mb-4 last:mb-0">
                            <span className="text-emerald-400 font-bold">»»» [Step {step.step_number} SUCCESS] Tool: {step.tool_name}</span>
                            <pre className="mt-1 whitespace-pre-wrap pl-4 border-l-2 border-slate-700/60 font-semibold font-sans text-[11px] leading-relaxed">
                              {step.tool_result}
                            </pre>
                          </div>
                        ))}
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
