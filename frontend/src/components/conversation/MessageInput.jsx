import React, { useRef, useEffect, useCallback } from 'react'
import { Send, Square, Plus, Mic } from 'lucide-react'
import clsx from 'clsx'

export default function MessageInput({
  value,
  onChange,
  onSubmit,
  onAbort,
  isStreaming,
  placeholder = 'Instruct the Decision Maker Agent…',
  disabled = false,
}) {
  const textareaRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px'
    }
  }, [value])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isStreaming && value.trim()) {
        onSubmit()
      }
    }
  }, [isStreaming, value, onSubmit])

  const canSubmit = !isStreaming && value.trim().length > 0 && !disabled

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3 shrink-0">
      <div className={clsx(
        'flex items-center gap-3 bg-white border rounded-full px-4 py-2 transition-all duration-150',
        isStreaming ? 'border-blue-300 shadow-[0_0_0_3px_rgba(59,130,246,0.15)]' :
        'border-slate-200 shadow-sm focus-within:border-blue-300 focus-within:shadow-[0_0_0_3px_rgba(59,130,246,0.1)]'
      )}>
        {/* Plus Action Icon */}
        <button 
          type="button"
          className="w-7 h-7 rounded-full flex items-center justify-center bg-slate-50 text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors shrink-0"
          title="Add attachment or action"
        >
          <Plus size={15} />
        </button>

        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isStreaming ? 'Agent is working…' : placeholder}
          disabled={isStreaming || disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none leading-relaxed min-h-[24px] max-h-40 disabled:cursor-not-allowed disabled:opacity-70 py-1"
        />

        <div className="flex items-center gap-2.5 shrink-0">
          {/* Microphone Icon */}
          <button
            type="button"
            className="p-1 text-slate-400 hover:text-slate-600 transition-colors"
            title="Voice command"
          >
            <Mic size={15} />
          </button>

          {isStreaming ? (
            <button
              onClick={onAbort}
              className="flex items-center gap-1.5 px-3 py-1 bg-red-50 hover:bg-red-100 text-red-600 text-xs font-semibold rounded-full transition-colors"
              title="Stop generation"
            >
              <Square size={10} fill="currentColor" />
              Stop
            </button>
          ) : (
            <button
              onClick={onSubmit}
              disabled={!canSubmit}
              className={clsx(
                'w-7 h-7 rounded-full flex items-center justify-center transition-all duration-150 shrink-0',
                canSubmit
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-300 cursor-not-allowed'
              )}
              title="Send message"
            >
              <Send size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Helper text */}
      <div className="text-center mt-2">
        <span className="text-[11px] text-slate-400 select-none">
          Glacier AI can make mistakes. Verify important financial data.
        </span>
      </div>
    </div>
  )
}
