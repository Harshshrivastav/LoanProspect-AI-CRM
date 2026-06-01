import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, ChevronDown, ChevronUp, RefreshCw, Wrench, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import { analyzeCustomerWithCrew } from '../../api/client'
import clsx from 'clsx'

const AGENT_INFO = {
  ProspectDiscoveryAgent: {
    color: 'bg-blue-500',
    light: 'bg-blue-50 border-blue-200',
    text: 'text-blue-700',
    desc: 'Scans transactions and account history to identify prospect signals',
  },
  LoanReadinessAgent: {
    color: 'bg-emerald-500',
    light: 'bg-emerald-50 border-emerald-200',
    text: 'text-emerald-700',
    desc: 'Computes loan readiness score and conversion band',
  },
  ComplianceAgent: {
    color: 'bg-amber-500',
    light: 'bg-amber-50 border-amber-200',
    text: 'text-amber-700',
    desc: 'Validates KYC status and marketing consent',
  },
  EvidenceAggregationAgent: {
    color: 'bg-indigo-500',
    light: 'bg-indigo-50 border-indigo-200',
    text: 'text-indigo-700',
    desc: 'Synthesizes all agent findings into unified recommendation',
  },
  OutreachAgent: {
    color: 'bg-purple-500',
    light: 'bg-purple-50 border-purple-200',
    text: 'text-purple-700',
    desc: 'Generates personalized outreach messages',
  },
}

const DEFAULT_AGENTS = [
  'ProspectDiscoveryAgent',
  'LoanReadinessAgent',
  'ComplianceAgent',
  'EvidenceAggregationAgent',
]

function AgentAccordion({ agentName, customer, prospect }) {
  const [open, setOpen] = useState(false)
  const info = AGENT_INFO[agentName] || {
    color: 'bg-slate-500',
    light: 'bg-slate-50 border-slate-200',
    text: 'text-slate-700',
    desc: 'Processing customer data',
  }

  const abbr = agentName.slice(0, 2).toUpperCase()

  // Build key finding based on agent type and available data
  const getKeyFinding = () => {
    if (!prospect) return 'Not analyzed yet'
    if (agentName === 'LoanReadinessAgent') {
      return `Score: ${prospect.readiness_score}/100 — ${prospect.conversion_band} conversion band`
    }
    if (agentName === 'ProspectDiscoveryAgent') {
      const signals = (prospect.positive_signals || []).slice(0, 2).join(', ')
      return signals ? `Signals: ${signals}` : 'No strong signals detected'
    }
    if (agentName === 'ComplianceAgent') {
      const cust = customer?.customer || customer
      return cust?.kyc_status === 'verified'
        ? 'KYC verified · Marketing consent obtained'
        : 'KYC status requires attention'
    }
    if (agentName === 'EvidenceAggregationAgent') {
      return prospect.recommendation_reason || 'See full analysis below'
    }
    return 'Analysis complete'
  }

  return (
    <div className={clsx('border rounded-xl overflow-hidden', info.light)}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/50 transition-colors text-left"
      >
        <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0', info.color)}>
          {abbr}
        </div>
        <div className="flex-1 min-w-0">
          <div className={clsx('text-xs font-semibold', info.text)}>{agentName}</div>
          <div className="text-xs text-slate-500 truncate">{getKeyFinding()}</div>
        </div>
        <CheckCircle size={14} className="text-emerald-500 shrink-0" />
        {open ? <ChevronUp size={14} className="text-slate-400 shrink-0" /> : <ChevronDown size={14} className="text-slate-400 shrink-0" />}
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-1 space-y-2">
              <p className="text-xs text-slate-600">{info.desc}</p>
              <div className="text-xs text-slate-500 font-medium">Key Finding:</div>
              <div className="text-xs text-slate-700 bg-white rounded-lg p-2.5 border border-slate-200">
                {getKeyFinding()}
              </div>
              {prospect && agentName === 'ProspectDiscoveryAgent' && (
                <div className="space-y-1">
                  <div className="text-xs text-slate-500 font-medium">Signals detected:</div>
                  {(prospect.positive_signals || []).map(s => (
                    <div key={s} className="text-xs text-emerald-700 bg-emerald-50 rounded px-2 py-1">
                      ✓ {s.replace(/_/g, ' ')}
                    </div>
                  ))}
                  {(prospect.risk_flags || []).map(r => (
                    <div key={r} className="text-xs text-red-700 bg-red-50 rounded px-2 py-1">
                      ⚠ {r.replace(/_/g, ' ')}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function AgentEvidencePanel({ customerId, customer, prospect }) {
  const [reanalyzing, setReanalyzing] = useState(false)
  const [reanalysisResult, setReanalysisResult] = useState(null)
  const [error, setError] = useState(null)

  const handleReanalyze = async () => {
    if (!customerId) return
    setReanalyzing(true)
    setError(null)
    setReanalysisResult(null)
    try {
      const result = await analyzeCustomerWithCrew(customerId)
      setReanalysisResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setReanalyzing(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot size={15} className="text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-800">Agent Evidence</h3>
        </div>
        <button
          onClick={handleReanalyze}
          disabled={reanalyzing}
          className={clsx(
            'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
            reanalyzing
              ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
              : 'bg-blue-50 hover:bg-blue-100 text-blue-700'
          )}
        >
          <RefreshCw size={12} className={reanalyzing ? 'animate-spin' : ''} />
          {reanalyzing ? 'Analyzing…' : 'Re-analyze'}
        </button>
      </div>

      {/* Re-analysis status */}
      {reanalyzing && (
        <div className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-200 rounded-xl">
          <Loader size={15} className="text-blue-500 animate-spin shrink-0" />
          <div>
            <div className="text-xs font-semibold text-blue-700">CrewAI agents running…</div>
            <div className="text-xs text-blue-600">This may take 30–60 seconds</div>
          </div>
        </div>
      )}

      {reanalysisResult && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl">
          <div className="text-xs font-semibold text-emerald-700 mb-1">Re-analysis Complete</div>
          <p className="text-xs text-emerald-600">
            {reanalysisResult.message || reanalysisResult.result || 'Analysis complete. Refresh to see updated scores.'}
          </p>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl">
          <AlertCircle size={14} className="text-red-500 shrink-0" />
          <span className="text-xs text-red-700">{error}</span>
        </div>
      )}

      {/* Agent accordions */}
      <div className="space-y-2">
        {DEFAULT_AGENTS.map(agent => (
          <AgentAccordion
            key={agent}
            agentName={agent}
            customer={customer}
            prospect={prospect}
          />
        ))}
      </div>

      {/* Info note */}
      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
        <p className="text-xs text-slate-500">
          Agent analysis is powered by CrewAI multi-agent orchestration with Google Gemini.
          Each agent specializes in a different aspect of prospect evaluation.
        </p>
      </div>
    </div>
  )
}
