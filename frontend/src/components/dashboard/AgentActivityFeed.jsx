import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, RefreshCw, Clock, Activity, Wrench, CheckCircle, AlertCircle } from 'lucide-react'
import { getAuditLogs } from '../../api/client'
import { AgentActivitySkeleton } from '../shared/LoadingSkeleton'
import clsx from 'clsx'

const AGENT_COLORS = {
  ProspectDiscoveryAgent: 'bg-blue-500',
  LoanReadinessAgent: 'bg-emerald-500',
  ComplianceAgent: 'bg-amber-500',
  OutreachAgent: 'bg-purple-500',
  EvidenceAggregationAgent: 'bg-indigo-500',
  CampaignAgent: 'bg-rose-500',
  default: 'bg-slate-500',
}

const AGENT_ABBR = {
  ProspectDiscoveryAgent: 'PD',
  LoanReadinessAgent: 'LR',
  ComplianceAgent: 'CA',
  OutreachAgent: 'OA',
  EvidenceAggregationAgent: 'EA',
  CampaignAgent: 'CM',
}

function formatTimestamp(ts) {
  if (!ts) return ''
  const date = new Date(ts)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return 'just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return date.toLocaleDateString()
}

function getAgentFromLog(log) {
  return log.agent_name || log.entity_type || 'System'
}

function getActionText(log) {
  if (log.action) return log.action
  if (log.event_type) return log.event_type.replace(/_/g, ' ')
  if (log.description) return log.description
  return 'Performed action'
}

function ActivityItem({ log, idx }) {
  const agent = getAgentFromLog(log)
  const agentColor = AGENT_COLORS[agent] || AGENT_COLORS.default
  const abbr = AGENT_ABBR[agent] || agent.slice(0, 2).toUpperCase()
  const action = getActionText(log)

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: idx * 0.04 }}
      className="flex items-start gap-3 py-2.5 border-b border-slate-50 last:border-0"
    >
      <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5', agentColor)}>
        {abbr}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <span className="text-xs font-semibold text-slate-800">{agent}</span>
            <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
              {action}
              {log.entity_id && (
                <span className="text-slate-400 ml-1">· {log.entity_id}</span>
              )}
            </p>
          </div>
          <span className="text-xs text-slate-400 shrink-0 tabular-nums">
            {formatTimestamp(log.created_at || log.timestamp)}
          </span>
        </div>
        {log.details && (
          <div className="mt-1 text-xs text-slate-400 truncate">{log.details}</div>
        )}
      </div>
    </motion.div>
  )
}

export default function AgentActivityFeed() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getAuditLogs(20)
      const items = data.logs || data.audit_logs || data || []
      setLogs(Array.isArray(items) ? items : [])
      setLastRefresh(new Date())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Keep initially empty per requirements. Load data on RM refresh request.
  }, [])


  return (
    <div className="card overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-blue-500" />
          <h3 className="text-sm font-semibold text-slate-900">Agent Activity</h3>
          {!loading && (
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          )}
        </div>
        <button
          onClick={fetchLogs}
          disabled={loading}
          className={clsx(
            'p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors',
            loading && 'animate-spin'
          )}
          title="Refresh"
        >
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-2 min-h-0">
        {loading && logs.length === 0 ? (
          <div className="py-3">
            <AgentActivitySkeleton />
          </div>
        ) : error ? (
          <div className="py-6 text-center">
            <AlertCircle size={24} className="text-slate-300 mx-auto mb-2" />
            <p className="text-xs text-slate-400">Could not load activity</p>
            <button onClick={fetchLogs} className="text-xs text-blue-500 hover:underline mt-1">
              Retry
            </button>
          </div>
        ) : logs.length === 0 ? (
          <div className="py-6 text-center">
            <Bot size={24} className="text-slate-300 mx-auto mb-2" />
            <p className="text-xs text-slate-500">No agent activity yet</p>
            <p className="text-xs text-slate-400">Activity will appear as agents run</p>
          </div>
        ) : (
          <AnimatePresence>
            {logs.map((log, i) => (
              <ActivityItem key={log.id || log.audit_id || i} log={log} idx={i} />
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-slate-50 bg-slate-50/50">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Clock size={10} />
          Updated {formatTimestamp(lastRefresh.toISOString())} · Auto-refreshes every 30s
        </div>
      </div>
    </div>
  )
}
