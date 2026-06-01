import React from 'react'
import { Bot, Terminal, ShieldAlert, Cpu } from 'lucide-react'
import clsx from 'clsx'

const TIMELINE_DATA = [
  {
    agent: 'Prospect Discovery Agent',
    tool: 'get_transaction_summary',
    timestamp: '08:30 AM',
    result: 'Detected +18% increase in expenditure LTM. Flagged medical & renovation tags.',
    color: 'bg-blue-500',
    icon: Bot,
    used: true,
  },
  {
    agent: 'Evidence Agent',
    tool: 'get_transactions_by_customer',
    timestamp: '09:15 AM',
    result: 'Confirmed salary credit regularity (£12,500/mo) for 60 consecutive months.',
    color: 'bg-indigo-500',
    icon: Cpu,
    used: true,
  },
  {
    agent: 'Scoring Agent',
    tool: 'calculate_readiness_score',
    timestamp: '10:05 AM',
    result: 'Evaluated risk segment: low. Assigned premium personal loan readiness at 92%.',
    color: 'bg-purple-500',
    icon: Terminal,
    used: true,
  },
  {
    agent: 'Compliance Agent',
    tool: 'verify_kyc_consent',
    timestamp: '10:10 AM',
    result: 'Checked KYC status: verified. Marketing outreach consent flag validated as active.',
    color: 'bg-emerald-500',
    icon: Bot,
    used: true,
  },
]

export default function EvidenceTimeline({ prospect }) {
  // We can dynamically adjust values or use static realistic logs
  const logs = TIMELINE_DATA

  return (
    <div className="space-y-4">
      <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
        Evidence Execution Feed
      </div>
      <div className="relative pl-3.5 border-l border-slate-100 space-y-5">
        {logs.map((log, i) => {
          const Icon = log.icon
          return (
            <div key={i} className="relative group">
              {/* Timeline marker */}
              <span className={clsx(
                'absolute -left-[20px] top-0.5 w-3.5 h-3.5 rounded-full border-2 border-white flex items-center justify-center shadow-sm text-[8px] text-white',
                log.color
              )}>
                {i + 1}
              </span>

              {/* Log details */}
              <div className="space-y-0.5">
                <div className="flex items-center gap-1.5">
                  <p className="text-[11px] font-bold text-slate-800 tracking-tight">
                    {log.agent}
                  </p>
                  <span className="text-[9px] text-slate-400 font-mono ml-auto">
                    {log.timestamp}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[9px] text-slate-400 font-mono">
                  <Terminal size={8} /> Tool: {log.tool}
                </div>
                <p className="text-[10px] text-slate-600 leading-normal bg-slate-50 p-2 rounded-lg border border-slate-100 mt-1">
                  {log.result}
                </p>
                <div className="flex items-center gap-1.5 mt-1 text-[9px] text-slate-400">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full shrink-0" />
                  Used in final decision: <span className="font-bold text-emerald-600">YES</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
