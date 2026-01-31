import { Link, useLocation } from 'react-router-dom'
import './Layout.css'

function Layout({ children }) {
  const location = useLocation()

  return (
    <div className="layout">
      <header className="header">
        <div className="container">
          <h1 className="logo">ERP Incident Portal</h1>
          <nav className="nav">
            <Link 
              to="/" 
              className={location.pathname === '/' ? 'active' : ''}
            >
              Incidents
            </Link>
            <Link 
              to="/incidents/new" 
              className={location.pathname === '/incidents/new' ? 'active' : ''}
            >
              New Incident
            </Link>
          </nav>
        </div>
      </header>
      <main className="main">
        <div className="container">
          {children}
        </div>
      </main>
    </div>
  )
}

export default Layout
