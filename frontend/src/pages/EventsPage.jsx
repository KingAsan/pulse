import { useState, useEffect } from 'react'
import api from '../api/client'
import './EventsPage.css'

export default function EventsPage() {
  const [events, setEvents] = useState([])
  const [types, setTypes] = useState([])
  const [cities, setCities] = useState([])
  const [activeType, setActiveType] = useState('')
  const [activeCity, setActiveCity] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/events/browse').then(r => setEvents(r.data)),
      api.get('/api/events/types').then(r => setTypes(r.data)),
      api.get('/api/events/cities').then(r => setCities(r.data)),
    ]).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleFilter = (type, city) => {
    setActiveType(type || '')
    setActiveCity(city || '')
    setLoading(true)
    const params = new URLSearchParams()
    if (type) params.set('type', type)
    if (city) params.set('city', city)
    api.get(`/api/events/browse?${params}`).then(r => setEvents(r.data)).finally(() => setLoading(false))
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (query.trim()) {
      setLoading(true)
      api.get(`/api/events/search?q=${encodeURIComponent(query)}`).then(r => setEvents(r.data)).finally(() => setLoading(false))
    }
  }

  return (
    <div className="container events-page">
      <div className="page-header">
        <h1>Events</h1>
        <p>Discover concerts, shows, festivals and more</p>
      </div>

      <form onSubmit={handleSearch} className="search-bar">
        <input type="text" className="input" placeholder="Search events..."
          value={query} onChange={e => setQuery(e.target.value)} />
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      <div className="events-filters">
        <div className="filter-group">
          <label>City</label>
          <select className="input" value={activeCity} onChange={e => handleFilter(activeType, e.target.value)}>
            <option value="">All Cities</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div className="filter-group">
          <label>Type</label>
          <select className="input" value={activeType} onChange={e => handleFilter(e.target.value, activeCity)}>
            <option value="">All Types</option>
            {types.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loader"><div className="spinner"></div></div>
      ) : events.length === 0 ? (
        <div className="empty-state"><h3>No events found</h3></div>
      ) : (
        <div className="events-grid">
          {events.map(e => (
            <div key={e.id} className="event-card">
              <div className="event-card-header">
                <div className="event-date-lg">
                  <span className="event-day-lg">{new Date(e.date).getDate()}</span>
                  <span className="event-month-lg">{new Date(e.date).toLocaleString('en', { month: 'short' })}</span>
                  <span className="event-year-lg">{new Date(e.date).getFullYear()}</span>
                </div>
                <span className="badge badge-accent">{e.type}</span>
              </div>
              <h3 className="event-card-title">{e.title}</h3>
              <p className="event-card-desc">{e.description}</p>
              <div className="event-card-meta">
                <div className="event-meta-item">
                  <span className="meta-icon">&#128205;</span>
                  <span>{e.venue}, {e.city}</span>
                </div>
                <div className="event-meta-item">
                  <span className="meta-icon">&#128337;</span>
                  <span>{e.time}</span>
                </div>
                <div className="event-meta-item">
                  <span className="meta-icon">&#128176;</span>
                  <span>{e.price}</span>
                </div>
              </div>
              <div className="event-card-genres">
                {e.genres?.map(g => <span key={g} className="badge badge-accent">{g}</span>)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
