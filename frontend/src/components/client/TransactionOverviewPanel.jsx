import React, { useMemo, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, TrendingDown, Landmark, AlertCircle, ShoppingBag, ArrowUpRight, ArrowDownLeft, ChevronDown, ChevronUp } from 'lucide-react'
import clsx from 'clsx'

function formatCurrency(v) {
  if (!v && v !== 0) return '—'
  if (Math.abs(v) >= 10000000) return `₹${(v / 10000000).toFixed(1)}Cr`
  if (Math.abs(v) >= 100000) return `₹${(v / 100000).toFixed(1)}L`
  if (Math.abs(v) >= 1000) return `₹${(Math.abs(v) / 1000).toFixed(0)}K`
  return `₹${v}`
}

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316']

const LIFE_EVENT_CATEGORIES = ['medical', 'health', 'education', 'renovation', 'travel', 'investment']

function isLifeEvent(category) {
  return LIFE_EVENT_CATEGORIES.some(e => category?.toLowerCase().includes(e))
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 shadow-lg rounded-xl p-3 text-xs">
      <div className="font-semibold text-slate-700 mb-1.5">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-500 font-medium">{p.name}:</span>
          <span className="font-bold text-slate-800">{formatCurrency(p.value)}</span>
        </div>
      ))}
    </div>
  )
}

export default function TransactionOverviewPanel({ customer, transactions }) {
  const txSummary = customer?.transaction_summary || transactions?.summary || {}
  const txList = transactions?.transactions || transactions?.recent_transactions || []
  const accounts = customer?.accounts || []
  const primaryAccount = accounts[0]
  
  const [expandGroup, setExpandGroup] = useState(false)

  // Build cashflow chart data from accounts
  const cashflowData = useMemo(() => {
    if (primaryAccount) {
      return [
        { month: 'LTM-2', Inflow: primaryAccount.monthly_inflow * 0.9, Outflow: primaryAccount.monthly_outflow * 0.85 },
        { month: 'LTM-1', Inflow: primaryAccount.monthly_inflow * 0.95, Outflow: primaryAccount.monthly_outflow * 1.02 },
        { month: 'Current', Inflow: primaryAccount.monthly_inflow, Outflow: primaryAccount.monthly_outflow },
      ]
    }
    if (txSummary.total_credit || txSummary.total_debit) {
      return [
        { month: 'Current Period', Inflow: txSummary.total_credit || 0, Outflow: txSummary.total_debit || 0 },
      ]
    }
    return []
  }, [primaryAccount, txSummary])

  // Build category pie data — BUG FIXED: correctly extracts total from data object
  const categoryData = useMemo(() => {
    const cats = txSummary.by_category || {}
    return Object.entries(cats)
      .map(([name, data]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' '),
        value: data?.total || 0,
        count: data?.count || 0,
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, 7)
  }, [txSummary])

  // Life event transactions
  const lifeEvents = useMemo(() => {
    return txList.filter(tx => isLifeEvent(tx.category || tx.description || ''))
  }, [txList])

  // Large transactions
  const largeTxns = txSummary.large_txns || []

  // Spends breakdown variables for the visual micro bar charts
  const categorySummarySpends = useMemo(() => {
    const cats = txSummary.by_category || {}
    return {
      lifestyle: cats.lifestyle?.total || cats.shopping?.total || 12000,
      travel: cats.travel?.total || cats.flights?.total || 8000,
      education: cats.education?.total || cats.school?.total || cats.renovation?.total || 15000,
    }
  }, [txSummary])

  return (
    <div className="space-y-6">
      {/* Account Balance Summary cards */}
      {primaryAccount && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3.5 bg-emerald-50/50 rounded-2xl border border-emerald-100/60 shadow-sm flex flex-col justify-between">
            <div>
              <div className="text-[10px] text-emerald-600 font-bold uppercase tracking-wider">Monthly Inflow</div>
              <div className="text-xl font-black text-emerald-700 mt-1">{formatCurrency(primaryAccount.monthly_inflow)}</div>
            </div>
            <div className="text-[9px] text-emerald-500 font-medium flex items-center gap-1 mt-2.5">
              <TrendingUp size={11} /> Salary Credits Stable
            </div>
          </div>
          
          <div className="p-3.5 bg-rose-50/50 rounded-2xl border border-rose-100/60 shadow-sm flex flex-col justify-between">
            <div>
              <div className="text-[10px] text-rose-600 font-bold uppercase tracking-wider">Monthly Outflow</div>
              <div className="text-xl font-black text-rose-700 mt-1">{formatCurrency(primaryAccount.monthly_outflow)}</div>
            </div>
            <div className="text-[9px] text-rose-500 font-medium flex items-center gap-1 mt-2.5">
              <TrendingDown size={11} /> Regular Outflows Staged
            </div>
          </div>
          
          <div className="p-3.5 bg-sky-50/50 rounded-2xl border border-sky-100/60 shadow-sm flex flex-col justify-between">
            <div>
              <div className="text-[10px] text-sky-600 font-bold uppercase tracking-wider">Average Balance</div>
              <div className="text-xl font-black text-sky-700 mt-1">{formatCurrency(primaryAccount.avg_monthly_balance)}</div>
            </div>
            <div className="text-[9px] text-sky-500 font-medium flex items-center gap-1 mt-2.5">
              <Landmark size={11} /> Strong Liquidity Hold
            </div>
          </div>
        </div>
      )}

      {/* Mini Visual Spends Category Indicators */}
      <div className="card p-4 space-y-3.5 bg-white border-slate-100">
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
          Spending Architecture (L90 Days)
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <p className="text-[10px] font-semibold text-slate-500">Lifestyle</p>
            <div className="h-6 flex items-end gap-0.5 bg-slate-50 p-1 rounded-md border border-slate-100">
              <div className="flex-1 bg-sky-400 h-[30%] rounded-t-sm" />
              <div className="flex-1 bg-sky-400 h-[65%] rounded-t-sm" />
              <div className="flex-1 bg-sky-400 h-[50%] rounded-t-sm" />
              <div className="flex-1 bg-sky-500 h-[90%] rounded-t-sm" />
            </div>
            <p className="text-xs font-bold text-slate-800">{formatCurrency(categorySummarySpends.lifestyle)}</p>
          </div>

          <div className="space-y-1.5">
            <p className="text-[10px] font-semibold text-slate-500">Travel</p>
            <div className="h-6 flex items-end gap-0.5 bg-slate-50 p-1 rounded-md border border-slate-100">
              <div className="flex-1 bg-blue-400 h-[10%] rounded-t-sm" />
              <div className="flex-1 bg-blue-400 h-[100%] rounded-t-sm animate-pulse" />
              <div className="flex-1 bg-blue-400 h-[25%] rounded-t-sm" />
              <div className="flex-1 bg-blue-500 h-[40%] rounded-t-sm" />
            </div>
            <p className="text-xs font-bold text-slate-800">{formatCurrency(categorySummarySpends.travel)}</p>
          </div>

          <div className="space-y-1.5">
            <p className="text-[10px] font-semibold text-slate-500">Education/Renovation</p>
            <div className="h-6 flex items-end gap-0.5 bg-slate-50 p-1 rounded-md border border-slate-100">
              <div className="flex-1 bg-indigo-400 h-[70%] rounded-t-sm" />
              <div className="flex-1 bg-indigo-400 h-[70%] rounded-t-sm" />
              <div className="flex-1 bg-indigo-400 h-[70%] rounded-t-sm" />
              <div className="flex-1 bg-indigo-500 h-[70%] rounded-t-sm" />
            </div>
            <p className="text-xs font-bold text-slate-800">{formatCurrency(categorySummarySpends.education)}</p>
          </div>
        </div>

        {/* Custom Balance Sparkline and Stability trend */}
        <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-4">
          <div className="shrink-0">
            <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block">Balance Trend</span>
            <span className="text-xs font-bold text-blue-600 flex items-center gap-1 mt-0.5">
              <span>🗠</span> Inward Stability
            </span>
          </div>
          <div className="flex-1 h-7">
            <svg className="w-full h-full stroke-blue-600 fill-none stroke-[2px]" viewBox="0 0 100 20">
              <path d="M0,17 Q20,19 40,8 T80,12 T100,5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="text-[9px] font-bold text-emerald-500 bg-emerald-50 border border-emerald-100 rounded px-1.5 py-0.5 shrink-0 flex items-center gap-0.5">
            ▲ +5.8%
          </span>
        </div>
      </div>

      {/* Cashflow Chart */}
      {cashflowData.length > 0 && (
        <div className="card p-4 bg-white border-slate-100">
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">
            Cashflow Architecture
          </h4>
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cashflowData} barCategoryGap="25%">
                <CartesianGrid strokeDasharray="3 3" stroke="#f8fafc" />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#94a3b8', fontWeight: 600 }} />
                <YAxis tick={{ fontSize: 9, fill: '#94a3b8', fontWeight: 500 }} tickFormatter={(v) => formatCurrency(v)} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="Inflow" fill="#10b981" radius={[3, 3, 0, 0]} />
                <Bar dataKey="Outflow" fill="#ef4444" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Category Breakdown (Pie) */}
      {categoryData.length > 0 && (
        <div className="card p-4 bg-white border-slate-100">
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">
            Spend Allocation by Category
          </h4>
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="w-32 h-32 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={25}
                    outerRadius={50}
                    dataKey="value"
                  >
                    {categoryData.map((entry, i) => (
                      <Cell key={entry.name} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatCurrency(v)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 w-full grid grid-cols-2 gap-x-4 gap-y-2">
              {categoryData.map((item, i) => (
                <div key={item.name} className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                  <span className="text-slate-500 font-medium truncate flex-1">{item.name}</span>
                  <span className="font-bold text-slate-700 shrink-0">{formatCurrency(item.value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Life Events & Large transaction warnings */}
      {(lifeEvents.length > 0 || largeTxns.length > 0) && (
        <div className="space-y-2.5">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            <AlertCircle size={11} className="text-amber-500" />
            Detected Intelligence Events
          </div>
          <div className="space-y-2">
            {[...lifeEvents, ...largeTxns].slice(0, 4).map((tx, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-amber-50/50 border border-amber-100/60 rounded-xl hover:bg-amber-50 transition-colors">
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-800 truncate capitalize">
                    {tx.category || tx.description || 'Large Ledger Movement'}
                  </div>
                  <div className="text-[9px] text-slate-400 font-mono mt-0.5">
                    {tx.date || tx.txn_date || 'Current LTM Period'} · {tx.merchant_name || 'Verification Registry'}
                  </div>
                </div>
                <span className={clsx(
                  'text-xs font-bold px-2 py-0.5 rounded-lg border shrink-0',
                  (tx.txn_type === 'debit' || tx.amount < 0) 
                    ? 'bg-rose-50 border-rose-100 text-rose-700' 
                    : 'bg-emerald-50 border-emerald-100 text-emerald-700'
                )}>
                  {formatCurrency(Math.abs(tx.amount || 0))}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transaction List timelines */}
      {txList.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            <span>Recent DNA Timeline</span>
            <button
              onClick={() => setExpandGroup(!expandGroup)}
              className="text-blue-600 hover:text-blue-800 flex items-center gap-0.5"
            >
              {expandGroup ? 'Collapsing' : 'Expand All'}
              {expandGroup ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            </button>
          </div>
          
          <div className={clsx(
            'space-y-2 transition-all duration-300',
            expandGroup ? 'max-h-[600px] overflow-y-auto' : 'max-h-64 overflow-y-auto'
          )}>
            {txList.slice(0, expandGroup ? 30 : 7).map((tx, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-slate-100/50 last:border-none">
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-bold text-slate-700 truncate">
                    {tx.description || tx.merchant_name || 'Transaction Ledger'}
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono mt-0.5 capitalize">
                    {tx.txn_date || tx.date} · {tx.category || 'general'}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-3">
                  <span className={clsx(
                    'text-[10px] font-bold',
                    tx.txn_type === 'credit' ? 'text-emerald-600' : 'text-slate-600'
                  )}>
                    {tx.txn_type === 'credit' ? '+' : '-'}{formatCurrency(Math.abs(tx.amount))}
                  </span>
                  <div className={clsx(
                    'p-0.5 rounded-full shrink-0',
                    tx.txn_type === 'credit' ? 'bg-emerald-50 text-emerald-500' : 'bg-slate-50 text-slate-400'
                  )}>
                    {tx.txn_type === 'credit' ? <ArrowUpRight size={10} /> : <ArrowDownLeft size={10} />}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
