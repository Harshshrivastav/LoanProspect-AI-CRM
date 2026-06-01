import React, { useState, useMemo } from 'react'
import { ArrowRight } from 'lucide-react'
import clsx from 'clsx'

// Default templates shown on a brand-new conversation (no messages yet)
const DEFAULT_TEMPLATES = [
  {
    emoji: '🎯',
    label: 'Top Loan Prospects',
    description: 'Rank customers by personal-loan readiness and surface the top 10 high-intent leads.',
    query: 'Show me the top 10 personal loan prospects ranked by readiness score.',
  },
  {
    emoji: '🏥',
    label: 'High-Value Spenders',
    description: 'Find customers with recent medical, education, or renovation expenses above ₹1 lakh.',
    query: 'Find customers with recent medical or education expenses above ₹1 lakh.',
  },
  {
    emoji: '💬',
    label: 'Draft WhatsApp Outreach',
    description: 'Generate personalized WhatsApp messages for the highest-intent prospects.',
    query: 'Generate personalized WhatsApp messages for the top 5 high-intent prospects.',
  },
  {
    emoji: '📊',
    label: 'Portfolio Overview',
    description: 'Get a snapshot of the entire customer portfolio — segments, risk bands, and product gaps.',
    query: 'Give me a full portfolio overview — how many customers, risk segments, and product gaps.',
  },
]

export default function TemplateSuggestionBar({ templates = null, onSelectTemplate, disabled = false }) {
  const activeTemplates = useMemo(() => {
    const list = templates || DEFAULT_TEMPLATES
    return list.slice(0, 4) // always exactly 4
  }, [templates])

  return (
    <div className="px-4 pb-3 pt-1">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {activeTemplates.map((t) => (
          <button
            key={t.label}
            onClick={() => onSelectTemplate(t.query)}
            disabled={disabled}
            className={clsx(
              'group relative flex flex-col items-start gap-1 px-3.5 py-3 rounded-xl border text-left transition-all duration-200',
              disabled
                ? 'bg-slate-50 border-slate-200/60 text-slate-400 cursor-not-allowed opacity-60'
                : 'bg-white border-slate-200/80 hover:border-blue-300 hover:bg-gradient-to-br hover:from-blue-50/60 hover:to-indigo-50/40 hover:shadow-md hover:shadow-blue-100/40 cursor-pointer'
            )}
          >
            {/* Title row */}
            <div className="flex items-center gap-1.5 w-full">
              <span className="text-base leading-none select-none">{t.emoji}</span>
              <span className={clsx(
                'text-[13px] font-semibold leading-tight truncate',
                disabled ? 'text-slate-400' : 'text-slate-700 group-hover:text-blue-700'
              )}>
                {t.label}
              </span>
            </div>

            {/* Description */}
            <p className={clsx(
              'text-[11px] leading-[1.35] line-clamp-2',
              disabled ? 'text-slate-300' : 'text-slate-400 group-hover:text-slate-500'
            )}>
              {t.description}
            </p>

            {/* Subtle arrow on hover */}
            {!disabled && (
              <ArrowRight
                size={12}
                className="absolute top-3 right-3 text-slate-300 opacity-0 group-hover:opacity-100 group-hover:text-blue-400 transition-all duration-200 group-hover:translate-x-0.5"
              />
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
