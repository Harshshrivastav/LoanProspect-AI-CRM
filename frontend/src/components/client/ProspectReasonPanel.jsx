import React from 'react'
import { CheckCircle, AlertTriangle, Target, TrendingUp, ChevronRight, Lightbulb } from 'lucide-react'
import { ScoreCircle } from '../shared/ScoreBar'
import { SignalList } from '../shared/SignalChip'
import ConfidenceMeter from '../shared/ConfidenceMeter'
import clsx from 'clsx'

function ScoreBreakdown({ breakdown = {} }) {
  const entries = Object.entries(breakdown).sort(([, a], [, b]) => b - a)
  const maxVal = Math.max(...entries.map(([, v]) => v), 1)

  if (!entries.length) return null

  return (
    <div className="space-y-2">
      {entries.map(([key, val]) => {
        const pct = (val / maxVal) * 100
        return (
          <div key={key} className="flex items-center gap-2">
            <div className="text-xs text-slate-600 w-40 truncate capitalize">{key.replace(/_/g, ' ')}</div>
            <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all duration-700"
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-xs font-semibold text-slate-700 w-6 text-right">{val}</span>
          </div>
        )
      })}
    </div>
  )
}

export default function ProspectReasonPanel({ prospect }) {
  if (!prospect) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-16">
        <Target size={40} className="text-slate-300 mb-3" />
        <h3 className="text-lg font-semibold text-slate-600">No Prospect Score</h3>
        <p className="text-slate-400 text-sm mt-1 text-center max-w-xs">
          This customer hasn't been scored yet. Use the Re-analyze button to compute their prospect score.
        </p>
      </div>
    )
  }

  const {
    readiness_score = 0,
    conversion_band = 'low',
    confidence = 0,
    positive_signals = [],
    risk_flags = [],
    loan_fit_factors = [],
    score_breakdown = {},
    recommendation_reason = '',
    next_best_action = '',
  } = prospect

  const bandColors = {
    high: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    medium: 'bg-amber-100 text-amber-700 border-amber-200',
    low: 'bg-red-100 text-red-700 border-red-200',
  }

  return (
    <div className="space-y-6">
      {/* Score Hero */}
      <div className="flex items-center gap-6 p-5 bg-gradient-to-r from-slate-50 to-blue-50 rounded-xl border border-slate-200">
        <ScoreCircle score={readiness_score} size="lg" />
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={clsx('px-3 py-1 rounded-full text-sm font-bold border', bandColors[conversion_band])}>
              {conversion_band === 'high' ? '🔥 High Intent' : conversion_band === 'medium' ? '⚡ Medium Intent' : '🔵 Low Intent'}
            </span>
          </div>
          <ConfidenceMeter confidence={confidence} label="AI Confidence" />
          {recommendation_reason && (
            <p className="text-sm text-slate-600 mt-2 leading-relaxed">{recommendation_reason}</p>
          )}
        </div>
      </div>

      {/* Next Best Action */}
      {next_best_action && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3">
          <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center shrink-0">
            <TrendingUp size={15} className="text-white" />
          </div>
          <div>
            <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-1">Next Best Action</div>
            <p className="text-sm font-semibold text-emerald-900">{next_best_action}</p>
          </div>
        </div>
      )}

      {/* Positive Signals */}
      {positive_signals.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
            <CheckCircle size={14} className="text-emerald-500" />
            Positive Signals
          </h4>
          <SignalList signals={positive_signals} maxVisible={10} />
        </div>
      )}

      {/* Risk Flags */}
      {risk_flags.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
            <AlertTriangle size={14} className="text-red-500" />
            Risk Flags
          </h4>
          <SignalList riskFlags={risk_flags} maxVisible={10} />
        </div>
      )}

      {/* Loan Fit Factors */}
      {loan_fit_factors.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1.5">
            <Lightbulb size={14} className="text-blue-500" />
            Loan Fit Analysis
          </h4>
          <div className="space-y-2">
            {loan_fit_factors.map((factor, i) => (
              <div key={i} className="flex items-start gap-2 p-2.5 bg-slate-50 rounded-lg">
                <span className="text-sm leading-relaxed">{factor}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Score Breakdown */}
      {Object.keys(score_breakdown).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1.5">
            <Target size={14} className="text-indigo-500" />
            Score Breakdown
          </h4>
          <ScoreBreakdown breakdown={score_breakdown} />
        </div>
      )}
    </div>
  )
}
