import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'
import clsx from 'clsx'

export default function NotificationToast({ notification, onDismiss }) {
  const { type = 'info', message } = notification

  const configs = {
    success: { icon: CheckCircle, bg: 'bg-emerald-500', iconClass: 'text-white' },
    error: { icon: AlertCircle, bg: 'bg-red-500', iconClass: 'text-white' },
    info: { icon: Info, bg: 'bg-blue-500', iconClass: 'text-white' },
    warning: { icon: AlertCircle, bg: 'bg-amber-500', iconClass: 'text-white' },
  }
  const cfg = configs[type] || configs.info
  const Icon = cfg.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="pointer-events-auto flex items-center gap-3 px-4 py-3 bg-slate-900 text-white rounded-xl shadow-2xl min-w-[280px] max-w-sm"
    >
      <div className={clsx('w-7 h-7 rounded-lg flex items-center justify-center shrink-0', cfg.bg)}>
        <Icon size={14} className={cfg.iconClass} />
      </div>
      <span className="text-sm flex-1">{message}</span>
      <button
        onClick={onDismiss}
        className="text-slate-400 hover:text-white transition-colors shrink-0"
      >
        <X size={14} />
      </button>
    </motion.div>
  )
}
