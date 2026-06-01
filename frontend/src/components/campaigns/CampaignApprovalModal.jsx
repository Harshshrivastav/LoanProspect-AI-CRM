import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { X, CheckCircle, Users, Package, AlertCircle, Play } from 'lucide-react'
import { approveCampaign } from '../../api/client'

export default function CampaignApprovalModal({ campaign, onClose, onApproved }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const campaignId = campaign.campaign_id || campaign.id

  const handleApprove = async () => {
    setLoading(true)
    setError(null)
    try {
      await approveCampaign(campaignId)
      onApproved && onApproved()
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const targetCount = campaign.target_count || campaign.target_customer_ids?.length || 0

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
          <h2 className="text-base font-semibold text-slate-900">Campaign Details</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Campaign Info */}
          <div className="p-4 bg-slate-50 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Campaign Name</span>
              <span className="text-sm font-semibold text-slate-900">{campaign.campaign_name || campaign.name}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Product</span>
              <span className="text-sm text-slate-700">{campaign.product_type}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Target Customers</span>
              <span className="text-sm font-semibold text-blue-600">{targetCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Status</span>
              <span className="text-sm capitalize text-slate-700">{campaign.status}</span>
            </div>
          </div>

          {campaign.status === 'draft' && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-xs text-amber-700">
                Approving this campaign will enable outreach to {targetCount} customers.
                This action cannot be undone.
              </p>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle size={14} className="text-red-500 shrink-0" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
        </div>

        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose} className="btn-secondary flex-1">Close</button>
          {campaign.status === 'draft' && (
            <button onClick={handleApprove} disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? (
                <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Approving...</>
              ) : (
                <><CheckCircle size={14} />Approve Campaign</>
              )}
            </button>
          )}
        </div>
      </motion.div>
    </div>
  )
}
