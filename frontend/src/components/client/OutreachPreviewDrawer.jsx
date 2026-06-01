import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Trash2, ShieldCheck, CheckCircle2, RotateCw, Sparkles, MessageSquare } from 'lucide-react'
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

export default function OutreachPreviewDrawer({
  isOpen,
  onClose,
  customer,
  messageState,
  onGenerate,
  onApprove,
  onConfigChange,
  onTextChange,
}) {
  if (!isOpen) return null

  const cust = customer?.customer || customer || {}
  const initials = (cust.full_name || '?').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()

  const {
    tone,
    channel,
    productType,
    generating,
    generated,
    editedText,
    approving,
    approved,
    error,
  } = messageState

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex justify-end">
        {/* Dark Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        />

        {/* Slide-over Drawer */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 220 }}
          className="relative w-full max-w-4xl bg-slate-50 flex flex-col h-full shadow-2xl overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200 shrink-0">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                <MessageSquare size={16} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Outreach Workspace</h3>
                <p className="text-[10px] text-slate-400 font-medium">Compose AI communication payloads</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Configuration Banner */}
          <div className="px-6 py-3 bg-white border-b border-slate-100 flex flex-wrap gap-4 items-center shrink-0">
            <div className="flex-1 min-w-[120px]">
              <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">Product</label>
              <select
                value={productType}
                onChange={(e) => onConfigChange('productType', e.target.value)}
                className="w-full px-2.5 py-1 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-700"
              >
                {PRODUCT_TYPES.map(pt => <option key={pt.value} value={pt.value}>{pt.label}</option>)}
              </select>
            </div>
            <div className="flex-1 min-w-[120px]">
              <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">Tone</label>
              <select
                value={tone}
                onChange={(e) => onConfigChange('tone', e.target.value)}
                className="w-full px-2.5 py-1 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-700"
              >
                {TONES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div className="flex-1 min-w-[120px]">
              <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">Channel</label>
              <select
                value={channel}
                onChange={(e) => onConfigChange('channel', e.target.value)}
                className="w-full px-2.5 py-1 text-xs border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-700"
              >
                {CHANNELS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div className="pt-4 flex items-end">
              <button
                onClick={onGenerate}
                disabled={generating || approved}
                className={clsx(
                  'px-4 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all duration-150 uppercase tracking-wider',
                  generating
                    ? 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
                    : approved
                    ? 'bg-emerald-500 text-white border border-emerald-500'
                    : 'bg-blue-600 hover:bg-blue-700 text-white hover:scale-[1.01] active:scale-[0.98]'
                )}
              >
                {generating ? (
                  <><RotateCw size={11} className="animate-spin" />Composing…</>
                ) : approved ? (
                  <><CheckCircle2 size={11} />Approved</>
                ) : (
                  <><Sparkles size={11} />Compose Payload</>
                )}
              </button>
            </div>
          </div>

          {/* Main Dual-Panel Workspace */}
          <div className="flex-1 flex overflow-hidden min-h-0">
            {/* Left Panel: Composer Textarea */}
            <div className="flex-1 flex flex-col p-6 border-r border-slate-200 overflow-y-auto">
              <div className="mb-4">
                <h4 className="text-xs font-bold text-slate-800">Message Refinement</h4>
                <p className="text-[10px] text-slate-400 mt-0.5">Refine and format the generated draft here.</p>
              </div>

              {/* Compliance Note */}
              <div className="flex items-start gap-2 bg-emerald-50 border border-emerald-100 p-3 rounded-xl mb-4">
                <ShieldCheck size={14} className="text-emerald-600 mt-0.5 shrink-0" />
                <div className="min-w-0">
                  <h5 className="text-[10px] font-bold text-emerald-800">Compliance Audit Approved</h5>
                  <p className="text-[9px] text-emerald-600 leading-normal mt-0.5">
                    Checked marketing consent. Opt-out links will be attached automatically on send.
                  </p>
                </div>
              </div>

              {/* Composer text block */}
              <div className="flex-1 bg-white border border-slate-200 rounded-2xl p-4 shadow-inner flex flex-col min-h-[220px]">
                {/* Mock Editor Toolbar */}
                <div className="border-b border-slate-100 pb-2.5 mb-3 flex gap-2 flex-wrap">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded shrink-0">B</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded italic shrink-0">I</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded underline shrink-0">U</span>
                  <div className="w-px h-4 bg-slate-200 my-auto mx-1" />
                  <span className="text-[10px] font-bold px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded shrink-0">🔗 Url</span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded shrink-0">😊 Emoji</span>
                </div>
                
                <textarea
                  value={editedText}
                  onChange={(e) => onTextChange(e.target.value)}
                  disabled={!generated || approved}
                  placeholder="Select variables and click 'Compose Payload' to generate outreach communication drafts..."
                  className="flex-1 w-full bg-transparent border-none focus:ring-0 resize-none text-xs text-slate-700 leading-relaxed focus:outline-none"
                />
              </div>

              {/* Action Rows */}
              {generated && !approved && (
                <div className="flex gap-3 mt-4 shrink-0">
                  <button
                    onClick={onApprove}
                    disabled={approving}
                    className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-2 hover:scale-[1.01] active:scale-[0.98] transition-all"
                  >
                    {approving ? (
                      <><RotateCw size={12} className="animate-spin" />Archiving Audit…</>
                    ) : (
                      <><Send size={12} />Approve & Send Payload</>
                    )}
                  </button>
                  <button
                    onClick={() => onTextChange('')}
                    className="py-2.5 px-3 border border-red-200 hover:bg-red-50 text-red-500 rounded-xl transition-colors"
                    title="Clear draft"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              )}

              {approved && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-center mt-4">
                  <CheckCircle2 size={24} className="text-emerald-500 mx-auto mb-2" />
                  <div className="text-xs font-bold text-emerald-800">Communication Queued</div>
                  <p className="text-[10px] text-emerald-600 leading-normal mt-0.5">
                    The {channel} package was audited and approved. Staged for automated execution.
                  </p>
                </div>
              )}

              {error && (
                <div className="p-3 bg-rose-50 border border-rose-100 text-rose-700 text-[10px] font-semibold leading-normal rounded-xl mt-4">
                  {error}
                </div>
              )}
            </div>

            {/* Right Panel: WhatsApp Phone Mockup Preview */}
            <div className="w-80 bg-slate-100 p-6 flex flex-col items-center justify-center border-l border-slate-200 shrink-0">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">
                Channel Preview
              </span>

              {/* Realistic Phone Shell */}
              <div className="w-64 h-[440px] bg-white rounded-[32px] border-4 border-slate-800 shadow-xl overflow-hidden flex flex-col relative">
                {/* Phone Speaker/Camera Notch */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-4 bg-slate-800 rounded-b-xl z-20 flex items-center justify-center">
                  <div className="w-8 h-1 bg-slate-600 rounded-full" />
                </div>

                {/* WhatsApp Chat Header */}
                <div className="bg-[#075e54] text-white pt-5 pb-2 px-3 flex items-center gap-2.5 shrink-0 z-10">
                  <div className="w-7 h-7 rounded-full bg-white/20 text-white font-bold text-[10px] flex items-center justify-center">
                    {initials}
                  </div>
                  <div className="min-w-0">
                    <h5 className="text-[10px] font-bold leading-tight truncate">{cust.full_name || 'Client'}</h5>
                    <p className="text-[8px] opacity-80 leading-none">Online</p>
                  </div>
                </div>

                {/* WhatsApp Chat Area */}
                <div className="flex-1 bg-[#efeae2] p-3 overflow-y-auto flex flex-col gap-2 relative">
                  {/* Encrypted Notice bubble */}
                  <div className="bg-[#e1f3fb] text-[8px] text-center text-slate-600 py-1 px-2 rounded-lg mx-auto mb-1 max-w-[85%] shadow-sm">
                    🔒 Messages are end-to-end encrypted.
                  </div>

                  {/* Incoming Client message */}
                  <div className="bg-white rounded-lg rounded-tl-none p-2 shadow-sm max-w-[85%] self-start relative text-[10px] text-slate-700">
                    Hello, thanks for keeping an eye on the account. Yes, we are planning a renovation.
                  </div>

                  {/* Composed message bubble preview (green WhatsApp style) */}
                  {editedText ? (
                    <div className="bg-[#d9fdd3] rounded-lg rounded-tr-none p-2 shadow-sm max-w-[85%] self-end relative border border-emerald-100 text-[10px] text-slate-800 mt-1.5 whitespace-pre-wrap break-words leading-relaxed animate-fade-in">
                      {editedText}
                      <div className="flex justify-end items-center gap-1.5 mt-1 text-[8px] text-slate-400">
                        <span>Draft</span>
                        <span>⏱</span>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-24 border border-dashed border-slate-300 rounded-lg m-2 text-center">
                      <p className="text-[9px] text-slate-400 px-3">
                        Draft is currently empty. Generated contents will render here in real time.
                      </p>
                    </div>
                  )}
                </div>

                {/* Phone Bottom bar */}
                <div className="bg-slate-50 p-2 flex items-center gap-2 border-t border-slate-200 shrink-0">
                  <div className="bg-white rounded-full flex-1 h-6 px-3 flex items-center text-[9px] text-slate-400 border border-slate-200">
                    Message payload...
                  </div>
                  <div className="w-6 h-6 rounded-full bg-[#128c7e] text-white flex items-center justify-center shrink-0">
                    🎤
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
