import { NavLink, Outlet } from 'react-router-dom'

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
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <Mark />
          Wind Forecast Monitor
        </div>
        <nav>
          <NavLink to="/" end>
            Decision view
          </NavLink>
          <NavLink to="/accuracy">Accuracy</NavLink>
          <NavLink to="/methodology">Methodology</NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
