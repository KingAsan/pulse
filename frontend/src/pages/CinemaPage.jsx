import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import Card from '../components/common/Card'
import api from '../api/client'
import './CinemaPage.css'

export default function CinemaPage() {
  const { user } = useAuth()
  const [activeSource, setActiveSource] = useState('hdrezka') // 'hdrezka' or 'animevost'
  const [content, setContent] = useState([])
  const [categories, setCategories] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedItem, setSelectedItem] = useState(null)
  const [itemDetail, setItemDetail] = useState(null)

  // Check if user is admin
  const isAdmin = user?.is_admin

  useEffect(() => {
    if (!isAdmin) return
    
    // Load categories based on active source
    if (activeSource === 'hdrezka') {
      api.get('/api/hdrezka/categories')
        .then(r => setCategories(r.data))
        .catch(() => {})
    } else if (activeSource === 'animevost') {
      api.get('/api/animevost/genres')
        .then(r => setCategories(r.data))
        .catch(() => {})
    }
  }, [activeSource, isAdmin])

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false)
      return
    }

    setLoading(true)
    
    if (activeSource === 'hdrezka') {
      if (activeCategory) {
        api.get(`/api/hdrezka/browse?category=${activeCategory}`)
          .then(r => setContent(r.data))
          .catch(() => {})
          .finally(() => setLoading(false))
      } else {
        api.get('/api/hdrezka/browse?category=films')
          .then(r => setContent(r.data))
          .catch(() => {})
          .finally(() => setLoading(false))
      }
    } else if (activeSource === 'animevost') {
      if (activeCategory) {
        api.get(`/api/animevost/genre/${activeCategory}`)
          .then(r => setContent(r.data))
          .catch(() => {})
          .finally(() => setLoading(false))
      } else {
        api.get('/api/animevost/browse')
          .then(r => setContent(r.data))
          .catch(() => {})
          .finally(() => setLoading(false))
      }
    }
  }, [activeSource, activeCategory, isAdmin])

  const handleSearch = (e) => {
    e.preventDefault()
    if (!query.trim() || !isAdmin) return

    setLoading(true)
    setActiveCategory(null)
    
    const endpoint = activeSource === 'hdrezka' 
      ? `/api/hdrezka/search?q=${encodeURIComponent(query)}`
      : `/api/animevost/search?q=${encodeURIComponent(query)}`
    
    api.get(endpoint)
      .then(r => setContent(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const handleItemClick = (item) => {
    if (!isAdmin) return
    
    setSelectedItem(item)
    setItemDetail(null)
    
    const endpoint = activeSource === 'hdrezka'
      ? `/api/hdrezka/detail?url=${encodeURIComponent(item.url)}`
      : `/api/animevost/detail?url=${encodeURIComponent(item.url)}`
    
    api.get(endpoint)
      .then(r => setItemDetail(r.data))
      .catch(() => {})
  }

  const closeDetail = () => {
    setSelectedItem(null)
    setItemDetail(null)
  }

  if (!isAdmin) {
    return (
      <div className="container cinema-page">
        <div className="page-header">
          <h1>Cinema</h1>
          <p>Access restricted to administrators only</p>
        </div>
        <div className="empty-state">
          <h3>Admin Access Required</h3>
          <p>This section is only available for admin users.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container cinema-page">
      <div className="page-header">
        <h1>Cinema</h1>
        <p>Browse movies, series, and anime from multiple sources</p>
      </div>

      {/* Source Selector */}
      <div className="source-selector">
        <button 
          className={`source-btn ${activeSource === 'hdrezka' ? 'active' : ''}`}
          onClick={() => { setActiveSource('hdrezka'); setActiveCategory(null); setQuery('') }}
        >
          HDRezka
        </button>
        <button 
          className={`source-btn ${activeSource === 'animevost' ? 'active' : ''}`}
          onClick={() => { setActiveSource('animevost'); setActiveCategory(null); setQuery('') }}
        >
          AnimeVost
        </button>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="search-bar">
        <input
          type="text"
          className="input"
          placeholder={`Search ${activeSource === 'hdrezka' ? 'movies & series' : 'anime'}...`}
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      {/* Categories/Genres Tabs */}
      <div className="tabs">
        <button 
          className={`tab ${!activeCategory ? 'active' : ''}`} 
          onClick={() => { setActiveCategory(null); setQuery('') }}
        >
          All
        </button>
        {categories.slice(0, 12).map(cat => (
          <button 
            key={cat.id} 
            className={`tab ${activeCategory === cat.id ? 'active' : ''}`}
            onClick={() => { setActiveCategory(cat.id); setQuery('') }}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Content Grid */}
      {loading ? (
        <div className="loader"><div className="spinner"></div></div>
      ) : content.length === 0 ? (
        <div className="empty-state">
          <h3>No content found</h3>
          <p>Try a different search or browse by category</p>
        </div>
      ) : (
        <div className="grid">
          {content.map(item => (
            <div key={item.id} onClick={() => handleItemClick(item)} className="cinema-card">
              <Card
                type="cinema"
                image={item.image}
                title={item.title}
                subtitle={item.type || activeSource}
              />
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedItem && (
        <div className="modal-overlay" onClick={closeDetail}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={closeDetail}>×</button>
            
            {itemDetail ? (
              <div className="detail-view">
                <div className="detail-header">
                  {itemDetail.poster && (
                    <img src={itemDetail.poster} alt={itemDetail.title} className="detail-poster" />
                  )}
                  <div className="detail-info">
                    <h2>{itemDetail.title}</h2>
                    {itemDetail.original_title && (
                      <p className="original-title">{itemDetail.original_title}</p>
                    )}
                    {itemDetail.year && <p className="year">Year: {itemDetail.year}</p>}
                    {itemDetail.genres && itemDetail.genres.length > 0 && (
                      <p className="genres">Genres: {itemDetail.genres.join(', ')}</p>
                    )}
                    {itemDetail.imdb_rating && (
                      <p className="rating">IMDb: {itemDetail.imdb_rating}</p>
                    )}
                    {itemDetail.kp_rating && (
                      <p className="rating">Kinopoisk: {itemDetail.kp_rating}</p>
                    )}
                    {itemDetail.status && (
                      <p className="status">Status: {itemDetail.status}</p>
                    )}
                    {itemDetail.episodes && (
                      <p className="episodes">Episodes: {itemDetail.episodes}</p>
                    )}
                  </div>
                </div>
                
                {itemDetail.description && (
                  <div className="detail-description">
                    <h3>Description</h3>
                    <p>{itemDetail.description}</p>
                  </div>
                )}

                {itemDetail.player_url && (
                  <div className="detail-player">
                    <a 
                      href={itemDetail.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-primary"
                    >
                      Watch on {activeSource === 'hdrezka' ? 'HDRezka' : 'AnimeVost'}
                    </a>
                  </div>
                )}
              </div>
            ) : (
              <div className="loader"><div className="spinner"></div></div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
