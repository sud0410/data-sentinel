import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/dq', label: 'Data Quality' },
  { to: '/lineage', label: 'Lineage' },
]

export default function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="border-b border-white/5 bg-surface-800/80 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <span className="font-semibold text-sm tracking-tight text-slate-100">
            <span className="text-brand-500">Data</span>Sentinel
          </span>
          <nav className="flex items-center gap-1">
            {links.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm transition-colors duration-150 ${
                    isActive
                      ? 'bg-brand-500/10 text-brand-400'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
            {user?.role === 'admin' && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm transition-colors duration-150 ${
                    isActive
                      ? 'bg-brand-500/10 text-brand-400'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`
                }
              >
                Admin
              </NavLink>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500 font-mono">{user?.username}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
            user?.role === 'admin' ? 'bg-brand-500/15 text-brand-400' : 'bg-surface-600 text-slate-400'
          }`}>
            {user?.role}
          </span>
          <button
            onClick={logout}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  )
}
