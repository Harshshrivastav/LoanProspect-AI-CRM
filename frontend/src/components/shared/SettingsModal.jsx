import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { X, Key, Bot, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { updateAgentConfig } from '../../api/client'
import { useApp } from '../../context/AppContext'

const MODELS = [
  'gemini-2.5-flash',
  'gemini-2.5-pro',
  'gemini-2.0-flash',
  'gemini-1.5-flash',
  'gemini-1.5-pro',
]

export default function SettingsModal({ onClose }) {
  const { setApiKeySet, addNotification } = useApp()
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('gemini-2.5-flash')

  const [showKey, setShowKey] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setError('API key is required')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await updateAgentConfig(apiKey.trim(), model)
      setSaved(true)
      setApiKeySet(true)
      addNotification({ type: 'success', message: 'Agent configuration saved successfully!' })
      setTimeout(onClose, 1200)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <Bot size={16} className="text-blue-600" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900">Agent Configuration</h2>
              <p className="text-xs text-slate-500">Configure your Gemini AI connection</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* API Key */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Gemini API Key
            </label>
            <div className="relative">
              <Key size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full pl-9 pr-10 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Get your key at{' '}
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline"
              >
                Google AI Studio
              </a>
            </p>
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              Gemini Model
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
            >
              {MODELS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Status messages */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle size={15} className="text-red-500 shrink-0" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
          {saved && (
            <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
              <CheckCircle size={15} className="text-emerald-500 shrink-0" />
              <span className="text-sm text-emerald-700">Configuration saved! Agents are ready.</span>
            </div>
          )}

          {/* Info box */}
          <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg">
            <p className="text-xs text-blue-700">
              Your API key is sent directly to the backend and never stored in the browser.
              The app works without a key but AI agent features will be unavailable.
            </p>
          </div>
        </div>

        <div className="flex gap-3 px-6 pb-6">
          <button onClick={onClose} className="btn-secondary flex-1">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || saved}
            className="btn-primary flex-1 justify-center"
          >
            {saving ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Saving...
              </>
            ) : saved ? (
              <>
                <CheckCircle size={15} />
                Saved!
              </>
            ) : (
              'Save Configuration'
            )}
          </button>
        </div>
      </motion.div>
    </div>
  )
}
