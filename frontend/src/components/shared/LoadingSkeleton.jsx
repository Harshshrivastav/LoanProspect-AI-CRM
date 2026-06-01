import React from 'react'
import clsx from 'clsx'

function SkeletonBlock({ className = '' }) {
  return <div className={clsx('shimmer rounded', className)} />
}

export function KPICardSkeleton() {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <SkeletonBlock className="h-4 w-24" />
        <SkeletonBlock className="h-8 w-8 rounded-lg" />
      </div>
      <SkeletonBlock className="h-8 w-16 mb-1" />
      <SkeletonBlock className="h-3 w-20" />
    </div>
  )
}

export function ProspectRowSkeleton() {
  return (
    <tr className="border-b border-slate-50">
      <td className="px-4 py-3">
        <SkeletonBlock className="h-4 w-6" />
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <SkeletonBlock className="h-9 w-9 rounded-full" />
          <div className="space-y-1.5">
            <SkeletonBlock className="h-4 w-32" />
            <SkeletonBlock className="h-3 w-20" />
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <SkeletonBlock className="h-4 w-20" />
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <SkeletonBlock className="h-2 flex-1 rounded-full" />
          <SkeletonBlock className="h-4 w-8" />
        </div>
      </td>
      <td className="px-4 py-3">
        <SkeletonBlock className="h-5 w-16 rounded-full" />
      </td>
      <td className="px-4 py-3">
        <div className="flex gap-1">
          <SkeletonBlock className="h-5 w-20 rounded-full" />
          <SkeletonBlock className="h-5 w-16 rounded-full" />
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="flex gap-2">
          <SkeletonBlock className="h-7 w-24 rounded-lg" />
          <SkeletonBlock className="h-7 w-20 rounded-lg" />
        </div>
      </td>
    </tr>
  )
}

export function MessageSkeleton({ role = 'assistant' }) {
  const isUser = role === 'user'
  return (
    <div className={clsx('flex gap-3 px-4 py-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && <SkeletonBlock className="h-8 w-8 rounded-full shrink-0" />}
      <div className={clsx('space-y-2', isUser ? 'max-w-xs' : 'max-w-md')}>
        <SkeletonBlock className="h-4 w-48" />
        <SkeletonBlock className="h-4 w-64" />
        <SkeletonBlock className="h-4 w-40" />
      </div>
    </div>
  )
}

export function PortalSkeleton() {
  return (
    <div className="flex h-full gap-6 p-6">
      {/* Left panel */}
      <div className="w-72 shrink-0 space-y-4">
        <div className="card p-5 space-y-4">
          <div className="flex flex-col items-center gap-3">
            <SkeletonBlock className="h-20 w-20 rounded-full" />
            <SkeletonBlock className="h-5 w-32" />
            <SkeletonBlock className="h-4 w-24" />
          </div>
          <div className="space-y-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex justify-between">
                <SkeletonBlock className="h-4 w-24" />
                <SkeletonBlock className="h-4 w-20" />
              </div>
            ))}
          </div>
        </div>
      </div>
      {/* Center panel */}
      <div className="flex-1 space-y-4">
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonBlock key={i} className="h-9 w-24 rounded-lg" />
          ))}
        </div>
        <div className="card p-5 space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <SkeletonBlock key={i} className="h-4 w-full" />
          ))}
        </div>
      </div>
    </div>
  )
}

export function AgentActivitySkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex gap-3 items-start">
          <SkeletonBlock className="h-7 w-7 rounded-full shrink-0" />
          <div className="flex-1 space-y-1.5">
            <SkeletonBlock className="h-4 w-40" />
            <SkeletonBlock className="h-3 w-56" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function CampaignCardSkeleton() {
  return (
    <div className="card p-5 space-y-3">
      <div className="flex items-start justify-between">
        <SkeletonBlock className="h-5 w-40" />
        <SkeletonBlock className="h-5 w-16 rounded-full" />
      </div>
      <SkeletonBlock className="h-2 w-full rounded-full" />
      <div className="flex gap-3">
        <SkeletonBlock className="h-4 w-24" />
        <SkeletonBlock className="h-4 w-20" />
      </div>
      <div className="flex gap-2">
        <SkeletonBlock className="h-8 w-20 rounded-lg" />
        <SkeletonBlock className="h-8 w-24 rounded-lg" />
      </div>
    </div>
  )
}
