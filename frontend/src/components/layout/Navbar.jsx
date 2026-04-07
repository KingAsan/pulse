import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useState } from 'react'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const links = [
    { path: '/', label: 'Home' },
    { path: '/movies', label: 'Movies' },
    { path: '/books', label: 'Books' },
    { path: '/music', label: 'Music' },
    { path: '/events', label: 'Events' },
    { path: '/cinema', label: 'Cinema' },
  ]

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/movies?q=${encodeURIComponent(searchQuery.trim())}`)
      setSearchQuery('')
    }
  }

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="navbar-brand">
          <span className="brand-icon">E</span>
          <span className="brand-text">EntertainMe</span>
        </Link>

        <div className="navbar-links">
          {links.map(link => (
            <Link
              key={link.path}
              to={link.path}
              className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="navbar-right">
          <form onSubmit={handleSearch} className="navbar-search">
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </form>

          {user ? (
            <div className="navbar-user">
              <Link to="/profile" className="nav-link user-link">
                <span className="user-avatar">{user.username[0].toUpperCase()}</span>
                <span className="user-name">{user.username}</span>
              </Link>
              <button onClick={logout} className="btn btn-sm btn-secondary">Exit</button>
            </div>
          ) : (
            <div className="navbar-auth">
              <Link to="/login" className="btn btn-sm btn-secondary">Login</Link>
              <Link to="/register" className="btn btn-sm btn-primary">Register</Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
