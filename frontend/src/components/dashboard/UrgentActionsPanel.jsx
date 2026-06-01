import React from 'react'
import { motion } from 'framer-motion'
import { Phone, MessageSquare, Zap, MapPin, AlertTriangle } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import clsx from 'clsx'

const SIGNAL_ICONS = {
  medical_spend: '🏥',
  stable_salary: '💰',
  high_balance: '🏦',
  education_spend: '🎓',
  renovation_spend: '🏡',
  rising_expenses: '📈',
  emi_paying: '📋',
  default: '📊',
}

function getTopSignalLabel(signals = []) {
  if (!signals.length) return null
  const signal = signals[0]
  const icon = SIGNAL_ICONS[signal] || SIGNAL_ICONS.default
  return `${icon} ${signal.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}`
}

export default function UrgentActionsPanel({ prospects = [], loading }) {
  const { openClientPortal } = useApp()
  const highPriority = prospects
    .filter((p) => p.conversion_band === 'high')
    .slice(0, 5)

  if (loading) {
    return (
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <h3 className="text-sm font-semibold text-slate-900">Urgent Actions</h3>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 shimmer rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (highPriority.length === 0) {
    return (
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 rounded-full bg-slate-300" />
          <h3 className="text-sm font-semibold text-slate-900">Urgent Actions</h3>
        </div>
        <div className="text-center py-6">
          <Zap size={24} className="text-slate-300 mx-auto mb-2" />
          <p className="text-sm text-slate-400">No urgent actions right now</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-3.5 border-b border-slate-100 bg-gradient-to-r from-red-50 to-orange-50">
        <div className="flex items-center gap-1.5">
          <AlertTriangle size={14} className="text-red-500" />
          <h3 className="text-sm font-semibold text-slate-900">Urgent Actions</h3>
        </div>
        <span className="ml-auto bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
          {highPriority.length}
        </span>
      </div>

      <div className="p-3 space-y-2">
        {highPriority.map((prospect, i) => {
          const topSignal = getTopSignalLabel(prospect.positive_signals)
          return (
            <motion.div
              key={prospect.customer_id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06 }}
              className="priority-border-high bg-white rounded-xl p-3.5 shadow-sm border border-slate-100 hover:shadow-md transition-shadow cursor-pointer group"
              onClick={() => openClientPortal(prospect.customer_id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-sm font-semibold text-slate-900 truncate">
                      {prospect.full_name}
                    </span>
                    <span className="badge-high text-xs shrink-0">
                      {prospect.readiness_score}
                    </span>
                  </div>
                  {topSignal && (
                    <div className="text-xs text-slate-500 mb-1.5 flex items-center gap-1">
                      <MapPin size={10} className="shrink-0" />
                      {prospect.city}
                      <span className="mx-1">·</span>
                      {topSignal}
                    </div>
                  )}
                  {prospect.next_best_action && (
                    <div className="text-xs text-emerald-700 font-medium">
                      {prospect.next_best_action}
                    </div>
                  )}
                </div>
                <button
                  className="shrink-0 flex items-center gap-1 px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                  onClick={(e) => {
                    e.stopPropagation()
                    openClientPortal(prospect.customer_id)
                  }}
                >
                  <Zap size={11} />
                  Act
                </button>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
