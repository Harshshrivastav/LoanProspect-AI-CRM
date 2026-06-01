import React, { useState, useEffect, useRef } from 'react'
import { NavLink, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  MessageSquare,
  Plus,
  Pin,
  Archive,
  Trash2,
  Bot,
  TrendingUp,
  Briefcase,
  Settings,
  Zap,
  Edit2,
  ChevronDown,
  Building2,
  Activity,
  Search,
  Bell,
  HelpCircle,
} from 'lucide-react'
import { useChat } from '../context/ChatContext'
import { useApp } from '../context/AppContext'
import { getCampaigns } from '../api/client'
import clsx from 'clsx'

function SessionItem({ session, isActive, onSelect, onRename, onPin, onArchive, onDelete }) {
  const [hovering, setHovering] = useState(false)
  const [renaming, setRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState(session.title || 'Untitled')
  const inputRef = useRef(null)
  const sessionId = session.session_id || session.id

  useEffect(() => {
    if (renaming && inputRef.current) inputRef.current.focus()
  }, [renaming])

  const handleRenameSubmit = () => {
    if (renameValue.trim()) {
      onRename(sessionId, renameValue.trim())
    }
    setRenaming(false)
  }

  return (
    <div
      className={clsx(
        'group relative flex items-center gap-2 px-3.5 py-1.5 rounded-lg cursor-pointer transition-all duration-100 text-xs mx-1',
        isActive 
          ? 'bg-blue-50 text-blue-900 font-bold border-l-2 border-blue-600' 
          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 font-medium'
      )}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => { setHovering(false) }}
      onClick={() => !renaming && onSelect(sessionId)}
    >
      {session.pinned && <Pin size={9} className="text-blue-500 shrink-0" />}
      <MessageSquare size={12} className="shrink-0 opacity-60 text-slate-400" />

      {renaming ? (
        <input
          ref={inputRef}
          value={renameValue}
          onChange={(e) => setRenameValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleRenameSubmit()
            if (e.key === 'Escape') setRenaming(false)
          }}
          onBlur={handleRenameSubmit}
          className="flex-1 bg-white border border-slate-200 text-slate-800 text-xs px-1 rounded outline-none min-w-0"
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <span className="flex-1 truncate min-w-0">{session.title || 'Untitled'}</span>
      )}

      {hovering && !renaming && (
        <div className="flex items-center gap-0.5 shrink-0 bg-inherit pl-1" onClick={(e) => e.stopPropagation()}>
          <button
            title="Rename"
            className="p-0.5 hover:text-slate-900 text-slate-400 rounded transition-colors"
            onClick={() => setRenaming(true)}
          >
            <Edit2 size={10} />
          </button>
          <button
            title={session.pinned ? 'Unpin' : 'Pin'}
            className="p-0.5 hover:text-slate-900 text-slate-400 rounded transition-colors"
            onClick={() => onPin(sessionId, session.pinned)}
          >
            <Pin size={10} />
          </button>
          <button
            title="Archive"
            className="p-0.5 hover:text-slate-900 text-slate-400 rounded transition-colors"
            onClick={() => onArchive(sessionId)}
          >
            <Archive size={10} />
          </button>
          <button
            title="Delete"
            className="p-0.5 hover:text-red-600 text-slate-400 rounded transition-colors"
            onClick={() => onDelete(sessionId)}
          >
            <Trash2 size={10} />
          </button>
        </div>
      )}
    </div>
  )
}

export default function AppLayout({ children }) {
  const navigate = useNavigate()
  const location = useLocation()
  const {
    sessions,
    activeSessionId,
    switchSession,
    startNewSession,
    removeSession,
    renameSessionLocal,
    togglePinSession,
    archiveSessionLocal,
    loadSessions,
    sessionsLoading,
  } = useChat()
  const { setSettingsModalOpen } = useApp()
  const [campaigns, setCampaigns] = useState([])
  const [campaignsExpanded, setCampaignsExpanded] = useState(true)

  useEffect(() => {
    loadSessions()
    getCampaigns()
      .then((d) => setCampaigns((d.campaigns || d || []).slice(0, 4)))
      .catch(() => {})
  }, [])

  const handleNewChat = async () => {
    const sessionId = await startNewSession('New Conversation')
    navigate('/chat')
  }

  const handleSelectSession = (sessionId) => {
    switchSession(sessionId)
    navigate(`/chat/${sessionId}`)
  }

  const pinnedSessions = sessions.filter((s) => s.pinned)
  const recentSessions = sessions.filter((s) => !s.pinned).slice(0, 15)

  return (
    <div className="flex h-full bg-slate-50 flex-col overflow-hidden">
      {/* Top Header Bar */}
      

      <div className="flex flex-1 h-full overflow-hidden w-full relative">
        {/* Left Light Sidebar */}
        <aside className="fixed left-0 h-[calc(100vh-64px)] w-64 bg-white border-r border-slate-200 flex flex-col z-40 overflow-y-auto no-scrollbar pt-4 select-none">
          {/* RM Portal details card */}
          <div className="px-3 mb-4">
            <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shrink-0 shadow-sm text-white">
                <Building2 size={15} />
              </div>
              <div className="min-w-0">
                <div className="text-slate-900 font-bold text-xs leading-normal">RM Portal</div>
                <div className="text-slate-400 text-[10px] font-semibold leading-none">Wealth Management</div>
              </div>
            </div>
          </div>

          {/* Workspace navigation links */}
          <div className="mx-3 mb-2 shrink-0">
            <div 
              onClick={() => navigate('/chat')}
              className={clsx(
                'flex items-center gap-2.5 px-3 py-2 text-xs font-bold rounded-lg cursor-pointer transition-colors shadow-sm select-none border',
                location.pathname.startsWith('/chat')
                  ? 'bg-sky-50 text-blue-900 border-sky-100/50 font-bold'
                  : 'bg-slate-50 text-slate-600 border-slate-100 hover:text-slate-900 font-medium'
              )}
            >
              <LayoutDashboard size={13} className={location.pathname.startsWith('/chat') ? 'text-blue-600' : 'text-slate-400'} />
              Workspace
            </div>
          </div>

          {/* Standard Navigation Options */}
          <nav className="px-3 space-y-1.5 shrink-0">
            <NavLink
              to="/"
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-bold transition-all duration-100',
                  isActive
                    ? 'bg-slate-50 text-slate-950 border border-slate-100'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950'
                )
              }
            >
              <TrendingUp size={13} className="text-slate-400" />
              Analytics
            </NavLink>
            
            <button
              onClick={handleNewChat}
              className="w-full flex items-center justify-center gap-2.5 px-3 py-2.5 rounded-lg text-xs font-black bg-blue-600 hover:bg-blue-750 text-white shadow-sm transition-all active:scale-97 border border-blue-500/20"
            >
              <Plus size={13} />
              New Conversation
            </button>
          </nav>

          {/* RECENT QUERIES list mapping */}
          <div className="flex-1 overflow-y-auto px-3 mt-6 min-h-0 select-none pb-4">
            <div className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider px-3.5 mb-2 select-none">
              Recent Queries
            </div>
            
            {sessionsLoading ? (
              <div className="space-y-1">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-7 bg-slate-50 border border-slate-100 rounded-lg shimmer mx-1" />
                ))}
              </div>
            ) : (
              <div className="space-y-0.5">
                {recentSessions.map((s) => (
                  <SessionItem
                    key={s.session_id || s.id}
                    session={s}
                    isActive={(s.session_id || s.id) === activeSessionId}
                    onSelect={handleSelectSession}
                    onRename={renameSessionLocal}
                    onPin={togglePinSession}
                    onArchive={archiveSessionLocal}
                    onDelete={removeSession}
                  />
                ))}

                {sessions.length === 0 && (
                  <div className="text-center py-6 select-none">
                    <MessageSquare size={18} className="text-slate-300 mx-auto mb-1.5" />
                    <p className="text-slate-400 text-[10px]">No recent queries</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Help Center bottom alignment */}
          <div className="px-3 pb-4 border-t border-slate-100 pt-3 space-y-1 shrink-0 bg-white select-none">
            <div className="flex items-center gap-2.5 px-3 py-2 text-slate-500 hover:text-slate-800 hover:bg-slate-50 rounded-lg transition-colors text-xs font-bold cursor-pointer">
              <HelpCircle size={13} className="text-slate-400" />
              Help Center
            </div>
          </div>
        </aside>

        {/* Main Content Layout Container */}
        <main className="ml-64 flex-1 flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-slate-50 relative">
          {children}
        </main>
      </div>
    </div>
  )
}
