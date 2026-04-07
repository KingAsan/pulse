import { useState, useEffect } from 'react'
import Card from '../components/common/Card'
import api from '../api/client'
import './BooksPage.css'

const SUBJECTS = ['Fiction', 'Science Fiction', 'Fantasy', 'Mystery', 'Romance', 'History', 'Science', 'Philosophy', 'Classic', 'Adventure']

export default function BooksPage() {
  const [books, setBooks] = useState([])
  const [activeSubject, setActiveSubject] = useState(null)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/api/books/trending')
      .then(r => setBooks(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    if (query.trim()) {
      setLoading(true)
      setActiveSubject(null)
      api.get(`/api/books/search?q=${encodeURIComponent(query)}`)
        .then(r => setBooks(r.data))
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }

  const handleSubject = (subject) => {
    setActiveSubject(subject)
    setQuery('')
    setLoading(true)
    api.get(`/api/books/subjects/${subject.toLowerCase()}`)
      .then(r => setBooks(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  return (
    <div className="container books-page">
      <div className="page-header">
        <h1>Books</h1>
        <p>Search and discover your next great read</p>
      </div>

      <form onSubmit={handleSearch} className="search-bar">
        <input
          type="text"
          className="input"
          placeholder="Search books by title or author..."
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      <div className="tabs">
        <button className={`tab ${!activeSubject ? 'active' : ''}`} onClick={() => { setActiveSubject(null); setQuery(''); setLoading(true); api.get('/api/books/trending').then(r => setBooks(r.data)).finally(() => setLoading(false)) }}>
          Trending
        </button>
        {SUBJECTS.map(s => (
          <button key={s} className={`tab ${activeSubject === s ? 'active' : ''}`} onClick={() => handleSubject(s)}>
            {s}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loader"><div className="spinner"></div></div>
      ) : books.length === 0 ? (
        <div className="empty-state">
          <h3>No books found</h3>
          <p>Try a different search or browse by subject</p>
        </div>
      ) : (
        <div className="grid">
          {books.map((b, i) => (
            <Card
              key={b.key || i}
              type="book"
              image={b.cover_url}
              title={b.title}
              subtitle={b.authors?.join(', ')}
              rating={b.rating}
              link={`/books/${encodeURIComponent(b.key)}`}
            />
          ))}
        </div>
      )}
    </div>
  )
}
