import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Card from '../components/common/Card'
import api from '../api/client'
import './MoviesPage.css'

export default function MoviesPage() {
  const [searchParams] = useSearchParams()
  const [movies, setMovies] = useState([])
  const [genres, setGenres] = useState([])
  const [activeGenre, setActiveGenre] = useState(null)
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/movies/genres').then(r => setGenres(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const q = searchParams.get('q')
    if (q) {
      setQuery(q)
      api.get(`/api/movies/search?q=${encodeURIComponent(q)}`)
        .then(r => setMovies(r.data))
        .catch(() => {})
        .finally(() => setLoading(false))
    } else if (activeGenre) {
      api.get(`/api/movies/discover?genre=${activeGenre}`)
        .then(r => setMovies(r.data))
        .catch(() => {})
        .finally(() => setLoading(false))
    } else {
      api.get('/api/movies/trending')
        .then(r => setMovies(r.data))
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }, [searchParams, activeGenre])

  const handleSearch = (e) => {
    e.preventDefault()
    if (query.trim()) {
      setLoading(true)
      setActiveGenre(null)
      api.get(`/api/movies/search?q=${encodeURIComponent(query)}`)
        .then(r => setMovies(r.data))
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }

  return (
    <div className="container movies-page">
      <div className="page-header">
        <h1>Movies</h1>
        <p>Discover trending films and find your next favorite movie</p>
      </div>

      <form onSubmit={handleSearch} className="search-bar">
        <input
          type="text"
          className="input"
          placeholder="Search movies..."
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      <div className="tabs">
        <button className={`tab ${!activeGenre ? 'active' : ''}`} onClick={() => { setActiveGenre(null); setQuery('') }}>
          Trending
        </button>
        {genres.slice(0, 12).map(g => (
          <button key={g.id} className={`tab ${activeGenre === g.id ? 'active' : ''}`}
            onClick={() => { setActiveGenre(g.id); setQuery('') }}>
            {g.name}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loader"><div className="spinner"></div></div>
      ) : movies.length === 0 ? (
        <div className="empty-state">
          <h3>No movies found</h3>
          <p>Try a different search or browse by genre</p>
        </div>
      ) : (
        <div className="grid">
          {movies.map(m => (
            <Card
              key={m.id}
              type="movie"
              image={m.poster_url}
              title={m.title}
              subtitle={m.release_date?.slice(0, 4)}
              rating={m.vote_average}
              link={`/movies/${m.id}`}
            />
          ))}
        </div>
      )}
    </div>
  )
}
