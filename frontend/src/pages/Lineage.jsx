const NODES = [
  { id: 'kafka-producer', label: 'Kafka Producer', sub: 'Transaction Simulator', x: 60, y: 160, color: '#6366f1' },
  { id: 'kafka-topic', label: 'Kafka Topic', sub: 'financial.transactions', x: 260, y: 160, color: '#8b5cf6' },
  { id: 'kafka-consumer', label: 'Kafka Consumer', sub: 'Schema Validator', x: 460, y: 160, color: '#6366f1' },
  { id: 'postgres', label: 'PostgreSQL', sub: 'Raw transactions store', x: 660, y: 60, color: '#0ea5e9' },
  { id: 'airflow', label: 'Airflow DAGs', sub: 'Aggregation · DQ Checks', x: 660, y: 260, color: '#f59e0b' },
  { id: 'fastapi', label: 'FastAPI Backend', sub: 'REST API · JWT Auth', x: 880, y: 160, color: '#10b981' },
  { id: 'frontend', label: 'React Frontend', sub: 'Dashboard · Admin', x: 1080, y: 160, color: '#ec4899' },
]

const EDGES = [
  { from: 'kafka-producer', to: 'kafka-topic' },
  { from: 'kafka-topic', to: 'kafka-consumer' },
  { from: 'kafka-consumer', to: 'postgres' },
  { from: 'kafka-consumer', to: 'airflow' },
  { from: 'postgres', to: 'fastapi' },
  { from: 'airflow', to: 'fastapi' },
  { from: 'fastapi', to: 'frontend' },
]

const NODE_W = 140
const NODE_H = 64

function getCenter(node) {
  return { cx: node.x + NODE_W / 2, cy: node.y + NODE_H / 2 }
}

export default function Lineage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Data Lineage</h1>
        <p className="text-xs text-slate-500 mt-0.5">End-to-end flow from transaction source to dashboard</p>
      </div>

      <div className="card overflow-x-auto">
        <svg
          viewBox="0 0 1260 380"
          width="100%"
          style={{ minWidth: 760 }}
          aria-label="Data lineage diagram"
        >
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill="rgba(255,255,255,0.2)" />
            </marker>
          </defs>

          {EDGES.map((edge, i) => {
            const from = NODES.find((n) => n.id === edge.from)
            const to = NODES.find((n) => n.id === edge.to)
            const f = getCenter(from)
            const t = getCenter(to)
            const mx = (f.cx + t.cx) / 2
            return (
              <path
                key={i}
                d={`M ${f.cx} ${f.cy} C ${mx} ${f.cy}, ${mx} ${t.cy}, ${t.cx} ${t.cy}`}
                fill="none"
                stroke="rgba(255,255,255,0.12)"
                strokeWidth="1.5"
                markerEnd="url(#arrow)"
              />
            )
          })}

          {NODES.map((node) => {
            const { cx, cy } = getCenter(node)
            return (
              <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
                <rect
                  width={NODE_W}
                  height={NODE_H}
                  rx={10}
                  fill={`${node.color}18`}
                  stroke={`${node.color}60`}
                  strokeWidth="1"
                />
                <text x={NODE_W / 2} y={24} textAnchor="middle" fill="#e2e8f0" fontSize="12" fontWeight="600" fontFamily="Inter">
                  {node.label}
                </text>
                <text x={NODE_W / 2} y={42} textAnchor="middle" fill="#64748b" fontSize="10" fontFamily="Inter">
                  {node.sub}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { phase: 'Ingestion', steps: ['Kafka producer simulates transactions', 'Events published to Kafka topic', 'Consumer validates schema (Pydantic)', 'Validated rows written to PostgreSQL'], color: '#6366f1' },
          { phase: 'Transformation', steps: ['Airflow daily aggregation DAG', 'Spend aggregated per user + category', 'DQ checks: null rate, drift, duplicates', 'Results written to dq_metrics table'], color: '#f59e0b' },
          { phase: 'Serving', steps: ['FastAPI reads from PostgreSQL', 'JWT-secured REST endpoints', 'React dashboard polls /pipeline/stats', 'Admin can trigger DAGs via API'], color: '#10b981' },
        ].map(({ phase, steps, color }) => (
          <div key={phase} className="card border-t-2" style={{ borderColor: color }}>
            <h3 className="text-sm font-medium text-slate-200 mb-3">{phase}</h3>
            <ul className="flex flex-col gap-1.5">
              {steps.map((s) => (
                <li key={s} className="text-xs text-slate-400 flex gap-2">
                  <span style={{ color }} className="mt-0.5">›</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}
