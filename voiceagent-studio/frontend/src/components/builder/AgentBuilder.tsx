import { useState } from 'react'
import { agentApi } from '../../lib/api'

const INDUSTRIES = ['healthcare', 'hospitality', 'hr', 'edtech', 'custom']
const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi' },
  { value: 'ta', label: 'Tamil' },
]
const TOOLS_BY_INDUSTRY: Record<string, string[]> = {
  healthcare: ['book_appointment', 'check_doctor_availability', 'get_department_info'],
  hospitality: ['book_restaurant', 'check_room_availability', 'get_amenities'],
  hr: [],
  edtech: [],
  custom: [],
}

interface Props {
  onCreated: (agent: any) => void
}

export function AgentBuilder({ onCreated }: Props) {
  const [form, setForm] = useState({
    name: '',
    role: '',
    industry: 'healthcare',
    language: 'en',
    system_prompt: '',
    tts_provider: 'edge_tts',
    tools_enabled: [] as string[],
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [kbFile, setKbFile] = useState<File | null>(null)

  const availableTools = TOOLS_BY_INDUSTRY[form.industry] ?? []

  const toggleTool = (tool: string) => {
    setForm((f) => ({
      ...f,
      tools_enabled: f.tools_enabled.includes(tool)
        ? f.tools_enabled.filter((t) => t !== tool)
        : [...f.tools_enabled, tool],
    }))
  }

  const handleSubmit = async () => {
    if (!form.name || !form.role || !form.system_prompt) {
      setError('Name, role, and system prompt are required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await agentApi.create(form)
      const agentId = res.data.agent_id
      if (kbFile) {
        await agentApi.uploadKB(agentId, kbFile)
      }
      onCreated(res.data.agent)
    } catch (e: any) {
      setError(e.response?.data?.detail ?? 'Failed to create agent')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5 max-w-xl">
      <h2 className="text-lg font-semibold text-white">Create New Agent</h2>

      {error && (
        <p className="text-sm text-red-400 bg-red-900/30 px-3 py-2 rounded">{error}</p>
      )}

      <Field label="Agent Name">
        <input
          className="input"
          placeholder="e.g. Priya"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
      </Field>

      <Field label="Role">
        <input
          className="input"
          placeholder="e.g. Hospital receptionist at Apollo Chennai"
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
        />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Industry">
          <select
            className="input"
            value={form.industry}
            onChange={(e) => setForm({ ...form, industry: e.target.value, tools_enabled: [] })}
          >
            {INDUSTRIES.map((i) => (
              <option key={i} value={i}>{i.charAt(0).toUpperCase() + i.slice(1)}</option>
            ))}
          </select>
        </Field>

        <Field label="Language">
          <select
            className="input"
            value={form.language}
            onChange={(e) => setForm({ ...form, language: e.target.value })}
          >
            {LANGUAGES.map((l) => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>
        </Field>
      </div>

      <Field label="System Prompt">
        <textarea
          className="input h-32 resize-none"
          placeholder="You are Priya, a warm receptionist at Apollo Hospitals..."
          value={form.system_prompt}
          onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
        />
      </Field>

      {availableTools.length > 0 && (
        <Field label="Tools">
          <div className="flex flex-wrap gap-2">
            {availableTools.map((tool) => (
              <button
                key={tool}
                onClick={() => toggleTool(tool)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors
                  ${form.tools_enabled.includes(tool)
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'border-gray-600 text-gray-400 hover:border-gray-400'
                  }`}
              >
                {tool.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </Field>
      )}

      <Field label="Knowledge Base (optional PDF or TXT)">
        <input
          type="file"
          accept=".pdf,.txt"
          className="text-sm text-gray-400"
          onChange={(e) => setKbFile(e.target.files?.[0] ?? null)}
        />
      </Field>

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium disabled:opacity-50 transition-colors"
      >
        {loading ? 'Creating...' : 'Create Agent'}
      </button>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</label>
      {children}
    </div>
  )
}
