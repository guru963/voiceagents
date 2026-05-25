import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { AgentBuilder } from '../components/builder/AgentBuilder'

export function BuilderPage() {
  const navigate = useNavigate()
  return (
    <div className="max-w-2xl mx-auto px-6 py-10 space-y-6">
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>
      <AgentBuilder onCreated={() => navigate('/')} />
    </div>
  )
}
