import React, { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import { AppProvider, useApp } from './context/AppContext'
import { ChatProvider } from './context/ChatContext'
import AppLayout from './layouts/AppLayout'
import Dashboard from './pages/Dashboard'
import ConversationWorkspace from './pages/ConversationWorkspace'
import ClientPortal from './components/client/ClientPortal'
import SettingsModal from './components/shared/SettingsModal'
import NotificationToast from './components/shared/NotificationToast'

function AppInner() {
  const { settingsModalOpen, setSettingsModalOpen, notifications, removeNotification } = useApp()
  return (
    <>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<ConversationWorkspace />} />
          <Route path="/chat/:sessionId" element={<ConversationWorkspace />} />
        </Routes>
      </AppLayout>
      <ClientPortal />
      {settingsModalOpen && <SettingsModal onClose={() => setSettingsModalOpen(false)} />}
      <div className="fixed bottom-4 right-4 z-[200] flex flex-col gap-2 pointer-events-none">
        {notifications.map((n) => (
          <NotificationToast
            key={n.id}
            notification={n}
            onDismiss={() => removeNotification(n.id)}
          />
        ))}
      </div>
    </>
  )
}

export default function App() {
  return (
    <AppProvider>
      <ChatProvider>
        <AppInner />
      </ChatProvider>
    </AppProvider>
  )
}
