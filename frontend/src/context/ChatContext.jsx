import React, { createContext, useContext, useState, useCallback, useRef } from 'react'
import { getChatSessions, getChatMessages, createChatSession, deleteSession, renameSession, pinSession, archiveSession } from '../api/client'

const ChatContext = createContext(null)

export function ChatProvider({ children }) {
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [agentActivity, setAgentActivity] = useState([])
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const streamControllerRef = useRef(null)

  const loadSessions = useCallback(async () => {
    setSessionsLoading(true)
    try {
      const data = await getChatSessions()
      setSessions(data.sessions || data || [])
    } catch (err) {
      console.error('Failed to load sessions:', err)
    } finally {
      setSessionsLoading(false)
    }
  }, [])

  const loadMessages = useCallback(async (sessionId) => {
    try {
      const data = await getChatMessages(sessionId)
      const msgs = data.messages || data || []
      setMessages(
        msgs.map((m) => {
          // Normalize plan
          let planObj = null
          if (m.plan) {
            planObj = Array.isArray(m.plan) ? { steps: m.plan } : m.plan
          } else if (m.agent_steps?.plan) {
            planObj = Array.isArray(m.agent_steps.plan) ? { steps: m.agent_steps.plan } : m.agent_steps.plan
          } else if (m.agent_steps?.entries?.plan) {
            planObj = Array.isArray(m.agent_steps.entries.plan) ? { steps: m.agent_steps.entries.plan } : m.agent_steps.entries.plan
          }

          // Normalize steps (executed tool result summaries)
          let stepList = []
          if (Array.isArray(m.steps)) {
            stepList = m.steps
          } else if (m.agent_steps) {
            if (Array.isArray(m.agent_steps)) {
              stepList = m.agent_steps
            } else if (Array.isArray(m.agent_steps.steps)) {
              stepList = m.agent_steps.steps
            } else if (Array.isArray(m.agent_steps.entries?.tool_logs)) {
              stepList = m.agent_steps.entries.tool_logs.map(log => ({
                step_number: log.step,
                tool: log.tool,
                status: log.status,
                observation: log.output,
                ts: log.ts
              }))
            }
          }

          // Normalize thoughts
          let thoughtList = []
          if (Array.isArray(m.thoughts)) {
            thoughtList = m.thoughts
          } else if (m.agent_steps) {
            if (Array.isArray(m.agent_steps.thoughts)) {
              thoughtList = m.agent_steps.thoughts
            } else if (Array.isArray(m.agent_steps.entries?.thoughts)) {
              thoughtList = m.agent_steps.entries.thoughts
            }
          }

          // Normalize suggestions
          let suggestionList = []
          if (Array.isArray(m.suggestions)) {
            suggestionList = m.suggestions
          } else if (m.agent_steps) {
            if (Array.isArray(m.agent_steps.suggestions)) {
              suggestionList = m.agent_steps.suggestions
            } else if (Array.isArray(m.agent_steps.entries?.suggestions)) {
              suggestionList = m.agent_steps.entries.suggestions
            }
          }

          return {
            id: m.id || m.message_id || Math.random().toString(36),
            role: m.role,
            content: m.content || m.text || '',
            steps: stepList,
            thoughts: thoughtList,
            plan: planObj,
            suggestions: suggestionList,
            timestamp: m.created_at || m.timestamp || new Date().toISOString(),
          }
        })
      )
    } catch (err) {
      console.error('Failed to load messages:', err)
      setMessages([])
    }
  }, [])

  const switchSession = useCallback(
    async (sessionId) => {
      setActiveSessionId(sessionId)
      setAgentActivity([])
      await loadMessages(sessionId)
    },
    [loadMessages]
  )

  const startNewSession = useCallback(
    async (title = 'New Conversation', customerContext = null) => {
      try {
        const data = await createChatSession(title, customerContext)
        const newSession = data.session || data
        setSessions((prev) => [newSession, ...prev])
        setActiveSessionId(newSession.session_id || newSession.id)
        setMessages([])
        setAgentActivity([])
        return newSession.session_id || newSession.id
      } catch (err) {
        console.error('Failed to create session:', err)
        // Create a local-only session for graceful degradation
        const localId = `local-${Date.now()}`
        setActiveSessionId(localId)
        setMessages([])
        setAgentActivity([])
        return localId
      }
    },
    []
  )

  const removeSession = useCallback(async (sessionId) => {
    try {
      await deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => (s.session_id || s.id) !== sessionId))
      if (activeSessionId === sessionId) {
        setActiveSessionId(null)
        setMessages([])
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }, [activeSessionId])

  const renameSessionLocal = useCallback(async (sessionId, title) => {
    try {
      await renameSession(sessionId, title)
      setSessions((prev) =>
        prev.map((s) =>
          (s.session_id || s.id) === sessionId ? { ...s, title } : s
        )
      )
    } catch (err) {
      console.error('Failed to rename session:', err)
    }
  }, [])

  const togglePinSession = useCallback(async (sessionId, currentPinned) => {
    try {
      await pinSession(sessionId, !currentPinned)
      setSessions((prev) =>
        prev.map((s) =>
          (s.session_id || s.id) === sessionId ? { ...s, pinned: !currentPinned } : s
        )
      )
    } catch (err) {
      console.error('Failed to pin session:', err)
    }
  }, [])

  const archiveSessionLocal = useCallback(async (sessionId) => {
    try {
      await archiveSession(sessionId)
      setSessions((prev) => prev.filter((s) => (s.session_id || s.id) !== sessionId))
    } catch (err) {
      console.error('Failed to archive session:', err)
    }
  }, [])

  const appendMessage = useCallback((message) => {
    setMessages((prev) => [...prev, message])
  }, [])

  const updateLastMessage = useCallback((updater) => {
    setMessages((prev) => {
      if (!prev.length) return prev
      const last = { ...prev[prev.length - 1] }
      const updated = typeof updater === 'function' ? updater(last) : { ...last, ...updater }
      return [...prev.slice(0, -1), updated]
    })
  }, [])

  const addAgentActivity = useCallback((event) => {
    setAgentActivity((prev) => [...prev, { ...event, timestamp: new Date().toISOString() }])
  }, [])

  const clearAgentActivity = useCallback(() => {
    setAgentActivity([])
  }, [])

  const updateSessionTitle = useCallback((sessionId, title) => {
    setSessions((prev) =>
      prev.map((s) =>
        (s.session_id || s.id) === sessionId ? { ...s, title } : s
      )
    )
  }, [])

  return (
    <ChatContext.Provider
      value={{
        sessions,
        setSessions,
        activeSessionId,
        setActiveSessionId,
        messages,
        setMessages,
        isStreaming,
        setIsStreaming,
        agentActivity,
        setAgentActivity,
        sessionsLoading,
        loadSessions,
        loadMessages,
        switchSession,
        startNewSession,
        removeSession,
        renameSessionLocal,
        togglePinSession,
        archiveSessionLocal,
        appendMessage,
        updateLastMessage,
        addAgentActivity,
        clearAgentActivity,
        updateSessionTitle,
        streamControllerRef,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export const useChat = () => {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within ChatProvider')
  return ctx
}
