import React from 'react'
import { CheckCircle2, AlertTriangle, HelpCircle, BrainCircuit } from 'lucide-react'
import ScoreBar from '../shared/ScoreBar'
import ConfidenceMeter from '../shared/ConfidenceMeter'
import clsx from 'clsx'

const BAND_THEMES = {
  high: {
    bg: 'bg-emerald-50 text-emerald-800 border-emerald-100',
    badge: 'bg-emerald-500 text-white',
    icon: '🔥 High Intent',
  },
  medium: {
    bg: 'bg-amber-50 text-amber-800 border-amber-100',
    badge: 'bg-amber-500 text-white',
    icon: '⚡ Medium Intent',
  },
  low: {
    bg: 'bg-slate-50 text-slate-800 border-slate-100',
    badge: 'bg-slate-400 text-white',
    icon: '🔵 Low Intent',
  },
}

export default function ProspectReasonCard({ prospect }) {
  if (!prospect) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200">
        <BrainCircuit size={28} className="text-slate-300 mb-2" />
        <h4 className="text-xs font-semibold text-slate-700">Not Evaluated</h4>
        <p className="text-[10px] text-slate-400 mt-1 max-w-[180px]">
          Score this customer to generate AI loan prospect reasoning files.
        </p>
      </div>
    )
  }

  const {
    readiness_score = 0,
    conversion_band = 'low',
    confidence = 0,
    recommendation_reason = 'Scan transaction records and liabilities to aggregate fit indicators.',
    positive_signals = [],
    risk_flags = [],
  } = prospect

  const theme = BAND_THEMES[conversion_band] || BAND_THEMES.low

  return (
    <div className="glass-panel p-5 rounded-2xl border-slate-200 bg-white relative overflow-hidden active-glow flex flex-col justify-between">
      {/* Decorative vertical band */}
      <div className={clsx(
        'absolute top-0 left-0 w-1.5 h-full',
        conversion_band === 'high' ? 'bg-emerald-500' :
        conversion_band === 'medium' ? 'bg-amber-500' : 'bg-slate-300'
      )} />

      {/* Header Info */}
      <div className="flex justify-between items-start gap-4 mb-4 pl-1">
        <div>
          <span className={clsx('px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider', theme.bg)}>
            {theme.icon}
          </span>
          <h4 className="text-sm font-bold text-slate-900 mt-2">Why Recommend?</h4>
        </div>
        <div className="text-right">
          <p className="text-[9px] text-slate-400 uppercase tracking-widest font-bold">Readiness</p>
          <p className="text-3xl font-black text-blue-600 leading-none mt-1">
            {readiness_score}<span className="text-xs font-semibold text-blue-400">%</span>
          </p>
        </div>
      </div>

      {/* Reason Paragraph */}
      <p className="text-xs text-slate-600 leading-relaxed italic pl-1 border-l border-slate-100 mb-4 bg-slate-50/50 p-2.5 rounded-lg">
        "{recommendation_reason}"
      </p>

      {/* Rationale Signals & Risks */}
      <div className="space-y-3.5 mb-4 pl-1">
        {/* Positive Factors */}
        {positive_signals.length > 0 && (
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-400 uppercase tracking-widest">
              <CheckCircle2 size={11} className="text-emerald-500" />
              Positive Signals
            </div>
            <div className="flex flex-wrap gap-1">
              {positive_signals.slice(0, 3).map((sig, i) => (
                <span key={i} className="text-[10px] bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-md font-semibold border border-emerald-100 capitalize">
                  {sig.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Risk Flags */}
        {risk_flags.length > 0 && (
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5 text-[9px] font-bold text-slate-400 uppercase tracking-widest">
              <AlertTriangle size={11} className="text-rose-500" />
              Risk Flags
            </div>
            <div className="flex flex-wrap gap-1">
              {risk_flags.slice(0, 2).map((risk, i) => (
                <span key={i} className="text-[10px] bg-rose-50 text-rose-800 px-2 py-0.5 rounded-md font-semibold border border-rose-100 capitalize">
                  {risk.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Confidence Footer */}
      <div className="pt-3 border-t border-slate-100 flex items-center gap-3 pl-1">
        <div className="flex-1 min-w-0">
          <div className="flex justify-between text-[10px] font-semibold text-slate-500 mb-1">
            <span>Confidence Index</span>
            <span className="text-blue-600 font-bold">{Math.round(confidence * 100)}%</span>
          </div>
          <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-500',
                confidence >= 0.8 ? 'bg-emerald-500' : confidence >= 0.5 ? 'bg-amber-500' : 'bg-rose-500'
              )}
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
        </div>
        <button
          className="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors shrink-0"
          title="Confidence metrics generated via CrewAI evidence correlation matrices."
        >
          <HelpCircle size={13} />
        </button>
      </div>
    </div>
  )
}
