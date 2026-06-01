import React from 'react'
import clsx from 'clsx'

const SIGNAL_ICONS = {
  stable_salary: '💰',
  medical_spend: '🏥',
  no_existing_personal_loan: '✅',
  high_balance: '🏦',
  education_spend: '🎓',
  renovation_spend: '🏡',
  rising_expenses: '📈',
  emi_paying: '📋',
  insurance_spend: '🛡️',
  salary_credit: '💵',
  travel_spend: '✈️',
  default: '📊',
}

export default function SignalChip({ signal, variant = 'positive', small = false }) {
  const isRisk = variant === 'risk'
  const isInfo = variant === 'info'

  const icon = SIGNAL_ICONS[signal] || SIGNAL_ICONS.default
  const label = signal
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full font-medium',
        small ? 'text-xs px-2 py-0.5' : 'text-xs px-2.5 py-1',
        isRisk
          ? 'bg-red-100 text-red-700'
          : isInfo
          ? 'bg-blue-100 text-blue-700'
          : 'bg-emerald-100 text-emerald-700'
      )}
    >
      <span className="text-xs">{icon}</span>
      {label}
    </span>
  )
}

export function SignalList({ signals = [], riskFlags = [], maxVisible = 3, small = false }) {
  const total = signals.length + riskFlags.length
  const showMore = total > maxVisible

  return (
    <div className="flex flex-wrap gap-1">
      {signals.slice(0, maxVisible).map((s) => (
        <SignalChip key={s} signal={s} variant="positive" small={small} />
      ))}
      {riskFlags.slice(0, Math.max(0, maxVisible - signals.length)).map((r) => (
        <SignalChip key={r} signal={r} variant="risk" small={small} />
      ))}
      {showMore && (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-500 font-medium">
          +{total - maxVisible} more
        </span>
      )}
    </div>
  )
}
