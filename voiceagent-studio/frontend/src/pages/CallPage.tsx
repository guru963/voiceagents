import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { CallView } from '../components/call/CallView'

export function CallPage() {
  const { agentId } = useParams<{ agentId: string }>()
  const navigate = useNavigate()

  const nameMap: Record<string, string> = {
    'apollo-receptionist': 'Priya (English)',
    'apollo-receptionist-hindi': 'Priya (Hindi)',
    'leela-concierge': 'Arjun (English)',
    'leela-concierge-tamil': 'Arjun (Tamil)',
  }

  const name = nameMap[agentId!] ?? 'Agent'

  return (
    <div className="max-w-2xl mx-auto px-6 py-10 space-y-6">
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to agents
      </button>
      <h2 className="text-xl font-semibold">Call with {name}</h2>
      <CallView agentId={agentId!} agentName={name} onEnd={() => navigate('/')} />
    </div>
  )
}
