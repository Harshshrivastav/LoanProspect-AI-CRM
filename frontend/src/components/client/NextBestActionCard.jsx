import React from 'react'
import { Rocket, Sparkles, MessageSquareCode } from 'lucide-react'
import clsx from 'clsx'

export default function NextBestActionCard({ prospect, onExecuteOutreach }) {
  if (!prospect) return null

  const {
    conversion_band = 'low',
    next_best_action = 'Introduce liquidity benefits on Premier Loan accounts',
  } = prospect

  // Custom channels, urgency, product match, and messaging angles based on intent
  const nextProduct = conversion_band === 'high' ? 'Premier Personal Loan' :
                      conversion_band === 'medium' ? 'Standard Personal Loan' : 'Pre-approved Credit Card'
                      
  const nextChannel = conversion_band === 'high' ? '💬 WhatsApp / Secured Portal' :
                      conversion_band === 'medium' ? '📧 Professional Email' : '📱 Marketing SMS'

  const messageAngle = conversion_band === 'high' ? 'Liquidity Preservation for high-value renovations.' :
                        conversion_band === 'medium' ? 'Tax benefit consolidation & emergency liquidity reserves.' : 
                        'Revolving benefits & high credit limits.'

  const urgency = conversion_band === 'high' ? 'CRITICAL (Next 24h)' :
                  conversion_band === 'medium' ? 'MEDIUM (Next 3d)' : 'LOW (General campaign)'

  return (
    <div className="glass-panel p-5 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white relative shadow-md overflow-hidden transition-transform duration-150 active:scale-[0.99] border-none">
      {/* Decorative pulse glow */}
      <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full blur-xl translate-x-8 -translate-y-8 animate-pulse" />

      {/* Title block */}
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-white/10 backdrop-blur-md">
          <Rocket size={14} className="text-white" />
        </div>
        <h4 className="text-[10px] font-bold uppercase tracking-widest text-blue-100">
          Next Best Action
        </h4>
        <span className={clsx(
          'ml-auto text-[9px] font-bold px-2 py-0.5 rounded-full backdrop-blur-md border border-white/20',
          conversion_band === 'high' ? 'bg-emerald-500/20 text-emerald-300' :
          conversion_band === 'medium' ? 'bg-amber-500/20 text-amber-300' : 'bg-white/10 text-slate-300'
        )}>
          {urgency}
        </span>
      </div>

      {/* Content grid */}
      <div className="space-y-3.5 mb-4">
        <div>
          <p className="text-[10px] text-blue-200 font-medium">Recommended Product</p>
          <p className="text-sm font-bold text-white tracking-tight mt-0.5 flex items-center gap-1.5">
            {nextProduct}
            <Sparkles size={11} className="text-amber-300 animate-pulse" />
          </p>
        </div>

        <div className="p-3 bg-white/10 rounded-xl border border-white/5 backdrop-blur-sm">
          <div className="flex items-center gap-1.5 text-[10px] text-blue-200 font-bold mb-1.5">
            <MessageSquareCode size={12} className="text-emerald-300" />
            Channel: {nextChannel}
          </div>
          <p className="text-[11px] text-slate-100 leading-relaxed italic">
            "{messageAngle}"
          </p>
        </div>
      </div>

      {/* Button CTA */}
      <button
        onClick={onExecuteOutreach}
        className="w-full py-2.5 bg-white hover:bg-slate-50 text-blue-700 rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-sm hover:shadow-md hover:scale-[1.01] active:scale-[0.98] transition-all duration-150"
      >
        <span>Execute Outreach</span>
        <span className="text-sm">→</span>
      </button>
    </div>
  )
}
