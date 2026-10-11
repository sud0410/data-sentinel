import { useCallback, useEffect, useState } from 'react'
import { client } from '../api/client'

const ALLOWED_DAGS = ['daily_aggregation_dag', 'data_quality_dag']

export default function Admin() {
  const [alerts, setAlerts] = useState([])
  const [dagId, setDagId] = useState(ALLOWED_DAGS[0])
  const [triggerStatus, setTriggerStatus] = useState('')
  const [resolvedFilter, setResolvedFilter] = useState('false')
  const [error, setError] = useState('')

  const fetchAlerts = useCallback(async () => {
    try {
      const params = resolvedFilter !== '' ? { resolved: resolvedFilter === 'true' } : {}
      const res = await client.get('/admin/alerts', { params })
      setAlerts(res.data)
    } catch {
      setError('Failed to load alerts')
    }
  }, [resolvedFilter])

  useEffect(() => { fetchAlerts() }, [fetchAlerts])

  async function triggerDag() {
    setTriggerStatus('Triggering…')
    try {
      const res = await client.post('/admin/trigger-dag', { dag_id: dagId, conf: {} })
      setTriggerStatus(`Triggered: ${res.data.dag_run_id} (${res.data.state})`)
    } catch (err) {
      setTriggerStatus(`Error: ${err.response?.data?.detail ?? 'unknown'}`)
    }
  }

  async function resolveAlert(id) {
    try {
      await client.patch(`/admin/alerts/${id}/resolve`)
      fetchAlerts()
    } catch {
      setError('Failed to resolve alert')
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-100">Admin Panel</h1>
        {error && <span className="text-xs text-red-400">{error}</span>}
      </div>

      <div className="card flex flex-col gap-4">
        <h2 className="text-sm font-medium text-slate-300">Trigger DAG Run</h2>
        <div className="flex gap-3 flex-wrap items-end">
          <div>
            <label htmlFor="dag-select" className="block text-xs text-slate-500 mb-1">DAG</label>
            <select
              id="dag-select"
              className="input w-64"
              value={dagId}
              onChange={(e) => setDagId(e.target.value)}
            >
              {ALLOWED_DAGS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <button id="trigger-dag-btn" onClick={triggerDag} className="btn-primary">
            Trigger
          </button>
        </div>
        {triggerStatus && (
          <p className="text-xs text-slate-400 font-mono bg-surface-700 px-3 py-2 rounded-lg">{triggerStatus}</p>
        )}
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-slate-300">Alert History</h2>
          <select
            id="alert-filter"
            className="input w-36 text-xs"
            value={resolvedFilter}
            onChange={(e) => setResolvedFilter(e.target.value)}
          >
            <option value="false">Open</option>
            <option value="true">Resolved</option>
            <option value="">All</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wider border-b border-white/5">
                <th className="pb-2 pr-4">Source</th>
                <th className="pb-2 pr-4">Severity</th>
                <th className="pb-2 pr-4">Message</th>
                <th className="pb-2 pr-4">Created</th>
                <th className="pb-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id} className="table-row">
                  <td className="py-2.5 pr-4 font-mono text-xs text-slate-300">{a.source}</td>
                  <td className="py-2.5 pr-4">
                    <span className={a.severity === 'critical' ? 'badge-failure' : 'badge-running'}>
                      {a.severity}
                    </span>
                  </td>
                  <td className="py-2.5 pr-4 text-slate-400 text-xs max-w-xs truncate">{a.message}</td>
                  <td className="py-2.5 pr-4 text-slate-400 text-xs">{new Date(a.created_at).toLocaleString()}</td>
                  <td className="py-2.5">
                    {!a.resolved && (
                      <button
                        onClick={() => resolveAlert(a.id)}
                        className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                      >
                        Resolve
                      </button>
                    )}
                    {a.resolved && <span className="badge-success">resolved</span>}
                  </td>
                </tr>
              ))}
              {alerts.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-600 text-xs">No alerts</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
