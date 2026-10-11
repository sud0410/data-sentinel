import { useCallback, useEffect, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { client } from '../api/client'

const CHECK_COLORS = {
  null_rate: '#f59e0b',
  row_count_drift: '#6366f1',
  duplicate_count: '#ef4444',
}

export default function DQMetrics() {
  const [metrics, setMetrics] = useState([])
  const [filter, setFilter] = useState('')
  const [error, setError] = useState('')

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await client.get('/dq/metrics', { params: { limit: 200 } })
      setMetrics(res.data)
    } catch {
      setError('Failed to load DQ metrics')
    }
  }, [])

  useEffect(() => { fetchMetrics() }, [fetchMetrics])

  const checks = [...new Set(metrics.map((m) => m.check_name))]

  const filtered = filter ? metrics.filter((m) => m.check_name === filter) : metrics

  const chartData = filtered
    .slice()
    .reverse()
    .map((m) => ({
      date: new Date(m.computed_at).toLocaleDateString(),
      [m.check_name]: parseFloat(m.metric_value ?? 0),
      passed: m.passed,
    }))

  const grouped = checks.reduce((acc, c) => {
    acc[c] = metrics.filter((m) => m.check_name === c)
    return acc
  }, {})

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-100">Data Quality Metrics</h1>
        {error && <span className="text-xs text-red-400">{error}</span>}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {checks.map((c) => {
          const latest = grouped[c]?.[0]
          return (
            <div key={c} className="stat-card border-l-2" style={{ borderColor: CHECK_COLORS[c] ?? '#6366f1' }}>
              <span className="stat-label">{c.replace(/_/g, ' ')}</span>
              <span className="stat-value text-xl">
                {latest ? parseFloat(latest.metric_value ?? 0).toFixed(4) : '—'}
              </span>
              {latest && (
                <span className={latest.passed ? 'badge-success' : 'badge-failure'}>
                  {latest.passed ? 'pass' : 'fail'}
                </span>
              )}
            </div>
          )
        })}
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-slate-300">Metric Trend</h2>
          <select
            id="dq-filter"
            className="input w-44 text-xs"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="">All checks</option>
            {checks.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} />
            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#16162a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8 }}
              labelStyle={{ color: '#94a3b8' }}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
            {(filter ? [filter] : checks).map((c) => (
              <Line
                key={c}
                type="monotone"
                dataKey={c}
                stroke={CHECK_COLORS[c] ?? '#6366f1'}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h2 className="text-sm font-medium text-slate-300 mb-4">Check History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-white/5">
                <th className="pb-2 pr-4">Check</th>
                <th className="pb-2 pr-4">Value</th>
                <th className="pb-2 pr-4">Threshold</th>
                <th className="pb-2 pr-4">Result</th>
                <th className="pb-2">Computed At</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 50).map((m) => (
                <tr key={m.id} className="table-row">
                  <td className="py-2.5 pr-4 font-mono text-xs text-slate-300">{m.check_name}</td>
                  <td className="py-2.5 pr-4 text-slate-400 font-mono text-xs">{parseFloat(m.metric_value ?? 0).toFixed(4)}</td>
                  <td className="py-2.5 pr-4 text-slate-400 font-mono text-xs">{parseFloat(m.threshold ?? 0).toFixed(4)}</td>
                  <td className="py-2.5 pr-4">
                    <span className={m.passed ? 'badge-success' : 'badge-failure'}>
                      {m.passed ? 'pass' : 'fail'}
                    </span>
                  </td>
                  <td className="py-2.5 text-slate-400 text-xs">{new Date(m.computed_at).toLocaleString()}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-600 text-xs">No data</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
