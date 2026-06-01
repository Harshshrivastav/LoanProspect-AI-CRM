import React, { useState } from 'react'
import { Bot, RefreshCw, AlertCircle, Loader2 } from 'lucide-react'
import { analyzeCustomerWithCrew } from '../../api/client'
import EvidenceTimeline from './EvidenceTimeline'
import clsx from 'clsx'

export default function AgentContributionPanel({ customerId, customer, prospect, onReanalyzed }) {
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
      if (onReanalyzed) {
        onReanalyzed()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setReanalyzing(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header and trigger */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <div className="p-1 rounded-lg bg-blue-50 text-blue-600 shrink-0">
            <Bot size={14} />
          </div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Agent Engine Logs
          </h4>
        </div>
        <button
          onClick={handleReanalyze}
          disabled={reanalyzing}
          className={clsx(
            'inline-flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg transition-colors border shadow-sm',
            reanalyzing
              ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
              : 'bg-blue-50 hover:bg-blue-100 border-blue-100 text-blue-700'
          )}
        >
          <RefreshCw size={10} className={reanalyzing ? 'animate-spin' : ''} />
          {reanalyzing ? 'Evaluating…' : 'Re-Score'}
        </button>
      </div>

      {/* Progress alerts */}
      {reanalyzing && (
        <div className="flex items-start gap-2.5 p-3 bg-blue-50 border border-blue-100 rounded-xl animate-pulse">
          <Loader2 size={14} className="text-blue-500 animate-spin shrink-0 mt-0.5" />
          <div className="min-w-0">
            <div className="text-xs font-bold text-blue-800">CrewAI execution started</div>
            <div className="text-[10px] text-blue-600 mt-0.5 leading-normal">
              Running Discovery, Readiness, Compliance, and Outreach agents. This takes 10–30 seconds.
            </div>
          </div>
        </div>
      )}

      {reanalysisResult && (
        <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-xl">
          <div className="text-xs font-bold text-emerald-800 flex items-center gap-1.5">
            <span>✓</span> Scoring Complete
          </div>
          <p className="text-[10px] text-emerald-600 mt-0.5 leading-relaxed">
            {reanalysisResult.message || reanalysisResult.result || 'Aggregated latest spending records and successfully updated confidence indices.'}
          </p>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-2.5 p-3 bg-red-50 border border-red-100 rounded-xl">
          <AlertCircle size={14} className="text-red-500 shrink-0 mt-0.5" />
          <span className="text-[10px] text-red-700 font-semibold leading-relaxed">
            {error}
          </span>
        </div>
      )}

      {/* Embedded Timeline */}
      <EvidenceTimeline prospect={prospect} />

      {/* Explanation of Agent orchestration */}
      <p className="text-[10px] text-slate-400 leading-normal p-2.5 bg-slate-50 border border-slate-100 rounded-xl">
        Evidence aggregator matches transactions with demographic proxies through multi-agent CrewAI layers powered by Google Gemini models.
      </p>
    </div>
  )
}
