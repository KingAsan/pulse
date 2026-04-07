import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Card from '../components/common/Card'
import api from '../api/client'
import './HomePage.css'

export default function HomePage() {
  const { user } = useAuth()
  const [trending, setTrending] = useState([])
  const [books, setBooks] = useState([])
  const [music, setMusic] = useState([])
  const [events, setEvents] = useState([])
  const [forYou, setForYou] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/movies/trending').then(r => setTrending(r.data.slice(0, 10))),
      api.get('/api/books/trending').then(r => setBooks(r.data.slice(0, 10))),
      api.get('/api/music/browse').then(r => setMusic(r.data.slice(0, 10))),
      api.get('/api/events/browse').then(r => setEvents(r.data.slice(0, 8))),
    ]).catch(() => {}).finally(() => setLoading(false))

    if (user) {
      api.get('/api/recommendations/for-you').then(r => setForYou(r.data)).catch(() => {})
    }
  }, [user])

  const hero = trending[0]

  if (loading) {
    return <div className="loader"><div className="spinner"></div></div>
  }

  return (
    <div className="home-page">
      {hero && (
        <section className="hero">
          <div className="hero-bg" style={hero.backdrop_url ? { backgroundImage: `url(${hero.backdrop_url})` } : {}}>
            <div className="hero-overlay">
              <div className="container hero-content">
                <h1 className="hero-title">{hero.title}</h1>
                <p className="hero-desc">{hero.overview?.slice(0, 200)}</p>
                <div className="hero-meta">
                  {hero.vote_average > 0 && <span className="rating-badge">&#9733; {hero.vote_average.toFixed(1)}</span>}
                  {hero.release_date && <span className="badge badge-accent">{hero.release_date.slice(0, 4)}</span>}
                </div>
                <div className="hero-actions">
                  <Link to={`/movies/${hero.id}`} className="btn btn-primary">Details</Link>
                  <Link to="/movies" className="btn btn-secondary">Browse All Movies</Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      <div className="container home-sections">
        {forYou && (forYou.movies?.length > 0 || forYou.books?.length > 0) && (
          <section className="home-section">
            <div className="section-header">
              <h2 className="section-title">Recommended for You</h2>
            </div>
            <div className="carousel">
              {forYou.movies?.map(m => (
                <Card key={`m-${m.id}`} type="movie" image={m.poster_url} title={m.title}
                  subtitle={m.release_date?.slice(0, 4)} rating={m.vote_average} link={`/movies/${m.id}`} />
              ))}
              {forYou.books?.map(b => (
                <Card key={`b-${b.key}`} type="book" image={b.cover_url} title={b.title}
                  subtitle={b.authors?.join(', ')} link={`/books/${encodeURIComponent(b.key)}`} />
              ))}
            </div>
          </section>
        )}

        <section className="home-section">
          <div className="section-header">
            <h2 className="section-title">Trending Movies</h2>
            <Link to="/movies" className="section-link">See All &rarr;</Link>
          </div>
          <div className="carousel">
            {trending.map(m => (
              <Card key={m.id} type="movie" image={m.poster_url} title={m.title}
                subtitle={m.release_date?.slice(0, 4)} rating={m.vote_average} link={`/movies/${m.id}`} />
            ))}
          </div>
        </section>

        <section className="home-section">
          <div className="section-header">
            <h2 className="section-title">Popular Books</h2>
            <Link to="/books" className="section-link">See All &rarr;</Link>
          </div>
          <div className="carousel">
            {books.map((b, i) => (
              <Card key={b.key || i} type="book" image={b.cover_url} title={b.title}
                subtitle={b.authors?.join(', ')} rating={b.rating} link={`/books/${encodeURIComponent(b.key)}`} />
            ))}
          </div>
        </section>

        <section className="home-section">
          <div className="section-header">
            <h2 className="section-title">Music</h2>
            <Link to="/music" className="section-link">See All &rarr;</Link>
          </div>
          <div className="carousel">
            {music.map(t => (
              <div key={t.id} className="music-card-mini">
                <div className="music-card-icon">&#9835;</div>
                <div className="music-card-info">
                  <span className="music-card-title">{t.title}</span>
                  <span className="music-card-artist">{t.artist}</span>
                </div>
                <span className="music-card-duration">{t.duration}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="home-section">
          <div className="section-header">
            <h2 className="section-title">Upcoming Events</h2>
            <Link to="/events" className="section-link">See All &rarr;</Link>
          </div>
          <div className="grid grid-lg">
            {events.map(e => (
              <div key={e.id} className="event-card-home">
                <div className="event-date-badge">
                  <span className="event-day">{new Date(e.date).getDate()}</span>
                  <span className="event-month">{new Date(e.date).toLocaleString('en', { month: 'short' })}</span>
                </div>
                <div className="event-info">
                  <h3>{e.title}</h3>
                  <p>{e.venue} &middot; {e.city}</p>
                  <span className="badge badge-accent">{e.type}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
