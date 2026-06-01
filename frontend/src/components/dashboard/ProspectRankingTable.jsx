import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  Eye,
  MessageSquare,
  Megaphone,
  Search,
  Filter,
  ChevronRight,
  RefreshCw,
  Trophy,
  BarChart2,
} from "lucide-react";
import { useApp } from "../../context/AppContext";
import { ProspectRowSkeleton } from "../shared/LoadingSkeleton";
import ScoreBar from "../shared/ScoreBar";
import { SignalList } from "../shared/SignalChip";
import ConfidenceMeter from "../shared/ConfidenceMeter";
import clsx from "clsx";

const BAND_COLORS = {
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
};

const BAND_LABELS = {
  high: "🔥 High",
  medium: "⚡ Medium",
  low: "🔵 Low",
};

function getInitials(name = "") {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function getAvatarColor(name = "") {
  const colors = [
    "bg-blue-500",
    "bg-purple-500",
    "bg-emerald-500",
    "bg-amber-500",
    "bg-rose-500",
    "bg-indigo-500",
    "bg-teal-500",
  ];
  const idx = name.charCodeAt(0) % colors.length;
  return colors[idx];
}

function formatIndianCurrency(amount) {
  if (!amount) return "—";
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`;
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(0)}K`;
  return `₹${amount}`;
}

function ScoreBreakdownMini({ breakdown = {} }) {
  const entries = Object.entries(breakdown).sort(([, a], [, b]) => b - a);
  const total = entries.reduce((s, [, v]) => s + v, 0);

  return (
    <div className="space-y-1.5">
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
        Score Breakdown
      </div>
      {entries.map(([key, val]) => (
        <div key={key} className="flex items-center gap-2">
          <div className="text-xs text-slate-600 w-36 truncate capitalize">
            {key.replace(/_/g, " ")}
          </div>
          <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${total ? (val / total) * 100 : 0}%` }}
            />
          </div>
          <span className="text-xs text-slate-500 w-6 text-right">{val}</span>
        </div>
      ))}
    </div>
  );
}

function ProspectExpandedRow({
  prospect,
  onClose,
  onViewProfile,
  onGenerateMessage,
}) {
  return (
    <tr>
      <td colSpan={7} className="px-4 pb-4 pt-0 bg-slate-50/80">
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2 }}
          className="rounded-xl border border-slate-200 bg-white p-5 grid grid-cols-3 gap-6"
        >
          {/* Column 1: Loan fit factors */}
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2.5">
              Loan Fit Factors
            </div>
            <div className="space-y-1.5">
              {(prospect.loan_fit_factors || []).map((factor, i) => (
                <div
                  key={i}
                  className="text-sm text-slate-700 flex items-start gap-2"
                >
                  <span className="mt-0.5">{factor}</span>
                </div>
              ))}
              {(!prospect.loan_fit_factors ||
                prospect.loan_fit_factors.length === 0) && (
                <p className="text-sm text-slate-400 italic">
                  No factors available
                </p>
              )}
            </div>

            {prospect.recommendation_reason && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
                <div className="text-xs font-semibold text-blue-700 mb-1">
                  Agent Recommendation
                </div>
                <p className="text-xs text-blue-800">
                  {prospect.recommendation_reason}
                </p>
              </div>
            )}
          </div>

          {/* Column 2: Score breakdown */}
          <div>
            <ScoreBreakdownMini breakdown={prospect.score_breakdown} />
            <div className="mt-4">
              <ConfidenceMeter
                confidence={prospect.confidence || 0}
                label="AI Confidence"
              />
            </div>
          </div>

          {/* Column 3: Next best action + buttons */}
          <div>
            {prospect.next_best_action && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl mb-4">
                <div className="text-xs font-semibold text-emerald-700 mb-1">
                  Next Best Action
                </div>
                <p className="text-sm font-medium text-emerald-800">
                  {prospect.next_best_action}
                </p>
              </div>
            )}
            <div className="space-y-2">
              <button
                onClick={() => onViewProfile(prospect.customer_id)}
                className="btn-primary w-full justify-center"
              >
                <Eye size={14} />
                View Full Profile
              </button>
              <button
                onClick={() => onGenerateMessage(prospect.customer_id)}
                className="btn-secondary w-full justify-center"
              >
                <MessageSquare size={14} />
                Generate Message
              </button>
            </div>
          </div>
        </motion.div>
      </td>
    </tr>
  );
}

export default function ProspectRankingTable({
  prospects = [],
  loading,
  onRefresh,
}) {
  const { openClientPortal } = useApp();
  const [expandedId, setExpandedId] = useState(null);
  const [search, setSearch] = useState("");
  const [filterBand, setFilterBand] = useState("all");
  const [filterCity, setFilterCity] = useState("all");
  const [sortBy, setSortBy] = useState("score");
  const [sortDir, setSortDir] = useState("desc");

  const cities = useMemo(() => {
    const set = new Set(prospects.map((p) => p.city).filter(Boolean));
    return Array.from(set).sort();
  }, [prospects]);

  const filtered = useMemo(() => {
    let list = [...prospects];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (p) =>
          (p.full_name || "").toLowerCase().includes(q) ||
          (p.customer_id || "").toLowerCase().includes(q) ||
          (p.city || "").toLowerCase().includes(q),
      );
    }
    if (filterBand !== "all") {
      list = list.filter((p) => p.conversion_band === filterBand);
    }
    if (filterCity !== "all") {
      list = list.filter((p) => p.city === filterCity);
    }
    list.sort((a, b) => {
      let va, vb;
      if (sortBy === "score") {
        va = a.readiness_score || 0;
        vb = b.readiness_score || 0;
      } else if (sortBy === "confidence") {
        va = a.confidence || 0;
        vb = b.confidence || 0;
      } else if (sortBy === "name") {
        va = a.full_name || "";
        vb = b.full_name || "";
      } else {
        va = a.readiness_score || 0;
        vb = b.readiness_score || 0;
      }
      if (sortDir === "asc") return va > vb ? 1 : -1;
      return va < vb ? 1 : -1;
    });
    return list;
  }, [prospects, search, filterBand, filterCity, sortBy, sortDir]);

  const toggleSort = (col) => {
    if (sortBy === col) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortBy(col);
      setSortDir("desc");
    }
  };

  const SortIcon = ({ col }) => {
    if (sortBy !== col)
      return <ChevronDown size={12} className="text-slate-300" />;
    return sortDir === "asc" ? (
      <ChevronUp size={12} className="text-blue-500" />
    ) : (
      <ChevronDown size={12} className="text-blue-500" />
    );
  };

  const toggleExpand = (id) =>
    setExpandedId((prev) => (prev === id ? null : id));

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Trophy size={15} className="text-white" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              Prospect Intelligence
            </h2>
            <p className="text-xs text-slate-400">
              {filtered.length} prospects ranked by AI readiness
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="btn-ghost"
            title="Refresh prospects"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 px-5 py-3 bg-slate-50/60 border-b border-slate-100">
        <div className="relative flex-1 max-w-xs">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="text"
            placeholder="Search prospects..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <Filter size={14} className="text-slate-400" />
        <select
          value={filterBand}
          onChange={(e) => setFilterBand(e.target.value)}
          className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Bands</option>
          <option value="high">High Intent</option>
          <option value="medium">Medium Intent</option>
          <option value="low">Low Intent</option>
        </select>
        {cities.length > 0 && (
          <select
            value={filterCity}
            onChange={(e) => setFilterCity(e.target.value)}
            className="px-3 py-1.5 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Cities</option>
            {cities.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-slate-50 text-left">
              <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-10">
                #
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                <button
                  className="flex items-center gap-1 hover:text-slate-700"
                  onClick={() => toggleSort("name")}
                >
                  Prospect <SortIcon col="name" />
                </button>
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                City
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                <button
                  className="flex items-center gap-1 hover:text-slate-700"
                  onClick={() => toggleSort("score")}
                >
                  Readiness Score <SortIcon col="score" />
                </button>
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Band
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Top Signals
              </th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <ProspectRowSkeleton key={i} />
              ))
            ) : prospects.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-16 text-center select-none">
                  <div className="max-w-md mx-auto">
                    <BarChart2
                      size={36}
                      className="text-slate-300 mx-auto mb-3.5 animate-pulse"
                    />
                    <h4 className="text-sm font-black text-slate-800 uppercase tracking-wider">Portfolio Scoring Pending</h4>
                    <p className="text-xs font-semibold text-slate-400 mt-1.5 leading-relaxed max-w-md mx-auto px-4">
                      All data values are currently unpopulated. Click <strong className="text-blue-600 font-extrabold">"Apply Dynamic Score Rules"</strong> or <strong className="text-blue-600 font-extrabold">"Refresh"</strong> to analyze and score prospects.
                    </p>
                  </div>
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center">
                  <BarChart2
                    size={32}
                    className="text-slate-300 mx-auto mb-3"
                  />
                  <p className="text-slate-500 font-medium">
                    No prospects found
                  </p>
                  <p className="text-slate-400 text-sm mt-1">
                    Try adjusting your filters
                  </p>
                </td>
              </tr>
            ) : (
              filtered.map((prospect, idx) => {
                const isExpanded = expandedId === prospect.customer_id;
                return (
                  <React.Fragment key={prospect.customer_id}>
                    <tr
                      className={clsx(
                        "border-b border-slate-50 transition-colors duration-100",
                        isExpanded ? "bg-blue-50/30" : "hover:bg-slate-50/60",
                        "cursor-pointer group",
                      )}
                      onClick={() => toggleExpand(prospect.customer_id)}
                    >
                      {/* Rank */}
                      <td className="px-4 py-3">
                        <div className="flex items-center">
                          {idx === 0 ? (
                            <span className="text-amber-500 font-bold text-sm">
                              🥇
                            </span>
                          ) : idx === 1 ? (
                            <span className="text-slate-400 font-bold text-sm">
                              🥈
                            </span>
                          ) : idx === 2 ? (
                            <span className="text-amber-700 font-bold text-sm">
                              🥉
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400 font-medium tabular-nums">
                              {idx + 1}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Name */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div
                            className={clsx(
                              "w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0",
                              getAvatarColor(prospect.full_name),
                            )}
                          >
                            {getInitials(prospect.full_name)}
                          </div>
                          <div className="min-w-0">
                            <button
                              className="text-sm font-semibold text-blue-600 hover:underline truncate block text-left"
                              onClick={(e) => {
                                e.stopPropagation();
                                openClientPortal(prospect.customer_id);
                              }}
                            >
                              {prospect.full_name}
                            </button>
                            <div className="text-xs text-slate-400">
                              {prospect.customer_id}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* City */}
                      <td className="px-4 py-3">
                        <span className="text-sm text-slate-600">
                          {prospect.city || "—"}
                        </span>
                      </td>

                      {/* Score */}
                      <td className="px-4 py-3 w-48">
                        <ScoreBar
                          score={prospect.readiness_score || 0}
                          height="h-2"
                        />
                      </td>

                      {/* Band */}
                      <td className="px-4 py-3">
                        <span className={BAND_COLORS[prospect.conversion_band]}>
                          {BAND_LABELS[prospect.conversion_band] ||
                            prospect.conversion_band}
                        </span>
                      </td>

                      {/* Signals */}
                      <td className="px-4 py-3">
                        <SignalList
                          signals={prospect.positive_signals || []}
                          riskFlags={prospect.risk_flags || []}
                          maxVisible={2}
                          small
                        />
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3">
                        <div
                          className="flex items-center gap-2"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            onClick={() =>
                              openClientPortal(prospect.customer_id)
                            }
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium rounded-lg transition-colors"
                          >
                            <Eye size={12} />
                            Profile
                          </button>
                          <button
                            onClick={() => {
                              openClientPortal(prospect.customer_id);
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg transition-colors"
                          >
                            <MessageSquare size={12} />
                            Message
                          </button>
                        </div>
                      </td>
                    </tr>
                    <AnimatePresence>
                      {isExpanded && (
                        <ProspectExpandedRow
                          prospect={prospect}
                          onClose={() => setExpandedId(null)}
                          onViewProfile={openClientPortal}
                          onGenerateMessage={openClientPortal}
                        />
                      )}
                    </AnimatePresence>
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      {!loading && filtered.length > 0 && (
        <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Showing {filtered.length} of {prospects.length} prospects · Click
            any row to expand
          </span>
          <span className="text-xs text-slate-400">
            Sorted by: {sortBy} (
            {sortDir === "desc" ? "highest first" : "lowest first"})
          </span>
        </div>
      )}
    </div>
  );
}
