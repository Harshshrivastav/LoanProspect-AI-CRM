import React, { useEffect, useState } from 'react'
import clsx from 'clsx'

export default function ConfidenceMeter({ confidence = 0, label = 'Confidence', showPercent = true, compact = false }) {
  const pct = Math.round((confidence <= 1 ? confidence * 100 : confidence))
  const [animatedWidth, setAnimatedWidth] = useState(0)

  useEffect(() => {
    const t = setTimeout(() => setAnimatedWidth(pct), 150)
    return () => clearTimeout(t)
  }, [pct])

  const color =
    pct >= 70 ? 'bg-emerald-500' :
    pct >= 45 ? 'bg-amber-500' :
    'bg-red-500'

  const textColor =
    pct >= 70 ? 'text-emerald-600' :
    pct >= 45 ? 'text-amber-600' :
    'text-red-600'

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={clsx(color, 'h-full rounded-full transition-all duration-700 ease-out')}
            style={{ width: `${animatedWidth}%` }}
          />
        </div>
        <span className={clsx('text-xs font-semibold tabular-nums', textColor)}>{pct}%</span>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-slate-500 font-medium">{label}</span>
        {showPercent && (
          <span className={clsx('text-sm font-bold tabular-nums', textColor)}>{pct}%</span>
        )}
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={clsx(color, 'h-full rounded-full transition-all duration-700 ease-out')}
          style={{ width: `${animatedWidth}%` }}
        />
      </div>
    </div>
  )
}
