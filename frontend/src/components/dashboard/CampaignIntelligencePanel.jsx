import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Megaphone, Plus, CheckCircle, Play, RefreshCw, X, AlertCircle } from 'lucide-react'
import { approveCampaign, createCampaign, runBulkOutreach } from '../../api/client'
import CampaignCard from '../campaigns/CampaignCard'
import { CampaignCardSkeleton } from '../shared/LoadingSkeleton'
import CampaignApprovalModal from '../campaigns/CampaignApprovalModal'
import clsx from 'clsx'

export default function CampaignIntelligencePanel({ campaigns = [], loading, onRefresh }) {
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [approvalModal, setApprovalModal] = useState(null)
  const [approvingId, setApprovingId] = useState(null)
  const [runningOutreach, setRunningOutreach] = useState(false)

  const handleApprove = async (campaignId) => {
    setApprovingId(campaignId)
    try {
      await approveCampaign(campaignId)
      onRefresh && onRefresh()
    } catch (err) {
      console.error('Failed to approve campaign:', err)
    } finally {
      setApprovingId(null)
    }
  }

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Megaphone size={15} className="text-white" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Campaigns</h2>
            <p className="text-xs text-slate-400">{campaigns.length} total · {campaigns.filter(c => c.status === 'active').length} active</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onRefresh} className="btn-ghost">
            <RefreshCw size={13} />
          </button>
          <button onClick={() => setCreateModalOpen(true)} className="btn-primary">
            <Plus size={14} />
            New Campaign
          </button>
        </div>
      </div>

      {/* Campaigns list */}
      <div className="p-4">
        {loading ? (
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => <CampaignCardSkeleton key={i} />)}
          </div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-10">
            <Megaphone size={32} className="text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No campaigns yet</p>
            <p className="text-slate-400 text-sm mt-1">Create your first outreach campaign</p>
            <button onClick={() => setCreateModalOpen(true)} className="btn-primary mt-4">
              <Plus size={14} />
              Create Campaign
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {campaigns.map((campaign) => (
              <CampaignCard
                key={campaign.campaign_id || campaign.id}
                campaign={campaign}
                approvingId={approvingId}
                onApprove={handleApprove}
                onRunOutreach={() => setApprovalModal(campaign)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Campaign Modal */}
      <AnimatePresence>
        {createModalOpen && (
          <CreateCampaignModal
            onClose={() => setCreateModalOpen(false)}
            onCreated={() => { setCreateModalOpen(false); onRefresh && onRefresh() }}
          />
        )}
      </AnimatePresence>

      {/* Approval Modal */}
      <AnimatePresence>
        {approvalModal && (
          <CampaignApprovalModal
            campaign={approvalModal}
            onClose={() => setApprovalModal(null)}
            onApproved={() => { setApprovalModal(null); onRefresh && onRefresh() }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

function CreateCampaignModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    campaign_name: '',
    product_type: 'personal_loan',
    segment_name: 'high_intent',
    target_count: 10,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const PRODUCT_TYPES = [
    { value: 'personal_loan', label: 'Personal Loan' },
    { value: 'home_loan', label: 'Home Loan' },
    { value: 'auto_loan', label: 'Auto Loan' },
    { value: 'credit_card', label: 'Credit Card' },
    { value: 'business_loan', label: 'Business Loan' },
  ]

  const SEGMENTS = [
    { value: 'high_intent', label: 'High Intent' },
    { value: 'medical_spend', label: 'Medical Spenders' },
    { value: 'high_balance', label: 'High Balance' },
    { value: 'no_loan', label: 'No Existing Loan' },
    { value: 'rising_expenses', label: 'Rising Expenses' },
  ]

  const handleSubmit = async () => {
    if (!form.campaign_name.trim()) { setError('Campaign name is required'); return }
    setLoading(true)
    setError(null)
    try {
      await runBulkOutreach({
        campaign_name: form.campaign_name.trim(),
        product_type: form.product_type,
        target_count: Number(form.target_count),
      })
      onCreated()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900">Create Campaign</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400">
            <X size={18} />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Campaign Name</label>
            <input
              type="text"
              value={form.campaign_name}
              onChange={(e) => setForm(p => ({ ...p, campaign_name: e.target.value }))}
              placeholder="e.g. Q1 Personal Loan Drive"
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Product Type</label>
            <select
              value={form.product_type}
              onChange={(e) => setForm(p => ({ ...p, product_type: e.target.value }))}
              className="input-field"
            >
              {PRODUCT_TYPES.map(pt => <option key={pt.value} value={pt.value}>{pt.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Target Segment</label>
            <select
              value={form.segment_name}
              onChange={(e) => setForm(p => ({ ...p, segment_name: e.target.value }))}
              className="input-field"
            >
              {SEGMENTS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Target Count <span className="text-slate-400 font-normal">(prospects)</span>
            </label>
            <input
              type="number"
              value={form.target_count}
              onChange={(e) => setForm(p => ({ ...p, target_count: e.target.value }))}
              min={1}
              max={100}
              className="input-field"
            />
          </div>
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle size={14} className="text-red-500 shrink-0" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
        </div>
        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button onClick={handleSubmit} disabled={loading} className="btn-primary flex-1 justify-center">
            {loading ? (
              <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Creating...</>
            ) : (
              <><Play size={14} />Create & Run</>
            )}
          </button>
        </div>
      </motion.div>
    </div>
  )
}
