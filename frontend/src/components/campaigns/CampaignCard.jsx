import React from 'react'
import { CheckCircle, Play, Users, Package, Calendar, BarChart } from 'lucide-react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  draft: { label: 'Draft', classes: 'bg-slate-100 text-slate-600', dot: 'bg-slate-400' },
  active: { label: 'Active', classes: 'bg-blue-100 text-blue-700', dot: 'bg-blue-500' },
  completed: { label: 'Completed', classes: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500' },
  paused: { label: 'Paused', classes: 'bg-amber-100 text-amber-700', dot: 'bg-amber-500' },
  running: { label: 'Running', classes: 'bg-indigo-100 text-indigo-700', dot: 'bg-indigo-500' },
}

const PRODUCT_LABELS = {
  personal_loan: '💳 Personal Loan',
  home_loan: '🏠 Home Loan',
  auto_loan: '🚗 Auto Loan',
  credit_card: '💳 Credit Card',
  business_loan: '🏢 Business Loan',
}

export default function CampaignCard({ campaign, approvingId, onApprove, onRunOutreach }) {
  const campaignId = campaign.campaign_id || campaign.id
  const status = campaign.status || 'draft'
  const statusCfg = STATUS_CONFIG[status] || STATUS_CONFIG.draft
  const isApproving = approvingId === campaignId

  const targetCount = campaign.target_count || campaign.target_customer_ids?.length || 0
  const successCount = campaign.success_count || 0
  const progressPct = targetCount > 0 ? Math.round((successCount / targetCount) * 100) : 0

  const createdAt = campaign.created_at
    ? new Date(campaign.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
    : null

  return (
    <div className="bg-white border border-slate-100 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-slate-900 truncate">
            {campaign.campaign_name || campaign.name || 'Unnamed Campaign'}
          </h3>
          <div className="text-xs text-slate-500 mt-0.5">
            {PRODUCT_LABELS[campaign.product_type] || campaign.product_type}
          </div>
        </div>
        <span className={clsx('inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium shrink-0', statusCfg.classes)}>
          <span className={clsx('w-1.5 h-1.5 rounded-full', statusCfg.dot, status === 'active' && 'animate-pulse')} />
          {statusCfg.label}
        </span>
      </div>

      {/* Metrics */}
      <div className="flex items-center gap-4 mb-3">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Users size={11} className="text-slate-400" />
          <span className="font-medium text-slate-700">{targetCount}</span> targets
        </div>
        {successCount > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <CheckCircle size={11} className="text-emerald-400" />
            <span className="font-medium text-emerald-600">{successCount}</span> sent
          </div>
        )}
        {createdAt && (
          <div className="flex items-center gap-1.5 text-xs text-slate-400 ml-auto">
            <Calendar size={10} />
            {createdAt}
          </div>
        )}
      </div>

      {/* Progress bar */}
      {targetCount > 0 && (
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-slate-400">Progress</span>
            <span className="text-xs font-medium text-slate-600">{progressPct}%</span>
          </div>
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={clsx(
                'h-full rounded-full transition-all duration-700',
                progressPct >= 100 ? 'bg-emerald-500' :
                progressPct > 0 ? 'bg-blue-500' : 'bg-slate-300'
              )}
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        {status === 'draft' && (
          <button
            onClick={() => onApprove(campaignId)}
            disabled={isApproving}
            className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-60"
          >
            {isApproving ? (
              <><span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />Approving...</>
            ) : (
              <><CheckCircle size={12} />Approve</>
            )}
          </button>
        )}
        <button
          onClick={() => onRunOutreach && onRunOutreach(campaign)}
          className={clsx(
            'inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
            status === 'draft' ? 'flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700' : 'w-full bg-blue-600 hover:bg-blue-700 text-white'
          )}
        >
          <Play size={12} />
          {status === 'draft' ? 'Preview' : 'Details'}
        </button>
      </div>

      {/* Expected outcome */}
      {campaign.expected_conversion_rate && (
        <div className="mt-2.5 flex items-center gap-1.5 text-xs text-slate-400">
          <BarChart size={10} />
          Expected conversion: {Math.round(campaign.expected_conversion_rate * 100)}%
        </div>
      )}
    </div>
  )
}
