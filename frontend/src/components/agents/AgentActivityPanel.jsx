import React, { useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, Cpu, Wrench, CheckCircle, Loader, AlertCircle, Zap } from 'lucide-react'
import ToolExecutionCard from './ToolExecutionCard'
import clsx from 'clsx'

const AGENT_COLORS = {
  ProspectDiscoveryAgent: { bg: 'bg-blue-500', text: 'text-blue-600', light: 'bg-blue-50 border-blue-200' },
  LoanReadinessAgent: { bg: 'bg-emerald-500', text: 'text-emerald-600', light: 'bg-emerald-50 border-emerald-200' },
  ComplianceAgent: { bg: 'bg-amber-500', text: 'text-amber-600', light: 'bg-amber-50 border-amber-200' },
  OutreachAgent: { bg: 'bg-purple-500', text: 'text-purple-600', light: 'bg-purple-50 border-purple-200' },
  EvidenceAggregationAgent: { bg: 'bg-indigo-500', text: 'text-indigo-600', light: 'bg-indigo-50 border-indigo-200' },
  CampaignAgent: { bg: 'bg-rose-500', text: 'text-rose-600', light: 'bg-rose-50 border-rose-200' },
  default: { bg: 'bg-slate-500', text: 'text-slate-600', light: 'bg-slate-50 border-slate-200' },
}

function getEventIcon(type) {
  switch (type) {
    case 'agent_start': return <Cpu size={12} className="text-blue-500" />
    case 'agent_done': return <CheckCircle size={12} className="text-emerald-500" />
    case 'tool_call': return <Wrench size={12} className="text-purple-500" />
    case 'tool_result': return <CheckCircle size={12} className="text-purple-400" />
    case 'status': return <Zap size={12} className="text-amber-500" />
    case 'error': return <AlertCircle size={12} className="text-red-500" />
    default: return <Bot size={12} className="text-slate-400" />
  }
}

function ActivityEventItem({ event, isLast }) {
  const agentName = event.agent || event.agent_name || 'System'
  const colors = AGENT_COLORS[agentName] || AGENT_COLORS.default
  const isToolEvent = event.type === 'tool_call' || event.type === 'tool_result'

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="relative pl-7 pb-3"
    >
      {/* Timeline line */}
      {!isLast && (
        <div className="absolute left-3 top-4 bottom-0 w-px bg-slate-200" />
      )}

      {/* Timeline dot */}
      <div className="absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center border-2 border-white shadow-sm bg-white">
        {getEventIcon(event.type)}
      </div>

      {/* Content */}
      <div className="min-w-0">
        {isToolEvent ? (
          <ToolExecutionCard event={event} />
        ) : (
          <div className={clsx('rounded-lg border p-2.5', colors.light)}>
            <div className="flex items-center justify-between mb-0.5">
              <span className={clsx('text-xs font-semibold', colors.text)}>
                {agentName}
              </span>
              {event.ts && (
                <span className="text-xs text-slate-400 tabular-nums">
                  {new Date(event.ts).toLocaleTimeString()}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              {event.message || event.task || event.result || event.error || event.type}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function AgentActivityPanel({ activity = [], isStreaming = false, currentAgent = null }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activity.length])

  if (!isStreaming && activity.length === 0) return null

  return (
    <div className="border-t border-slate-100 bg-slate-50/60 px-4 py-3">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-5 h-5 rounded-md bg-blue-600 flex items-center justify-center">
          <Bot size={11} className="text-white" />
        </div>
        <span className="text-xs font-semibold text-slate-700">Agent Activity</span>
        {isStreaming && (
          <div className="flex items-center gap-1.5 ml-1">
            <div className="flex gap-0.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1 h-1 rounded-full bg-blue-500 animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
            {currentAgent && (
              <span className="text-xs text-blue-600 font-medium">{currentAgent} working…</span>
            )}
          </div>
        )}
      </div>

      <div className="max-h-48 overflow-y-auto space-y-0 pr-1">
        <AnimatePresence>
          {activity.map((event, i) => (
            <ActivityEventItem
              key={`${event.type}-${i}`}
              event={event}
              isLast={i === activity.length - 1}
            />
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
