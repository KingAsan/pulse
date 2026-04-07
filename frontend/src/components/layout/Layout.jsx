import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import './Layout.css'

export default function Layout() {
  return (
    <div className="layout">
      <Navbar />
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <span className="footer-logo">EntertainMe</span>
              <p>Your personal entertainment assistant</p>
            </div>
            <div className="footer-links">
              <span>Movies</span>
              <span>Books</span>
              <span>Music</span>
              <span>Events</span>
            </div>
            <div className="footer-copy">
              &copy; 2026 EntertainMe. Diploma Project.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
