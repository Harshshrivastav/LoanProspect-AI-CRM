import React from 'react'
import { Sparkles } from 'lucide-react'

export default function LoanFitFactorChips({ prospect }) {
  if (!prospect) return null
  const fitFactors = prospect.loan_fit_factors || []

  // Fallback factors if database doesn't populate them yet
  const displayFactors = fitFactors.length > 0 ? fitFactors : [
    'Stable Salary Inflow',
    'Growing Spending Trends',
    'Low Current Liabilities',
    'High Digital Touchpoints',
    'Suitable Product Match',
  ]

  return (
    <div className="space-y-2.5">
      <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
        <Sparkles size={11} className="text-blue-500" />
        Fit Diagnostics
      </div>
      <div className="flex flex-wrap gap-1.5">
        {displayFactors.map((factor, i) => (
          <span
            key={i}
            className="px-2.5 py-1 bg-sky-50/60 hover:bg-sky-50 text-sky-700 text-[10px] font-semibold border border-sky-100 rounded-full transition-colors duration-150 shadow-sm"
          >
            {factor}
          </span>
        ))}
      </div>
    </div>
  )
}
