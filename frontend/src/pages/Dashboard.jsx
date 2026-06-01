import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Bot, Zap, RefreshCw, AlertCircle, Sparkles, Shield, Cpu, Activity, Info } from 'lucide-react'
import { getProspects, getCampaigns, getDynamicFactors, recalculateProspects } from '../api/client'
import KPICards from '../components/dashboard/KPICards'
import ProspectRankingTable from '../components/dashboard/ProspectRankingTable'
import CampaignIntelligencePanel from '../components/dashboard/CampaignIntelligencePanel'
import UrgentActionsPanel from '../components/dashboard/UrgentActionsPanel'
import AgentActivityFeed from '../components/dashboard/AgentActivityFeed'
import { useApp } from '../context/AppContext'
import clsx from 'clsx'

function DynamicDecisionCockpit({ onRecalculate, loading }) {
  const [focus, setFocus] = useState("general");
  const [risk, setRisk] = useState("moderate");
  const [loadingStep, setLoadingStep] = useState(0);

  useEffect(() => {
    if (loading) {
      setLoadingStep(0);
      const t1 = setTimeout(() => setLoadingStep(1), 1000);
      const t2 = setTimeout(() => setLoadingStep(2), 2200);
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
      };
    }
  }, [loading]);

  const focusOptions = [
    { id: "general", label: "General Personal", icon: "🌐", desc: "Default business metrics" },
    { id: "renovation", label: "Home Renovation", icon: "🏡", desc: "+12 pts boost for property spends" },
    { id: "medical", label: "Medical Emergency", icon: "🏥", desc: "+15 pts emergency liquidity booster" },
    { id: "festive", label: "Festive Seasonal", icon: "🎁", desc: "+8 pts general spend growth factor" }
  ];

  const riskOptions = [
    { id: "conservative", label: "Conservative", icon: Shield, color: "text-emerald-600 bg-emerald-50 border-emerald-100", desc: "Strict filters, maximum risk mitigation" },
    { id: "moderate", label: "Balanced", icon: Activity, color: "text-blue-600 bg-blue-50 border-blue-100", desc: "Balanced performance weighting" },
    { id: "aggressive", label: "Aggressive", icon: Zap, color: "text-amber-600 bg-amber-50 border-amber-100", desc: "Maximize conversion, higher risk tolerance" }
  ];

  return (
    <div className="bg-gradient-to-r from-blue-50/40 to-indigo-50/20 border border-slate-200/60 rounded-2xl p-5 shadow-xs relative overflow-hidden select-none">
      {loading && (
        <div className="absolute inset-0 bg-white/90 z-20 flex flex-col items-center justify-center backdrop-blur-xs animate-fade-in">
          <div className="flex gap-1.5 mb-3">
            {[0, 1, 2].map((i) => (
              <span key={i} className="w-2.5 h-2.5 rounded-full bg-[#006194] animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
          <span className="text-sm font-bold text-slate-800 tracking-tight">
            {loadingStep === 0 && "🤖 Decision Maker Agent: Querying database repositories..."}
            {loadingStep === 1 && "📋 Compliance Specialist: Validating RBI consent pool policies..."}
            {loadingStep === 2 && "⚙️ Underwriting Engine: Applying dynamic scoring formulas..."}
          </span>
          <span className="text-xs text-slate-400 mt-1 font-semibold">Running dynamic portfolio recalculation...</span>
        </div>
      )}

      <div className="flex flex-col md:flex-row gap-5 items-start md:items-center justify-between">
        <div className="space-y-4 flex-1">
          {/* Header Row */}
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-[#006194] animate-pulse" />
            <h3 className="text-xs font-extrabold text-slate-400 tracking-wider uppercase">Dynamic Underwriting Cockpit</h3>
            <span className="text-[10px] font-bold bg-blue-50 border border-blue-100 text-[#006194] px-2.5 py-0.5 rounded-full">System Active</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Column 1: Campaign Focus */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700 block">Select Campaign Strategy Focus</span>
              <div className="grid grid-cols-2 gap-2">
                {focusOptions.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setFocus(opt.id)}
                    className={clsx(
                      "px-3 py-2 rounded-xl text-left border transition-all text-xs font-semibold flex flex-col justify-between h-14",
                      focus === opt.id 
                        ? "bg-white border-[#006194] shadow-xs text-[#006194]" 
                        : "bg-white/60 border-slate-200 hover:border-slate-300 text-slate-600"
                    )}
                  >
                    <span className="flex items-center gap-1.5 leading-none">
                      <span>{opt.icon}</span>
                      {opt.label}
                    </span>
                    <span className="text-[9px] text-slate-400 font-medium leading-tight truncate w-full">{opt.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Column 2: Risk Appetite */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-slate-700 block">Dynamic Credit Risk Guidelines</span>
              <div className="grid grid-cols-3 gap-2">
                {riskOptions.map((opt) => {
                  const Icon = opt.icon;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => setRisk(opt.id)}
                      className={clsx(
                        "px-2 py-2 rounded-xl text-center border transition-all text-xs font-semibold flex flex-col items-center justify-center gap-1.5 h-14",
                        risk === opt.id 
                          ? "bg-white border-[#006194] shadow-xs text-[#006194]" 
                          : "bg-white/60 border-slate-200 hover:border-slate-300 text-slate-600"
                      )}
                    >
                      <Icon size={14} className={risk === opt.id ? "text-[#006194]" : "text-slate-400"} />
                      <span className="leading-none">{opt.label}</span>
                    </button>
                  );
                })}
              </div>
              <div className="flex items-start gap-1 text-[10px] text-slate-500 font-semibold leading-relaxed mt-1">
                <Info size={11} className="text-slate-400 shrink-0 mt-0.5" />
                {risk === "conservative" && "Conservative: Deducts 20 points for high-risk assets and penalizes EMI ratios > 30%."}
                {risk === "moderate" && "Balanced: Standard Loan It risk-rating matrices and consent checks are applied."}
                {risk === "aggressive" && "Aggressive: Minimizes high-risk penalties and adds a +5 points booster to qualified prospects."}
              </div>
            </div>
          </div>
        </div>

        {/* Action Button Column */}
        <div className="shrink-0 flex items-center self-stretch md:self-center md:pl-4">
          <button
            onClick={() => onRecalculate(focus, risk)}
            disabled={loading}
            className="w-full md:w-auto bg-[#006194] hover:bg-blue-800 text-white text-xs font-bold px-5 py-3.5 rounded-xl shadow-md shadow-blue-100 hover:shadow-lg transition-all flex items-center justify-center gap-2 select-none"
          >
            <Cpu size={14} className="animate-pulse" />
            Apply Dynamic Score Rules
          </button>
        </div>
      </div>
    </div>
  );
}


function DashboardHeader({ onRefresh, refreshing }) {
  return (
    <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-100 shrink-0">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Prospect Intelligence</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          AI-ranked loan prospects — updated in real time
        </p>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-200 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-emerald-700 font-medium">Live</span>
        </div>
        <button
          onClick={onRefresh}
          disabled={refreshing}
          className="btn-secondary text-xs"
        >
          <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [prospects, setProspects] = useState([])
  const [campaigns, setCampaigns] = useState([])
  const [prospectsLoading, setProspectsLoading] = useState(false)
  const [campaignsLoading, setCampaignsLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [recalculating, setRecalculating] = useState(false)
  const [error, setError] = useState(null)

  const fetchProspects = useCallback(async () => {
    setProspectsLoading(true)
    try {
      const data = await getProspects(20)
      setProspects(data.prospects || data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setProspectsLoading(false)
    }
  }, [])

  const fetchCampaigns = useCallback(async () => {
    setCampaignsLoading(true)
    try {
      const data = await getCampaigns()
      setCampaigns(data.campaigns || data || [])
    } catch {
      setCampaigns([])
    } finally {
      setCampaignsLoading(false)
    }
  }, [])

  useEffect(() => {
    // Keep initially empty per requirements. Load data on RM refresh request.
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    await Promise.all([fetchProspects(), fetchCampaigns()])
    setRefreshing(false)
  }

  const handleCampaignsRefresh = () => {
    fetchCampaigns()
  }

  const handleRecalculate = async (focus, risk) => {
    setRecalculating(true)
    setError(null)
    try {
      const res = await recalculateProspects(focus, risk)
      if (res.status === "success") {
        setProspects(res.prospects || [])
        // Fetch campaigns as well
        await fetchCampaigns()
      } else {
        throw new Error(res.message || "Failed to recalculate")
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setRecalculating(false)
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <DashboardHeader onRefresh={handleRefresh} refreshing={refreshing} />

      <div className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* Dynamic Underwriting Cockpit */}
          <DynamicDecisionCockpit 
            onRecalculate={handleRecalculate}
            loading={recalculating}
          />

          {/* KPI Cards */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <KPICards
              prospects={prospects}
              campaigns={campaigns}
              loading={prospectsLoading && campaignsLoading}
            />
          </motion.div>

          {/* Main grid: Prospect Table + Right sidebar */}
          <div className="grid grid-cols-[1fr_280px] gap-5">
            {/* Left: Prospect Ranking Table (main centerpiece) */}
            <div className="min-w-0">
              <ProspectRankingTable
                prospects={prospects}
                loading={prospectsLoading}
                onRefresh={fetchProspects}
              />
            </div>

            {/* Right sidebar: Urgent + Activity Feed */}
            <div className="space-y-5 min-h-0">
              <UrgentActionsPanel
                prospects={prospects}
                loading={prospectsLoading}
              />
              <div style={{ height: '380px' }}>
                <AgentActivityFeed />
              </div>
            </div>
          </div>

          {/* Bottom: Campaign Intelligence */}
          <CampaignIntelligencePanel
            campaigns={campaigns}
            loading={campaignsLoading}
            onRefresh={handleCampaignsRefresh}
          />
        </div>
      </div>
    </div>
  )
}
