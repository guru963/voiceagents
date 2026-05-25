import { useEffect, useState, useCallback } from 'react'
import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  VoiceAssistantControlBar,
  RoomAudioRenderer,
  DisconnectButton,
  useLocalParticipant,
  useTrackTranscription,
} from '@livekit/components-react'
import '@livekit/components-styles'
import { Track } from 'livekit-client'
import { tokenApi } from '../../lib/api'
import { LatencyChart } from '../dashboard/LatencyChart'
import { Transcript } from './Transcript'

interface CallViewProps {
  agentId: string
  agentName: string
  onEnd: () => void
}

interface LatencyPoint {
  turn: number
  stt: number
  llm: number
  tts: number
  total: number
}

export function CallView({ agentId, agentName, onEnd }: CallViewProps) {
  const [token, setToken] = useState('')
  const [serverUrl, setServerUrl] = useState('')
  const [connected, setConnected] = useState(false)
  const [latencyData, setLatencyData] = useState<LatencyPoint[]>([])
  const [turn, setTurn] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    tokenApi
      .create(agentId, 'user')
      .then((res) => {
        setToken(res.data.token)
        setServerUrl(res.data.livekit_url)
      })
      .catch(() => setError('Failed to start call. Please try again.'))
  }, [agentId])

  const handleDisconnect = useCallback(() => {
    setConnected(false)
    onEnd()
  }, [onEnd])

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-400">
        {error}
      </div>
    )
  }

  if (!token) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400">Connecting to {agentName}...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <LiveKitRoom
        token={token}
        serverUrl={serverUrl}
        connect={true}
        audio={true}
        video={false}
        onDisconnected={handleDisconnect}
        onConnected={() => setConnected(true)}
        className="bg-transparent"
      >
        <RoomAudioRenderer />
        <CallInner agentName={agentName} />
      </LiveKitRoom>

      {latencyData.length > 0 && (
        <LatencyChart data={latencyData} />
      )}
    </div>
  )
}

function CallInner({ agentName }: { agentName: string }) {
  const { state, audioTrack, agentTranscriptions } = useVoiceAssistant()
  const { localParticipant, microphoneTrack } = useLocalParticipant()

  const userTrackRef = microphoneTrack ? {
    participant: localParticipant,
    publication: microphoneTrack,
    source: Track.Source.Microphone
  } : undefined

  const { segments: userTranscriptions } = useTrackTranscription(userTrackRef)

  return (
    <div className="space-y-6">
      {/* Agent status + visualizer */}
      <div className="flex flex-col items-center gap-4 py-8">
        <div className="relative">
          <div
            className={`w-24 h-24 rounded-full border-2 flex items-center justify-center text-2xl font-semibold
              ${state === 'speaking' ? 'border-blue-400 bg-blue-900/30 animate-pulse' : ''}
              ${state === 'listening' ? 'border-green-400 bg-green-900/30' : ''}
              ${state === 'thinking' ? 'border-yellow-400 bg-yellow-900/30' : ''}
              ${state === 'idle' || state === 'connecting' ? 'border-gray-600 bg-gray-800' : ''}
            `}
          >
            {agentName[0]}
          </div>
          <div className="absolute -bottom-1 -right-1">
            <StatusDot state={state} />
          </div>
        </div>
        <p className="text-lg font-medium text-white">{agentName}</p>
        <p className="text-sm text-gray-400 capitalize">{state}</p>

        {audioTrack && (
          <BarVisualizer
            trackRef={audioTrack}
            barCount={24}
            className="w-48 h-12"
          />
        )}
      </div>

      {/* Live transcript */}
      <Transcript
        agentTranscriptions={agentTranscriptions}
        userTranscriptions={userTranscriptions}
      />

      {/* Controls */}
      <div className="flex justify-center">
        <VoiceAssistantControlBar />
      </div>
    </div>
  )
}

function StatusDot({ state }: { state: string }) {
  const colors: Record<string, string> = {
    speaking: 'bg-blue-400',
    listening: 'bg-green-400',
    thinking: 'bg-yellow-400',
    idle: 'bg-gray-500',
    connecting: 'bg-gray-500',
  }
  return (
    <span
      className={`block w-4 h-4 rounded-full ${colors[state] ?? 'bg-gray-500'}`}
    />
  )
}
