import { NavLink, Outlet } from 'react-router-dom'
import { TIMEZONES, setTimezone, useTimezone } from '../tz'

function Mark() {
  return (
    <svg viewBox="0 0 32 32" width="24" height="24" aria-hidden="true">
      <rect width="32" height="32" rx="7" fill="oklch(0.47 0.11 240)" />
      <g
        stroke="oklch(0.97 0.01 245)"
        strokeWidth="2.6"
        strokeLinecap="round"
        fill="none"
      >
        <path d="M6 11h13a3.2 3.2 0 1 0-3.1-4" />
        <path d="M6 17h16a3.2 3.2 0 1 1-3.1 4" />
        <path d="M6 23h8" />
      </g>
    </svg>
  )
}

export default function Layout() {
  const tz = useTimezone()
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <Mark />
          Wind Forecast Monitor
        </div>
        <div className="topbar-right">
          <nav>
            <NavLink to="/" end>
              Decision view
            </NavLink>
            <NavLink to="/accuracy">Accuracy</NavLink>
            <NavLink to="/methodology">Methodology</NavLink>
          </nav>
          <select
            className="tz-select"
            value={tz}
            onChange={(e) => setTimezone(e.target.value)}
            aria-label="Display timezone"
            title="Times shown in this timezone. The decision cutoff stays 09:00 Europe/London."
          >
            {TIMEZONES.map((t) => (
              <option key={t.id} value={t.id}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
