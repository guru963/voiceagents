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
  useRoomContext,
} from '@livekit/components-react'
import '@livekit/components-styles'
import { Track } from 'livekit-client'
import { tokenApi } from '../../lib/api'
import { LatencyChart } from '../dashboard/LatencyChart'
import { Transcript } from './Transcript'
import { Calendar, User, Clock, CheckCircle, Utensils, X, Activity } from 'lucide-react'

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
  const room = useRoomContext()
  const [bookingData, setBookingData] = useState<any>(null)

  useEffect(() => {
    const handleData = (payload: Uint8Array, participant?: any) => {
      try {
        const text = new TextDecoder().decode(payload)
        const data = JSON.parse(text)
        if (data && (data.type === 'booking_confirmed' || data.type === 'availability_checked')) {
          setBookingData(data)
        }
      } catch (e) {
        console.error('Failed to parse data message:', e)
      }
    }

    room.on('dataReceived', handleData)
    return () => {
      room.off('dataReceived', handleData)
    }
  }, [room])

  const userTrackRef = microphoneTrack ? {
    participant: localParticipant,
    publication: microphoneTrack,
    source: Track.Source.Microphone
  } : undefined

  const { segments: userTranscriptions } = useTrackTranscription(userTrackRef)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
      {/* Call panel */}
      <div className={`${bookingData ? 'lg:col-span-2' : 'lg:col-span-3'} space-y-6 transition-all duration-300`}>
        {/* Agent status + visualizer */}
        <div className="flex flex-col items-center gap-4 py-8 bg-gray-900/40 border border-gray-800 rounded-2xl p-6 backdrop-blur-md">
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

      {/* Booking Side Panel */}
      {bookingData && (
        <div className="lg:col-span-1 w-full">
          <LiveBookingTerminal data={bookingData} onClose={() => setBookingData(null)} />
        </div>
      )}
    </div>
  )
}

function LiveBookingTerminal({ data, onClose }: { data: any; onClose: () => void }) {
  const isHospital = data.category === 'hospital'
  const isRestaurant = data.category === 'restaurant'
  const isHotel = data.category === 'hotel'
  
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 backdrop-blur-md relative shadow-2xl flex flex-col gap-4 animate-in slide-in-from-right duration-300">
      <button 
        onClick={onClose}
        className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
      >
        <X className="w-4 h-4" />
      </button>

      <div className="flex items-center gap-2 border-b border-gray-800 pb-3">
        <div className={`w-2.5 h-2.5 rounded-full ${data.type === 'booking_confirmed' ? 'bg-green-500 animate-ping' : 'bg-blue-500'}`} />
        <h3 className="text-xs font-semibold tracking-wider text-gray-400 uppercase">
          {data.type === 'booking_confirmed' ? 'Live Booking Ticket' : 'Availability Check'}
        </h3>
      </div>

      {data.type === 'booking_confirmed' ? (
        <div className="relative border border-dashed border-gray-700 bg-gray-950/60 rounded-xl p-5 overflow-hidden flex flex-col gap-4">
          {/* Top accent line */}
          <div className={`absolute top-0 left-0 right-0 h-1.5 ${isHospital ? 'bg-blue-500' : isRestaurant ? 'bg-amber-500' : 'bg-purple-500'}`} />
          
          <div className="flex items-center justify-between mt-1">
            <span className={`text-[10px] uppercase tracking-wider font-semibold px-2.5 py-0.5 rounded-full border 
              ${isHospital ? 'bg-blue-900/40 text-blue-300 border-blue-800/60' : 'bg-amber-900/40 text-amber-300 border-amber-800/60'}`}>
              {isHospital ? 'Apollo Clinic' : 'The Leela Dining'}
            </span>
            <div className="flex items-center gap-1 text-green-400 text-xs font-medium">
              <CheckCircle className="w-3.5 h-3.5 fill-green-900/30" />
              <span>Confirmed</span>
            </div>
          </div>

          <div className="space-y-3 mt-2 text-sm text-left">
            {isHospital && (
              <>
                <div className="flex items-start gap-3">
                  <User className="w-4 h-4 text-blue-400 mt-0.5" />
                  <div>
                    <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Patient Name</p>
                    <p className="font-semibold text-white mt-0.5">{data.patient_name}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Activity className="w-4 h-4 text-blue-400 mt-0.5" />
                  <div>
                    <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Dept & Doctor</p>
                    <p className="font-semibold text-white mt-0.5">{data.department} — {data.doctor_name}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Calendar className="w-4 h-4 text-blue-400 mt-0.5" />
                  <div>
                    <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Appointment Date</p>
                    <p className="font-semibold text-white mt-0.5">{data.preferred_date}</p>
                  </div>
                </div>
              </>
            )}

            {isRestaurant && (
              <>
                <div className="flex items-start gap-3">
                  <User className="w-4 h-4 text-amber-400 mt-0.5" />
                  <div>
                    <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Guest Name</p>
                    <p className="font-semibold text-white mt-0.5">{data.guest_name}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Utensils className="w-4 h-4 text-amber-400 mt-0.5" />
                  <div>
                    <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Venue</p>
                    <p className="font-semibold text-white mt-0.5">{data.restaurant}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Clock className="w-4 h-4 text-amber-400 mt-0.5" />
                  <div>
                    <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Date / Time / Party</p>
                    <p className="font-semibold text-white mt-0.5">{data.date} at {data.time} ({data.guests} Guests)</p>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="border-t border-dashed border-gray-800 pt-4 mt-2 flex flex-col items-center justify-center gap-1.5">
            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-medium">Booking ID Reference</span>
            <span className="text-xs font-mono font-bold tracking-wider text-gray-300 bg-gray-900 border border-gray-800 px-3 py-1 rounded-lg">
              {data.ref_id}
            </span>
          </div>

          {/* Ticket notches */}
          <div className="absolute -left-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-gray-950 rounded-full border border-gray-800" />
          <div className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-gray-950 rounded-full border border-gray-800" />
        </div>
      ) : (
        <div className="bg-gray-950/60 rounded-xl p-5 border border-gray-800 flex flex-col gap-4 text-left">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-semibold text-white">
              {isHospital ? `${data.department} Schedule` : `${data.room_type} Availability`}
            </span>
          </div>

          {isHospital && data.slots && (
            <div className="space-y-2 mt-1">
              <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Available slots for {data.date}:</p>
              <div className="flex flex-col gap-1.5 mt-2">
                {data.slots.map((slot: string, idx: number) => (
                  <div key={idx} className="flex items-center gap-2 bg-gray-900/60 border border-gray-800/80 px-3 py-2 rounded-lg text-xs text-gray-300 hover:border-gray-700 transition-colors">
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    <span>{slot}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {isHotel && (
            <div className="space-y-3 mt-1 text-sm">
              <div className="bg-gray-900/60 border border-gray-800/80 p-3 rounded-lg flex flex-col gap-2">
                <span className="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Description</span>
                <span className="text-xs text-gray-200 font-medium">{data.description}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500 font-medium block uppercase tracking-wide">Check-In</span>
                  <span className="text-gray-300 font-semibold mt-0.5 block">{data.check_in}</span>
                </div>
                <div>
                  <span className="text-gray-500 font-medium block uppercase tracking-wide">Check-Out</span>
                  <span className="text-gray-300 font-semibold mt-0.5 block">{data.check_out}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
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
