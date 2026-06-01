import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, LayoutGrid, CreditCard, TrendingUp, MessageSquare, ShieldCheck, AlertCircle, Sparkles } from 'lucide-react'
import { useApp } from '../../context/AppContext'
import { useClientPortal } from '../../hooks/useClientPortal'

// Sub-components import
import KYCProfileCard from './KYCProfileCard'
import TransactionOverviewPanel from './TransactionOverviewPanel'
import ProspectReasonCard from './ProspectReasonCard'
import LoanFitFactorChips from './LoanFitFactorChips'
import AgentContributionPanel from './AgentContributionPanel'
import NextBestActionCard from './NextBestActionCard'
import OutreachPreviewDrawer from './OutreachPreviewDrawer'
import ComplianceStatusBanner from './ComplianceStatusBanner'
import CampaignHistoryList from './CampaignHistoryList'
import { PortalSkeleton } from '../shared/LoadingSkeleton'
import clsx from 'clsx'

const MOBILE_TABS = [
  { id: 'kyc', label: 'KYC & Assets', icon: LayoutGrid },
  { id: 'transactions', label: 'Transactions', icon: CreditCard },
  { id: 'prospect', label: 'Rationale & Fit', icon: TrendingUp },
  { id: 'campaigns', label: 'Actions & History', icon: MessageSquare },
]

function RelationshipAssetsCard({ customer }) {
  if (!customer) return null
  const accounts = customer.accounts || []
  const products = customer.product_holdings || customer.products || []

  // Sum balances
  const totalBalance = accounts.reduce((acc, curr) => acc + (curr.current_balance || 0), 0)
  const totalInflow = accounts.reduce((acc, curr) => acc + (curr.monthly_inflow || 0), 0)
  const totalOutflow = accounts.reduce((acc, curr) => acc + (curr.monthly_outflow || 0), 0)

  const formatLakhs = (val) => {
    if (!val) return '₹0L'
    return `₹${(val / 100000).toFixed(1)}L`
  }

  const PRODUCT_EMOJIS = {
    savings_account: '💰',
    salary_account: '💵',
    credit_card: '💳',
    personal_loan: '🏦',
    home_loan: '🏠',
    fd: '📊',
    mutual_fund: '📈',
  }

  return (
    <div className="space-y-4">
      <div className="card p-5 bg-white border-slate-100 relative overflow-hidden active-glow">
        <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-4 border-b border-slate-100 pb-2">
          Banking Relationship
        </h4>
        
        <div className="space-y-4">
          <div>
            <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Relationship Size</p>
            <p className="text-2xl font-black text-blue-600 tracking-tight mt-0.5">
              {formatLakhs(totalBalance)}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-2 bg-slate-50 border border-slate-100 rounded-xl">
              <p className="text-[9px] text-slate-400 font-bold uppercase">Monthly Inflow</p>
              <p className="text-xs font-bold text-emerald-600 mt-0.5">+{formatLakhs(totalInflow)}</p>
            </div>
            <div className="p-2 bg-slate-50 border border-slate-100 rounded-xl">
              <p className="text-[9px] text-slate-400 font-bold uppercase">Monthly Outflow</p>
              <p className="text-xs font-bold text-rose-600 mt-0.5">-{formatLakhs(totalOutflow)}</p>
            </div>
          </div>

          {/* Relationship depth meter */}
          <div className="p-3 bg-blue-50/50 border border-blue-100/50 rounded-xl">
            <div className="flex justify-between items-center text-[10px] font-bold text-blue-700 mb-1.5 uppercase tracking-wider">
              <span>Relationship Depth</span>
              <span>85%</span>
            </div>
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div className="h-full bg-blue-600 rounded-full" style={{ width: '85%' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Existing Holdings */}
      {products.length > 0 && (
        <div className="card p-5 bg-white border-slate-100">
          <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-3 border-b border-slate-100 pb-2">
            Active Holdings
          </h4>
          <div className="grid grid-cols-1 gap-2">
            {products.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-100 rounded-xl">
                <div className="flex items-center gap-2">
                  <span className="text-sm shrink-0">
                    {PRODUCT_EMOJIS[item.product_type] || '🏦'}
                  </span>
                  <div>
                    <span className="text-xs font-bold text-slate-700 capitalize block leading-tight">
                      {(item.product_type || '').replace(/_/g, ' ')}
                    </span>
                    <span className={clsx(
                      'text-[9px] font-bold uppercase tracking-wider mt-0.5 block',
                      item.product_status === 'active' ? 'text-emerald-500' : 'text-slate-400'
                    )}>
                      {item.product_status}
                    </span>
                  </div>
                </div>
                {item.emi_amount > 0 && (
                  <span className="text-[10px] font-bold text-slate-500 bg-white border border-slate-200 rounded px-1.5 py-0.5">
                    EMI: ₹{(item.emi_amount / 1000).toFixed(0)}K
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function ClientPortal() {
  const { selectedCustomerId, clientPortalOpen, closeClientPortal } = useApp()
  const [activeTab, setActiveTab] = useState('kyc')
  const [outreachOpen, setOutreachOpen] = useState(false)

  const {
    customer,
    prospect,
    transactions,
    loading,
    error,
    refetch,
    messageState,
    handleGenerateMessage,
    handleApproveMessage,
    updateMessageConfig,
    updateEditedText,
  } = useClientPortal(selectedCustomerId)

  if (!clientPortalOpen) return null

  const cust = customer?.customer || customer || {}

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[80] flex items-stretch overflow-hidden">
        {/* Glass backdrop filter */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-slate-900/60 backdrop-blur-md"
          onClick={closeClientPortal}
        />

        {/* Intelligence workspace slides in from right */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 280 }}
          className="relative ml-auto w-full max-w-7xl bg-[#faf8ff] flex flex-col h-full shadow-2xl z-10"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header Banner with exact breadcrumbs from provided sample */}
          <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200/80 shrink-0">
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1 font-semibold uppercase tracking-wider">
                <span>Clients</span>
                <span className="text-[10px] font-normal text-slate-300">▶</span>
                <span className="text-blue-600 font-bold">
                  {loading ? 'Loading...' : cust.full_name || selectedCustomerId}
                </span>
              </div>
              <h1 className="text-xl font-headline-lg font-bold text-slate-800 tracking-tight leading-none flex items-center gap-2">
                Client Intelligence Portal
                {!loading && (
                  <span className="px-2 py-0.5 rounded-md bg-sky-50 border border-sky-100 text-sky-700 text-[9px] font-bold uppercase tracking-widest flex items-center gap-0.5 shadow-sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-500 animate-pulse shrink-0" /> Live Dossier
                  </span>
                )}
              </h1>
            </div>
            
            <button
              onClick={closeClientPortal}
              className="p-2 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors flex items-center gap-1"
            >
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1 hidden sm:inline">Close File</span>
              <X size={18} />
            </button>
          </div>

          {/* Body content canvas */}
          {loading ? (
            <PortalSkeleton />
          ) : error ? (
            <div className="flex flex-col items-center justify-center flex-1 gap-3.5 bg-white p-8">
              <AlertCircle size={44} className="text-red-400 animate-pulse" />
              <h3 className="text-base font-bold text-slate-800">Operational Failure</h3>
              <p className="text-slate-500 text-xs text-center max-w-sm leading-relaxed">{error}</p>
              <button onClick={closeClientPortal} className="btn-secondary text-xs px-5 py-2.5">Close dossier file</button>
            </div>
          ) : (
            <div className="flex-1 flex flex-col min-h-0">
              
              {/* DESKTOP WORKSPACE GRID (Three split-columns) */}
              <div className="hidden lg:grid grid-cols-12 gap-6 p-6 flex-1 overflow-y-auto custom-scrollbar">
                
                {/* Column 1: KYC profile & relationship balances (Left span 3) */}
                <div className="col-span-3 space-y-6">
                  <KYCProfileCard customer={customer} prospect={prospect} />
                  <RelationshipAssetsCard customer={customer} />
                </div>

                {/* Column 2: visual spending trends & prospect reasonings (Center span 6) */}
                <div className="col-span-6 space-y-6 min-w-0">
                  <ProspectReasonCard prospect={prospect} />
                  <TransactionOverviewPanel customer={customer} transactions={transactions} />
                </div>

                {/* Column 3: diagnostics, campaign status & actions (Right span 3) */}
                <div className="col-span-3 space-y-6">
                  <NextBestActionCard
                    prospect={prospect}
                    onExecuteOutreach={() => setOutreachOpen(true)}
                  />
                  <LoanFitFactorChips prospect={prospect} />
                  <ComplianceStatusBanner customer={customer} />
                  <AgentContributionPanel
                    customerId={selectedCustomerId}
                    customer={customer}
                    prospect={prospect}
                    onReanalyzed={refetch}
                  />
                  <CampaignHistoryList customer={customer} />
                </div>
              </div>

              {/* MOBILE WORKSPACE CANVAS (Tabbed navigation for screens < 1024px) */}
              <div className="lg:hidden flex-1 flex flex-col min-h-0 overflow-hidden">
                {/* Tab Header Selector */}
                <div className="flex items-center gap-1 px-4 pt-3 pb-0 bg-white border-b border-slate-200/80 shrink-0 overflow-x-auto no-scrollbar">
                  {MOBILE_TABS.map((tab) => {
                    const Icon = tab.icon
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={clsx(
                          'flex items-center gap-1.5 px-3.5 py-3 text-xs font-bold uppercase tracking-wider rounded-t-xl border-b-2 transition-all shrink-0',
                          activeTab === tab.id
                            ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                            : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                        )}
                      >
                        <Icon size={13} />
                        {tab.label}
                      </button>
                    )
                  })}
                </div>

                {/* Tab content area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {activeTab === 'kyc' && (
                    <>
                      <KYCProfileCard customer={customer} prospect={prospect} />
                      <RelationshipAssetsCard customer={customer} />
                    </>
                  )}
                  {activeTab === 'transactions' && (
                    <TransactionOverviewPanel customer={customer} transactions={transactions} />
                  )}
                  {activeTab === 'prospect' && (
                    <>
                      <ProspectReasonCard prospect={prospect} />
                      <LoanFitFactorChips prospect={prospect} />
                    </>
                  )}
                  {activeTab === 'campaigns' && (
                    <>
                      <NextBestActionCard
                        prospect={prospect}
                        onExecuteOutreach={() => setOutreachOpen(true)}
                      />
                      <ComplianceStatusBanner customer={customer} />
                      <AgentContributionPanel
                        customerId={selectedCustomerId}
                        customer={customer}
                        prospect={prospect}
                        onReanalyzed={refetch}
                      />
                      <CampaignHistoryList customer={customer} />
                    </>
                  )}
                </div>
              </div>

            </div>
          )}

          {/* OUTREACH MESSAGE PREVIEW OVERLAY DRAWER */}
          <OutreachPreviewDrawer
            isOpen={outreachOpen}
            onClose={() => setOutreachOpen(false)}
            customer={customer}
            messageState={messageState}
            onGenerate={handleGenerateMessage}
            onApprove={handleApproveMessage}
            onConfigChange={updateMessageConfig}
            onTextChange={updateEditedText}
          />

        </motion.div>
      </div>
    </AnimatePresence>
  )
}
