import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Phone, Plus, Trash2, Mic, Calendar } from 'lucide-react'
import { agentApi } from '../lib/api'

// Demo agents — always shown
const DEMO_AGENTS = [
  {
    agent_id: 'apollo-receptionist',
    name: 'Priya (English)',
    role: 'Receptionist at Apollo Hospitals Chennai',
    industry: 'healthcare',
    language: 'en',
    isDemo: true,
  },
  {
    agent_id: 'apollo-receptionist-hindi',
    name: 'Priya (Hindi)',
    role: 'Receptionist at Apollo Hospitals Chennai',
    industry: 'healthcare',
    language: 'hi',
    isDemo: true,
  },
  {
    agent_id: 'leela-concierge',
    name: 'Arjun (English)',
    role: 'Concierge at The Leela Palace Chennai',
    industry: 'hospitality',
    language: 'en',
    isDemo: true,
  },
  {
    agent_id: 'leela-concierge-tamil',
    name: 'Arjun (Tamil)',
    role: 'Concierge at The Leela Palace Chennai',
    industry: 'hospitality',
    language: 'ta',
    isDemo: true,
  },
]

const INDUSTRY_COLORS: Record<string, string> = {
  healthcare: 'bg-blue-900/40 text-blue-300 border-blue-800',
  hospitality: 'bg-amber-900/40 text-amber-300 border-amber-800',
  hr: 'bg-purple-900/40 text-purple-300 border-purple-800',
  edtech: 'bg-green-900/40 text-green-300 border-green-800',
  custom: 'bg-gray-800 text-gray-300 border-gray-700',
}

export function Dashboard() {
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    agentApi.list()
      .then((r) => setAgents(r.data.agents ?? []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (agentId: string) => {
    if (!confirm('Delete this agent?')) return
    await agentApi.delete(agentId)
    setAgents((prev) => prev.filter((a) => a.agent_id !== agentId))
  }

  const allAgents = [...DEMO_AGENTS, ...agents]

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">VoiceAgent Studio</h1>
          <p className="text-sm text-gray-400 mt-1">Multilingual voice AI agents for real industries</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/appointments"
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm font-medium transition-colors"
          >
            <Calendar className="w-4 h-4 text-blue-400" />
            My Appointments
          </Link>
          <Link
            to="/build"
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Agent
          </Link>
        </div>
      </div>

      {/* Agent grid */}
      {loading ? (
        <div className="text-gray-500 text-sm">Loading agents...</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {allAgents.map((agent) => (
            <AgentCard
              key={agent.agent_id}
              agent={agent}
              onDelete={agent.isDemo ? undefined : () => handleDelete(agent.agent_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function AgentCard({ agent, onDelete }: { agent: any; onDelete?: () => void }) {
  const colorClass = INDUSTRY_COLORS[agent.industry] ?? INDUSTRY_COLORS.custom

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-4 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center text-lg font-semibold">
            {agent.name[0]}
          </div>
          <div>
            <p className="font-medium text-white">{agent.name}</p>
            <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{agent.role}</p>
          </div>
        </div>
        {agent.isDemo && (
          <span className="text-xs bg-blue-900/50 text-blue-400 px-2 py-0.5 rounded-full border border-blue-800">
            Demo
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-xs px-2 py-0.5 rounded-full border ${colorClass}`}>
          {agent.industry}
        </span>
        <span className="text-xs text-gray-500">
          {agent.language === 'hi' ? 'Hindi' : agent.language === 'ta' ? 'Tamil' : 'English'}
        </span>
      </div>

      <div className="flex gap-2 mt-auto">
        <Link
          to={`/call/${agent.agent_id}`}
          className="flex-1 flex items-center justify-center gap-2 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors"
        >
          <Phone className="w-3.5 h-3.5" />
          Call
        </Link>
        {onDelete && (
          <button
            onClick={onDelete}
            className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}
