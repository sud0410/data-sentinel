import { useCallback, useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { client } from '../api/client'

const STATUS_CLASS = {
  success: 'badge-success',
  failed: 'badge-failure',
  running: 'badge-running',
}

function StatCard({ label, value, unit }) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <span className="stat-value">
        {value ?? '—'}
        {unit && <span className="text-sm text-slate-500 ml-1">{unit}</span>}
      </span>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [runs, setRuns] = useState([])
  const [error, setError] = useState('')

  const fetchAll = useCallback(async () => {
    try {
      const [s, r] = await Promise.all([
        client.get('/pipeline/stats'),
        client.get('/pipeline/runs', { params: { limit: 20 } }),
      ])
      setStats(s.data)
      setRuns(r.data)
    } catch {
      setError('Failed to load pipeline data')
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, 10_000)
    return () => clearInterval(id)
  }, [fetchAll])

  const chartData = runs
    .slice()
    .reverse()
    .map((r) => ({
      dag: r.dag_id.replace('_dag', ''),
      rows: r.row_count ?? 0,
      date: new Date(r.run_date).toLocaleDateString(),
    }))

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-100">Pipeline Dashboard</h1>
        {error && <span className="text-xs text-red-400">{error}</span>}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Total Transactions" value={stats?.total_transactions?.toLocaleString()} />
        <StatCard label="Last Hour" value={stats?.transactions_last_hour?.toLocaleString()} />
        <StatCard label="Ingestion Rate" value={stats?.ingestion_rate_per_minute?.toFixed(1)} unit="/min" />
        <StatCard label="Last Run" value={stats?.last_run_status ?? '—'} />
      </div>

      <div className="card">
        <h2 className="text-sm font-medium text-slate-300 mb-4">Row Count per Run</h2>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} />
            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#16162a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8 }}
              labelStyle={{ color: '#94a3b8' }}
              itemStyle={{ color: '#818cf8' }}
            />
            <Bar dataKey="rows" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h2 className="text-sm font-medium text-slate-300 mb-4">Recent Pipeline Runs</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-white/5">
                <th className="pb-2 pr-4">DAG</th>
                <th className="pb-2 pr-4">Date</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Rows</th>
                <th className="pb-2">Duration</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => {
                const duration =
                  r.started_at && r.finished_at
                    ? `${Math.round((new Date(r.finished_at) - new Date(r.started_at)) / 1000)}s`
                    : '—'
                return (
                  <tr key={r.id} className="table-row">
                    <td className="py-2.5 pr-4 font-mono text-xs text-slate-300">{r.dag_id}</td>
                    <td className="py-2.5 pr-4 text-slate-400 text-xs">{new Date(r.run_date).toLocaleString()}</td>
                    <td className="py-2.5 pr-4">
                      <span className={STATUS_CLASS[r.status] ?? 'badge-running'}>{r.status}</span>
                    </td>
                    <td className="py-2.5 pr-4 text-slate-400 font-mono text-xs">{r.row_count ?? '—'}</td>
                    <td className="py-2.5 text-slate-400 text-xs">{duration}</td>
                  </tr>
                )
              })}
              {runs.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-600 text-xs">No runs yet</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
