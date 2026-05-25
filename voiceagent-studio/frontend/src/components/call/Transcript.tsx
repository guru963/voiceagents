import { useEffect, useRef } from 'react'

interface TranscriptProps {
  agentTranscriptions: any[]
  userTranscriptions: any[]
}

export function Transcript({ agentTranscriptions, userTranscriptions }: TranscriptProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Merge and sort by timestamp
  const all = [
    ...agentTranscriptions.map((t) => ({ ...t, speaker: 'agent' })),
    ...userTranscriptions.map((t) => ({ ...t, speaker: 'user' })),
  ].sort((a, b) => (a.firstReceivedTime ?? 0) - (b.firstReceivedTime ?? 0))

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [all.length])

  if (all.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-gray-500 text-sm">
        Transcript will appear here...
      </div>
    )
  }

  return (
    <div className="h-48 overflow-y-auto rounded-lg bg-gray-900 p-4 space-y-3">
      {all.map((msg, i) => (
        <div
          key={i}
          className={`flex gap-2 ${msg.speaker === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-xs px-3 py-2 rounded-lg text-sm
              ${msg.speaker === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-100'
              }
              ${msg.isFinal ? '' : 'opacity-60 italic'}
            `}
          >
            {msg.text || msg.transcript}
            {!msg.isFinal && <span className="ml-1 text-xs">...</span>}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
