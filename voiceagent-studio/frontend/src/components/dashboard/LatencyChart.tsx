import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend, CartesianGrid,
} from 'recharts'

interface LatencyPoint {
  turn: number
  stt: number
  llm: number
  tts: number
}

export function LatencyChart({ data }: { data: LatencyPoint[] }) {
  const latest = data[data.length - 1]
  const avg = (key: keyof LatencyPoint) =>
    Math.round(data.reduce((s, d) => s + (d[key] as number), 0) / data.length)

  return (
    <div className="bg-gray-900 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-300">Pipeline Latency</h3>
        {latest && (
          <span className="text-xs text-gray-400">
            Last: {(latest.stt + latest.llm + latest.tts).toFixed(0)}ms total
          </span>
        )}
      </div>

      {/* Summary pills */}
      <div className="flex gap-3">
        {[
          { label: 'STT', color: 'bg-blue-500', key: 'stt' },
          { label: 'LLM', color: 'bg-purple-500', key: 'llm' },
          { label: 'TTS', color: 'bg-green-500', key: 'tts' },
        ].map(({ label, color, key }) => (
          <div key={key} className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${color}`} />
            <span className="text-xs text-gray-400">
              {label} avg {avg(key as keyof LatencyPoint)}ms
            </span>
          </div>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="turn" tick={{ fontSize: 10, fill: '#6b7280' }} />
          <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} unit="ms" />
          <Tooltip
            contentStyle={{ background: '#1f2937', border: 'none', borderRadius: 8 }}
            labelStyle={{ color: '#e5e7eb' }}
            formatter={(value: number) => [`${value}ms`]}
          />
          <Bar dataKey="stt" stackId="a" fill="#3b82f6" name="STT" />
          <Bar dataKey="llm" stackId="a" fill="#8b5cf6" name="LLM" />
          <Bar dataKey="tts" stackId="a" fill="#10b981" name="TTS" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
