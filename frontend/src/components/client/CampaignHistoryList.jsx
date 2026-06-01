import React from 'react'
import { Calendar, PhoneCall, Mail, MessageSquare, PlusCircle } from 'lucide-react'
import clsx from 'clsx'

const STATUS_BADGES = {
  sent: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  delivered: 'bg-teal-50 text-teal-700 border-teal-100',
  read: 'bg-blue-50 text-blue-700 border-blue-100',
  clicked: 'bg-sky-50 text-sky-700 border-sky-100',
  draft: 'bg-slate-100 text-slate-600 border-slate-200',
}

const OUTREACH_ICONS = {
  whatsapp: { icon: MessageSquare, color: 'text-emerald-500' },
  email: { icon: Mail, color: 'text-indigo-500' },
  sms: { icon: MessageSquare, color: 'text-sky-500' },
  call: { icon: PhoneCall, color: 'text-amber-500' },
}

export default function CampaignHistoryList({ customer }) {
  if (!customer) return null
  const outreachList = customer.outreach_history || []
  const notesList = customer.rm_notes || []

  return (
    <div className="space-y-4">
      {/* Communication Outreach Log */}
      <div>
        <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2.5">
          <Calendar size={11} className="text-blue-500" />
          Outreach History
        </div>
        
        {outreachList.length === 0 ? (
          <div className="text-center py-6 bg-slate-50 border border-dashed border-slate-200 rounded-xl">
            <p className="text-[11px] text-slate-400">No prior communications found</p>
          </div>
        ) : (
          <div className="space-y-2">
            {outreachList.slice(0, 5).map((log, i) => {
              const channelCfg = OUTREACH_ICONS[log.channel] || OUTREACH_ICONS.whatsapp
              const ChannelIcon = channelCfg.icon
              const statusClass = STATUS_BADGES[log.sent_status] || STATUS_BADGES.draft
              return (
                <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 hover:bg-slate-100/70 border border-slate-100 rounded-xl transition-all duration-150">
                  <div className={clsx('p-1.5 bg-white rounded-lg shadow-sm shrink-0', channelCfg.color)}>
                    <ChannelIcon size={13} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-bold text-slate-700 capitalize">
                        {log.channel} Outreach
                      </span>
                      <span className={clsx('px-1.5 py-0.5 rounded text-[8px] font-bold border uppercase tracking-wider', statusClass)}>
                        {log.sent_status}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-600 mt-1 leading-normal line-clamp-2">
                      "{log.message_text}"
                    </p>
                    {log.created_at && (
                      <span className="text-[9px] text-slate-400 mt-1 block">
                        {new Date(log.created_at).toLocaleDateString()} at{' '}
                        {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* RM Notes Section */}
      {notesList.length > 0 && (
        <div className="pt-2">
          <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2.5">
            <span>Dossier Intelligence Notes</span>
            <span className="text-slate-400">Total: {notesList.length}</span>
          </div>
          <div className="space-y-2">
            {notesList.slice(0, 3).map((note, i) => (
              <div key={i} className="p-3 bg-amber-50/50 border border-amber-100/60 rounded-xl">
                <p className="text-[10px] text-amber-900 leading-relaxed font-medium">
                  {note.note_text}
                </p>
                <div className="flex justify-between items-center mt-1.5 text-[8px] text-amber-700 font-bold uppercase tracking-wider">
                  <span>Auditor: {note.rm_id}</span>
                  {note.created_at && (
                    <span>{new Date(note.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
