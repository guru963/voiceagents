import { useEffect, useRef, useMemo } from 'react'

interface TranscriptProps {
  agentTranscriptions: any[]
  userTranscriptions: any[]
}

/** Strip leaked LLM function-call syntax and normalize whitespace */
function cleanText(raw: string | undefined): string {
  if (!raw) return ''
  // Remove <function=...>...</function> blocks
  let cleaned = raw.replace(/<function=\w+>.*?<\/function>/gs, '')
  // Remove orphaned <function ...> or </function> tags
  cleaned = cleaned.replace(/<\/?function[^>]*>/g, '')
  // Normalize whitespace: collapse multiple spaces/newlines into single space
  cleaned = cleaned.replace(/\s+/g, ' ')
  return cleaned.trim()
}

interface MergedMessage {
  speaker: string
  text: string
  isFinal: boolean
  key: string
}

export function Transcript({ agentTranscriptions, userTranscriptions }: TranscriptProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Merge and sort by timestamp
  const all = useMemo(() => {
    const sorted = [
      ...agentTranscriptions.map((t) => ({ ...t, speaker: 'agent' })),
      ...userTranscriptions.map((t) => ({ ...t, speaker: 'user' })),
    ].sort((a, b) => (a.firstReceivedTime ?? 0) - (b.firstReceivedTime ?? 0))

    // Merge consecutive same-speaker segments into single messages
    const merged: MergedMessage[] = []
    for (const seg of sorted) {
      const segText = cleanText(seg.text || seg.transcript)
      if (!segText) continue

      const last = merged[merged.length - 1]
      if (last && last.speaker === seg.speaker && !last.isFinal) {
        // Append to previous message with a space
        last.text = (last.text + ' ' + segText).replace(/\s+/g, ' ').trim()
        last.isFinal = !!seg.isFinal
      } else {
        merged.push({
          speaker: seg.speaker,
          text: segText,
          isFinal: !!seg.isFinal,
          key: `${seg.speaker}-${seg.firstReceivedTime ?? merged.length}`,
        })
      }
    }
    return merged
  }, [agentTranscriptions, userTranscriptions])

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
      {all.map((msg) => (
        <div
          key={msg.key}
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
            {msg.text}
            {!msg.isFinal && <span className="ml-1 text-xs">...</span>}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
