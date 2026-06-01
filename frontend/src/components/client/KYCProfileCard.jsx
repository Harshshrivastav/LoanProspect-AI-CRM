import React from 'react'
import { Calendar, MapPin, Briefcase, Phone, Mail, CheckCircle2, ShieldAlert, Award } from 'lucide-react'
import clsx from 'clsx'

function getInitials(name = '') {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

function getAvatarColor(name = '') {
  const colors = [
    'bg-gradient-to-br from-blue-500 to-indigo-600',
    'bg-gradient-to-br from-purple-500 to-pink-600',
    'bg-gradient-to-br from-emerald-500 to-teal-600',
    'bg-gradient-to-br from-amber-500 to-orange-600',
    'bg-gradient-to-br from-rose-500 to-red-600',
  ]
  const idx = name ? (name.charCodeAt(0) || 0) % colors.length : 0
  return colors[idx]
}

function formatCurrency(amount) {
  if (!amount) return '—'
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(0)}K`
  return `₹${amount}`
}

const RISK_CONFIG = {
  low: { label: 'Low Risk Segment', classes: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
  medium: { label: 'Medium Risk Segment', classes: 'bg-amber-50 text-amber-700 border-amber-100' },
  high: { label: 'High Risk Segment', classes: 'bg-rose-50 text-rose-700 border-rose-100' },
}

export default function KYCProfileCard({ customer, prospect }) {
  if (!customer) return null
  const cust = customer.customer || customer
  const initials = getInitials(cust.full_name || cust.name || '')
  const avatarColor = getAvatarColor(cust.full_name || '')
  const riskCfg = RISK_CONFIG[cust.risk_segment] || RISK_CONFIG.medium

  const accounts = customer.accounts || []
  const primaryAccount = accounts[0]

  return (
    <div className="space-y-4">
      {/* Profile Card Summary */}
      <div className="card p-5 bg-white border-slate-100 relative overflow-hidden active-glow flex flex-col items-center text-center">
        {/* Avatar block with green verification checkmark */}
        <div className="relative mb-3.5">
          <div className={clsx('w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-black shadow-md border-2 border-white', avatarColor)}>
            {initials}
          </div>
          {cust.kyc_status === 'verified' && (
            <div className="absolute bottom-0 right-0 bg-white rounded-full p-0.5 shadow-md border border-slate-100">
              <CheckCircle2 size={18} className="text-[#00c853] fill-[#00c853] text-white" style={{ strokeWidth: 3 }} />
            </div>
          )}
        </div>

        <h3 className="text-base font-bold text-slate-800 tracking-tight leading-snug">
          {cust.full_name || cust.name}
        </h3>
        <p className="text-[10px] font-mono text-slate-400 mt-0.5 uppercase tracking-wider">
          ID: {cust.customer_id}
        </p>

        {/* Badges row */}
        <div className="flex flex-wrap gap-1.5 justify-center mt-3.5">
          <span className={clsx('px-2.5 py-0.5 rounded-full text-[9px] font-bold border uppercase tracking-wider', riskCfg.classes)}>
            {riskCfg.label}
          </span>
          {cust.consent_marketing ? (
            <span className="px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-100 rounded-full text-[9px] font-bold uppercase tracking-wider">
              ✓ Contact Consent
            </span>
          ) : (
            <span className="px-2 py-0.5 bg-slate-50 text-slate-400 border border-slate-100 rounded-full text-[9px] font-bold uppercase tracking-wider">
              ✖ No Consent
            </span>
          )}
        </div>

        {/* Profile Info Attributes */}
        <div className="mt-5 w-full text-left space-y-2.5 pt-4 border-t border-slate-100">
          <div className="flex items-center justify-between text-xs py-0.5">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Calendar size={13} /> Age
            </span>
            <span className="font-semibold text-slate-700">{cust.age} yrs</span>
          </div>

          <div className="flex items-center justify-between text-xs py-0.5">
            <span className="text-slate-400 flex items-center gap-1.5">
              <MapPin size={13} /> Location
            </span>
            <span className="font-semibold text-slate-700">{cust.city}</span>
          </div>

          <div className="flex items-center justify-between text-xs py-0.5">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Briefcase size={13} /> Occupation
            </span>
            <span className="font-semibold text-slate-700 text-right truncate max-w-[120px]" title={cust.occupation}>
              {cust.occupation}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs py-0.5">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Award size={13} /> Employment
            </span>
            <span className="font-semibold text-slate-700 capitalize">{cust.employment_type || 'Salaried'}</span>
          </div>

          <div className="flex items-center justify-between text-xs py-0.5">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Phone size={13} /> Contact
            </span>
            <span className="font-semibold text-slate-700 font-mono text-[11px]">{cust.phone}</span>
          </div>

          <div className="flex items-center justify-between text-xs py-0.5">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Mail size={13} /> Email
            </span>
            <span className="font-semibold text-slate-700 text-[10px] truncate max-w-[120px]" title={cust.email}>
              {cust.email}
            </span>
          </div>
        </div>
      </div>

      {/* Account Relationship Tenure and RM */}
      <div className="card p-4 bg-slate-50/50 border-slate-100 flex flex-col gap-2">
        <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2 mb-1">
          <span>Dossier Metadata</span>
        </div>
        
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-400">Account Tenure</span>
          <span className="font-semibold text-slate-700">
            {cust.account_tenure_months ? `${Math.floor(cust.account_tenure_months / 12)}y ${cust.account_tenure_months % 12}m` : '—'}
          </span>
        </div>

        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-400">Assigned RM</span>
          <span className="font-semibold text-slate-700">{cust.rm_assigned || 'RM-001'}</span>
        </div>

        {cust.last_contact_date && (
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Last Contact</span>
            <span className="font-semibold text-slate-700">{cust.last_contact_date}</span>
          </div>
        )}
      </div>
    </div>
  )
}
