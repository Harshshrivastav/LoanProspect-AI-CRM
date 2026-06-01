import React from 'react'
import { Database } from 'lucide-react'

export default function InlineDataGrid({ data }) {
  if (!data || !Array.isArray(data) || data.length === 0) return null

  // Extract column keys
  const columns = Object.keys(data[0])

  return (
    <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 shadow-2xs my-3 select-text max-w-xl animate-fade-in flex flex-col min-h-0">
      <div className="flex items-center gap-2 mb-3 shrink-0 select-none">
        <Database size={13} className="text-indigo-650 animate-pulse-slow" />
        <h3 className="text-xs font-black text-slate-800 uppercase tracking-wider">Strategy Findings Dataset</h3>
      </div>

      <div className="overflow-x-auto border border-slate-200/85 rounded-xl bg-white scrollbar-light flex-1">
        <table className="w-full text-left border-collapse min-w-[300px]">
          <thead>
            <tr className="border-b border-slate-200 text-[9px] text-slate-400 font-extrabold uppercase tracking-wider bg-slate-50 select-none">
              {columns.map((col, idx) => (
                <th key={idx} className="py-2.5 px-3">{col.replace(/_/g, ' ')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rIdx) => (
              <tr 
                key={rIdx} 
                className="border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors text-[11px] font-semibold text-slate-700"
              >
                {columns.map((col, colIdx) => (
                  <td key={colIdx} className="py-2.5 px-3 truncate max-w-[150px]">
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
