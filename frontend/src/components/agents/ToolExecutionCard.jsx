import React, { useState } from 'react'
import { Wrench, ChevronDown, ChevronUp, Clock, CheckCircle, Loader } from 'lucide-react'
import clsx from 'clsx'

function truncate(str, max = 200) {
  if (!str) return ''
  const s = typeof str === 'string' ? str : JSON.stringify(str)
  return s.length > max ? s.slice(0, max) + '…' : s
}

export default function ToolExecutionCard({ event, compact = false }) {
  const [expanded, setExpanded] = useState(false)
  const { tool, input, output, result, done, ts, type } = event

  const isResult = type === 'tool_result'
  const hasOutput = output || result

  if (compact) {
    return (
      <div className="flex items-center gap-2 py-1">
        <div className={clsx(
          'w-5 h-5 rounded flex items-center justify-center shrink-0',
          done || isResult ? 'bg-emerald-100' : 'bg-blue-100'
        )}>
          {done || isResult
            ? <CheckCircle size={11} className="text-emerald-600" />
            : <Loader size={11} className="text-blue-600 animate-spin" />
          }
        </div>
        <span className="text-xs font-mono text-slate-700 truncate">
          {tool}
          {input && <span className="text-slate-400 ml-1">({truncate(input, 40)})</span>}
        </span>
      </div>
    )
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-50/50">
      {/* Tool header */}
      <button
        onClick={() => hasOutput && setExpanded(!expanded)}
        className="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-slate-100/80 transition-colors text-left"
      >
        <div className={clsx(
          'w-6 h-6 rounded-md flex items-center justify-center shrink-0',
          done || isResult ? 'bg-emerald-100' : 'bg-blue-100'
        )}>
          {done || isResult
            ? <CheckCircle size={13} className="text-emerald-600" />
            : <Loader size={13} className="text-blue-600 animate-spin" />
          }
        </div>
        <div className="flex-1 min-w-0">
          <span className="text-xs font-semibold font-mono text-slate-800">{tool}</span>
          {input && (
            <span className="text-xs text-slate-400 ml-2 font-normal truncate">
              ({truncate(typeof input === 'object' ? JSON.stringify(input) : input, 60)})
            </span>
          )}
        </div>
        {ts && (
          <span className="text-xs text-slate-400 shrink-0 tabular-nums flex items-center gap-1">
            <Clock size={10} />
            {new Date(ts).toLocaleTimeString()}
          </span>
        )}
        {hasOutput && (
          expanded ? <ChevronUp size={13} className="text-slate-400 shrink-0" /> : <ChevronDown size={13} className="text-slate-400 shrink-0" />
        )}
      </button>

      {/* Expanded output */}
      {expanded && hasOutput && (
        <div className="px-3 pb-3 border-t border-slate-200/70">
          <div className="mt-2 p-2.5 bg-slate-900 rounded-lg overflow-auto max-h-40">
            <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
              {typeof (output || result) === 'string'
                ? (output || result)
                : JSON.stringify(output || result, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
