import React from 'react'
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

const STATUS_THEMES = {
  verified: {
    bg: 'bg-emerald-50 border-emerald-100',
    text: 'text-emerald-800',
    accentText: 'text-emerald-600',
    icon: ShieldCheck,
    label: 'KYC Verified & Compliant',
  },
  pending: {
    bg: 'bg-amber-50 border-amber-100',
    text: 'text-amber-800',
    accentText: 'text-amber-600',
    icon: AlertTriangle,
    label: 'KYC Verification Pending',
  },
  rejected: {
    bg: 'bg-rose-50 border-rose-100',
    text: 'text-rose-800',
    accentText: 'text-rose-600',
    icon: ShieldAlert,
    label: 'KYC Rejected / Action Required',
  },
}

export default function ComplianceStatusBanner({ customer, compact = false }) {
  if (!customer) return null
  const cust = customer.customer || customer
  
  const status = cust.kyc_status || 'pending'
  const theme = STATUS_THEMES[status] || STATUS_THEMES.pending
  const Icon = theme.icon

  if (compact) {
    return (
      <span className={clsx(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border',
        status === 'verified' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
        status === 'pending' ? 'bg-amber-50 text-amber-700 border-amber-200' :
        'bg-red-50 text-red-700 border-red-200'
      )}>
        <Icon size={11} className="shrink-0" />
        {status === 'verified' ? 'Compliant' : status === 'pending' ? 'KYC Pending' : 'Non-Compliant'}
      </span>
    )
  }

  return (
    <div className={clsx('flex items-start gap-3 p-3.5 rounded-xl border transition-all duration-200', theme.bg)}>
      <div className={clsx('p-1.5 rounded-lg bg-white shadow-sm shrink-0', theme.accentText)}>
        <Icon size={16} />
      </div>
      <div className="flex-1 min-w-0">
        <h4 className={clsx('text-xs font-bold uppercase tracking-wider', theme.accentText)}>
          {theme.label}
        </h4>
        <p className={clsx('text-xs mt-0.5 leading-relaxed', theme.text)}>
          {status === 'verified' 
            ? 'Verified identity details matching regulatory compliance registries. General marketing consent is active.'
            : status === 'pending'
            ? 'RM action is required. Please recheck documents or prompt the client for update.'
            : 'Identity verification failed. Account restrictions have been applied until resolving documents.'
          }
        </p>
        <div className="flex items-center gap-4 mt-2 text-[10px] font-semibold">
          <span className={clsx('flex items-center gap-1', cust.consent_marketing ? theme.accentText : 'text-slate-400')}>
            <span>●</span> Marketing Consent: {cust.consent_marketing ? 'ACTIVE' : 'DECLINED'}
          </span>
          <span className="text-slate-400">
            Assigned RM: {cust.rm_assigned || 'RM-001'}
          </span>
        </div>
      </div>
    </div>
  )
}
