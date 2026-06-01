import React from 'react'
import { MessageSquare, CheckCircle, AlertCircle, Loader, Send, Edit3, History } from 'lucide-react'
import clsx from 'clsx'

const TONES = [
  { value: 'friendly', label: '😊 Friendly' },
  { value: 'professional', label: '💼 Professional' },
  { value: 'urgent', label: '⚡ Urgent' },
  { value: 'empathetic', label: '🤝 Empathetic' },
]

const CHANNELS = [
  { value: 'whatsapp', label: '💬 WhatsApp' },
  { value: 'email', label: '📧 Email' },
  { value: 'sms', label: '📱 SMS' },
  { value: 'call', label: '📞 Call Script' },
]

const PRODUCT_TYPES = [
  { value: 'personal_loan', label: 'Personal Loan' },
  { value: 'home_loan', label: 'Home Loan' },
  { value: 'auto_loan', label: 'Auto Loan' },
  { value: 'credit_card', label: 'Credit Card' },
]

export default function OutreachPanel({ customer, messageState, onGenerate, onApprove, onConfigChange, onTextChange }) {
  const cust = customer?.customer || customer || {}
  const outreachHistory = customer?.outreach_history || []

  const {
    tone, channel, productType,
    generating, generated, editedText, approving, approved, error, outreachId,
  } = messageState

  return (
    <div className="space-y-5">
      {/* Config row */}
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Product</label>
          <select
            value={productType}
            onChange={(e) => onConfigChange('productType', e.target.value)}
            className="w-full px-2.5 py-1.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {PRODUCT_TYPES.map(pt => <option key={pt.value} value={pt.value}>{pt.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Tone</label>
          <select
            value={tone}
            onChange={(e) => onConfigChange('tone', e.target.value)}
            className="w-full px-2.5 py-1.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {TONES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Channel</label>
          <select
            value={channel}
            onChange={(e) => onConfigChange('channel', e.target.value)}
            className="w-full px-2.5 py-1.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {CHANNELS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
      </div>

      {/* Generate button */}
      <button
        onClick={onGenerate}
        disabled={generating || approved}
        className={clsx(
          'w-full inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all',
          generating
            ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
            : approved
            ? 'bg-emerald-100 text-emerald-700 cursor-default'
            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md'
        )}
      >
        {generating ? (
          <><Loader size={16} className="animate-spin" />Generating message…</>
        ) : approved ? (
          <><CheckCircle size={16} />Message Sent Successfully!</>
        ) : (
          <><MessageSquare size={16} />Generate {channel.charAt(0).toUpperCase() + channel.slice(1)} Message</>
        )}
      </button>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle size={14} className="text-red-500 shrink-0" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* Generated message editor */}
      {generated && !approved && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 text-sm font-semibold text-slate-700">
              <Edit3 size={14} className="text-blue-500" />
              Generated Message
            </div>
            <span className="text-xs text-slate-400">Editable before sending</span>
          </div>
          <textarea
            value={editedText}
            onChange={(e) => onTextChange(e.target.value)}
            rows={6}
            className="w-full px-4 py-3 text-sm border border-slate-200 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white resize-none leading-relaxed"
          />
          <div className="flex items-center gap-3 mt-3">
            <button
              onClick={onGenerate}
              disabled={generating}
              className="btn-secondary text-xs"
            >
              <MessageSquare size={12} />
              Regenerate
            </button>
            <button
              onClick={onApprove}
              disabled={approving || !outreachId}
              className="btn-primary flex-1 justify-center"
            >
              {approving ? (
                <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Approving…</>
              ) : (
                <><Send size={14} />Approve & Send</>
              )}
            </button>
          </div>
          {!outreachId && (
            <p className="text-xs text-slate-400 mt-1">
              Note: Message approval requires a valid outreach ID from the backend.
            </p>
          )}
        </div>
      )}

      {/* Approved confirmation */}
      {approved && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
          <CheckCircle size={24} className="text-emerald-500 mx-auto mb-2" />
          <div className="text-sm font-semibold text-emerald-700">Message Approved & Queued</div>
          <div className="text-xs text-emerald-600 mt-1">
            The {channel} message to {cust.full_name || 'this customer'} has been approved and will be sent shortly.
          </div>
        </div>
      )}

      {/* Outreach History */}
      {outreachHistory.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 text-sm font-semibold text-slate-700 mb-3">
            <History size={14} className="text-slate-500" />
            Outreach History
          </div>
          <div className="space-y-2">
            {outreachHistory.slice(0, 5).map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 border border-slate-100 rounded-lg">
                <div className="shrink-0 mt-0.5">
                  {item.status === 'sent' ? (
                    <CheckCircle size={13} className="text-emerald-500" />
                  ) : (
                    <MessageSquare size={13} className="text-slate-400" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium text-slate-700 truncate">
                    {item.message_text || item.message || 'Message sent'}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {item.channel || 'whatsapp'} · {item.sent_at || item.created_at
                      ? new Date(item.sent_at || item.created_at).toLocaleDateString()
                      : '—'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No history empty state */}
      {outreachHistory.length === 0 && !generated && (
        <div className="text-center py-8 border border-dashed border-slate-200 rounded-xl">
          <MessageSquare size={28} className="text-slate-300 mx-auto mb-2" />
          <p className="text-sm text-slate-500">No outreach history</p>
          <p className="text-xs text-slate-400 mt-0.5">Generate and send your first message above</p>
        </div>
      )}
    </div>
  )
}
