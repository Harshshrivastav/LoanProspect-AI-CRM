import React, { useEffect, useRef, useState } from 'react'
import clsx from 'clsx'

export function getScoreColor(score) {
  if (score >= 70) return { bar: 'bg-emerald-500', text: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200' }
  if (score >= 45) return { bar: 'bg-amber-500', text: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200' }
  return { bar: 'bg-red-500', text: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' }
}

export default function ScoreBar({ score = 0, label, showNumber = true, height = 'h-2', animate = true, className = '' }) {
  const colors = getScoreColor(score)
  const [width, setWidth] = useState(animate ? 0 : score)
  const mounted = useRef(false)

  useEffect(() => {
    if (!animate) return
    const timeout = setTimeout(() => setWidth(score), 100)
    return () => clearTimeout(timeout)
  }, [score, animate])

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <div className={clsx('flex-1 bg-slate-100 rounded-full overflow-hidden', height)}>
        <div
          className={clsx(colors.bar, height, 'rounded-full transition-all duration-700 ease-out')}
          style={{ width: `${Math.min(100, Math.max(0, width))}%` }}
        />
      </div>
      {showNumber && (
        <span className={clsx('text-xs font-bold tabular-nums min-w-[2.5rem] text-right', colors.text)}>
          {score}
          {label && <span className="text-slate-400 font-normal ml-0.5">{label}</span>}
        </span>
      )}
    </div>
  )
}

export function ScoreCircle({ score = 0, size = 'md' }) {
  const colors = getScoreColor(score)
  const sizes = {
    sm: { outer: 'w-12 h-12', text: 'text-lg', sub: 'text-xs' },
    md: { outer: 'w-20 h-20', text: 'text-2xl', sub: 'text-xs' },
    lg: { outer: 'w-28 h-28', text: 'text-4xl', sub: 'text-sm' },
  }
  const sz = sizes[size] || sizes.md

  // SVG circle stroke
  const radius = size === 'lg' ? 50 : size === 'md' ? 36 : 22
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score / 100) * circumference
  const viewBox = size === 'lg' ? '0 0 120 120' : size === 'md' ? '0 0 80 80' : '0 0 50 50'
  const cx = size === 'lg' ? 60 : size === 'md' ? 40 : 25
  const cy = size === 'lg' ? 60 : size === 'md' ? 40 : 25
  const strokeWidth = size === 'lg' ? 8 : size === 'md' ? 6 : 4

  const strokeColor = score >= 70 ? '#10b981' : score >= 45 ? '#f59e0b' : '#ef4444'

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg viewBox={viewBox} className={sz.outer} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={clsx('font-bold tabular-nums', colors.text, sz.text)}>{score}</span>
        <span className={clsx('text-slate-400', sz.sub)}>/100</span>
      </div>
    </div>
  )
}
