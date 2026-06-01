import React from 'react'
import { ShieldCheck, ShieldAlert, AlertTriangle, Info } from 'lucide-react'
import clsx from 'clsx'

export default function ComplianceBanner({ status = 'compliant', message, compact = false }) {
  const configs = {
    compliant: {
      icon: ShieldCheck,
      bg: 'bg-emerald-50',
      border: 'border-emerald-200',
      text: 'text-emerald-700',
      iconColor: 'text-emerald-500',
      label: 'Compliant',
    },
    blocked: {
      icon: ShieldAlert,
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-700',
      iconColor: 'text-red-500',
      label: 'Blocked',
    },
    warning: {
      icon: AlertTriangle,
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-700',
      iconColor: 'text-amber-500',
      label: 'Warning',
    },
    info: {
      icon: Info,
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-700',
      iconColor: 'text-blue-500',
      label: 'Info',
    },
  }

  const cfg = configs[status] || configs.compliant
  const Icon = cfg.icon

  if (compact) {
    return (
      <span
        className={clsx(
          'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border',
          cfg.bg, cfg.border, cfg.text
        )}
      >
        <Icon size={10} className={cfg.iconColor} />
        {cfg.label}
      </span>
    )
  }

  return (
    <div className={clsx('flex items-start gap-2.5 p-3 rounded-lg border', cfg.bg, cfg.border)}>
      <Icon size={15} className={clsx(cfg.iconColor, 'mt-0.5 shrink-0')} />
      <div className="min-w-0">
        <div className={clsx('text-sm font-semibold', cfg.text)}>{cfg.label}</div>
        {message && <div className={clsx('text-xs mt-0.5', cfg.text, 'opacity-80')}>{message}</div>}
      </div>
    </div>
  )
}
