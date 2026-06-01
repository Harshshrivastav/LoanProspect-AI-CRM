import React, { createContext, useContext, useState, useCallback } from 'react'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [selectedCustomerId, setSelectedCustomerId] = useState(null)
  const [clientPortalOpen, setClientPortalOpen] = useState(false)
  const [activeCampaign, setActiveCampaign] = useState(null)
  const [agentStatus, setAgentStatus] = useState(null)
  const [apiKeySet, setApiKeySet] = useState(false)
  const [settingsModalOpen, setSettingsModalOpen] = useState(false)
  const [notifications, setNotifications] = useState([])

  const openClientPortal = useCallback((customerId) => {
    setSelectedCustomerId(customerId)
    setClientPortalOpen(true)
  }, [])

  const closeClientPortal = useCallback(() => {
    setClientPortalOpen(false)
    // Don't clear selectedCustomerId immediately to allow exit animation
    setTimeout(() => setSelectedCustomerId(null), 300)
  }, [])

  const addNotification = useCallback((notification) => {
    const id = Date.now()
    setNotifications((prev) => [...prev, { id, ...notification }])
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id))
    }, 5000)
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
  }, [])

  return (
    <AppContext.Provider
      value={{
        selectedCustomerId,
        setSelectedCustomerId,
        clientPortalOpen,
        openClientPortal,
        closeClientPortal,
        activeCampaign,
        setActiveCampaign,
        agentStatus,
        setAgentStatus,
        apiKeySet,
        setApiKeySet,
        settingsModalOpen,
        setSettingsModalOpen,
        notifications,
        addNotification,
        removeNotification,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
