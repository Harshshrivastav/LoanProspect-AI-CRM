import React from 'react'
import { motion } from 'framer-motion'
import { Users, TrendingUp, Target, Megaphone, Clock, ArrowUpRight } from 'lucide-react'
import { KPICardSkeleton } from '../shared/LoadingSkeleton'
import clsx from 'clsx'

function KPICard({ title, value, subtitle, icon: Icon, color, trend, delay = 0 }) {
  const colorMap = {
    blue: {
      bg: 'bg-blue-50',
      iconBg: 'bg-blue-600',
      text: 'text-blue-700',
      value: 'text-blue-900',
    },
    emerald: {
      bg: 'bg-emerald-50',
      iconBg: 'bg-emerald-600',
      text: 'text-emerald-700',
      value: 'text-emerald-900',
    },
    amber: {
      bg: 'bg-amber-50',
      iconBg: 'bg-amber-500',
      text: 'text-amber-700',
      value: 'text-amber-900',
    },
    indigo: {
      bg: 'bg-indigo-50',
      iconBg: 'bg-indigo-600',
      text: 'text-indigo-700',
      value: 'text-indigo-900',
    },
    rose: {
      bg: 'bg-rose-50',
      iconBg: 'bg-rose-500',
      text: 'text-rose-700',
      value: 'text-rose-900',
    },
  }
  const c = colorMap[color] || colorMap.blue

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="card p-5 hover:shadow-md transition-shadow duration-200"
    >
      <div className="flex items-start justify-between mb-3">
        <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center', c.iconBg)}>
          <Icon size={18} className="text-white" />
        </div>
        {trend !== undefined && (
          <div className="flex items-center gap-1 text-emerald-600 text-xs font-medium">
            <ArrowUpRight size={13} />
            {trend}%
          </div>
        )}
      </div>
      <div className={clsx('text-3xl font-bold tabular-nums mb-0.5', c.value)}>
        {value}
      </div>
      <div className="text-sm font-medium text-slate-700">{title}</div>
      {subtitle && <div className="text-xs text-slate-400 mt-0.5">{subtitle}</div>}
    </motion.div>
  )
}

export default function KPICards({ prospects = [], campaigns = [], loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => <KPICardSkeleton key={i} />)}
      </div>
    )
  }

  const total = prospects.length
  const high = prospects.filter((p) => p.conversion_band === 'high').length
  const medium = prospects.filter((p) => p.conversion_band === 'medium').length
  const activeCampaigns = (campaigns || []).filter((c) => c.status === 'active').length
  const pendingApprovals = (campaigns || []).filter((c) => c.status === 'draft').length

  const cards = [
    {
      title: 'Total Prospects',
      value: total,
      subtitle: 'Scored this cycle',
      icon: Users,
      color: 'blue',
      delay: 0,
    },
    {
      title: 'High Intent',
      value: high,
      subtitle: 'Score ≥ 70 — Act now',
      icon: TrendingUp,
      color: 'emerald',
      trend: high > 0 ? Math.round((high / total) * 100) : 0,
      delay: 0.05,
    },
    {
      title: 'Medium Intent',
      value: medium,
      subtitle: 'Score 45–69 — Nurture',
      icon: Target,
      color: 'amber',
      delay: 0.1,
    },
    {
      title: 'Active Campaigns',
      value: activeCampaigns,
      subtitle: 'Running outreach',
      icon: Megaphone,
      color: 'indigo',
      delay: 0.15,
    },
    {
      title: 'Pending Approvals',
      value: pendingApprovals,
      subtitle: 'Awaiting your review',
      icon: Clock,
      color: 'rose',
      delay: 0.2,
    },
  ]

  return (
    <div className="grid grid-cols-5 gap-4">
      {cards.map((card) => (
        <KPICard key={card.title} {...card} />
      ))}
    </div>
  )
}
