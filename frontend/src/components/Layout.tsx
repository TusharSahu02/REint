import { NavLink, Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">Wind Forecast Monitor</div>
        <nav>
          <NavLink to="/" end>
            Decision view
          </NavLink>
          <NavLink to="/accuracy">
            Accuracy
          </NavLink>
          <NavLink to="/methodology">
            Methodology
          </NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
