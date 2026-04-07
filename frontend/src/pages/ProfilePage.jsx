import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Rating from '../components/common/Rating'
import api from '../api/client'
import './ProfilePage.css'

export default function ProfilePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('favorites')
  const [favorites, setFavorites] = useState([])
  const [ratings, setRatings] = useState([])
  const [taste, setTaste] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    loadData()
  }, [user, activeTab])

  const loadData = () => {
    setLoading(true)
    if (activeTab === 'favorites') {
      api.get('/api/profile/favorites').then(r => setFavorites(r.data)).finally(() => setLoading(false))
    } else if (activeTab === 'ratings') {
      api.get('/api/profile/ratings').then(r => setRatings(r.data)).finally(() => setLoading(false))
    } else if (activeTab === 'taste') {
      api.get('/api/recommendations/taste').then(r => setTaste(r.data)).finally(() => setLoading(false))
    }
  }

  const removeFavorite = async (item) => {
    await api.delete('/api/profile/favorites', { data: { item_type: item.item_type, item_id: item.item_id } })
    setFavorites(prev => prev.filter(f => !(f.item_type === item.item_type && f.item_id === item.item_id)))
  }

  if (!user) return null

  const groupedFavorites = favorites.reduce((acc, f) => {
    if (!acc[f.item_type]) acc[f.item_type] = []
    acc[f.item_type].push(f)
    return acc
  }, {})

  return (
    <div className="container profile-page">
      <div className="profile-header">
        <div className="profile-avatar">{user.username[0].toUpperCase()}</div>
        <div>
          <h1>{user.username}</h1>
          <p className="profile-email">{user.email}</p>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'favorites' ? 'active' : ''}`} onClick={() => setActiveTab('favorites')}>
          Favorites
        </button>
        <button className={`tab ${activeTab === 'ratings' ? 'active' : ''}`} onClick={() => setActiveTab('ratings')}>
          Ratings
        </button>
        <button className={`tab ${activeTab === 'taste' ? 'active' : ''}`} onClick={() => setActiveTab('taste')}>
          Taste Profile
        </button>
      </div>

      {loading ? (
        <div className="loader"><div className="spinner"></div></div>
      ) : (
        <>
          {activeTab === 'favorites' && (
            <div className="favorites-section">
              {favorites.length === 0 ? (
                <div className="empty-state">
                  <h3>No favorites yet</h3>
                  <p>Start adding movies, books and music to your favorites!</p>
                </div>
              ) : (
                Object.entries(groupedFavorites).map(([type, items]) => (
                  <div key={type} className="favorites-group">
                    <h2 className="section-title">{type === 'movie' ? 'Movies' : type === 'book' ? 'Books' : type === 'music' ? 'Music' : 'Events'}</h2>
                    <div className="favorites-list">
                      {items.map(f => (
                        <div key={`${f.item_type}-${f.item_id}`} className="favorite-item">
                          {f.image_url ? (
                            <img src={f.image_url} alt={f.title} className="favorite-img" />
                          ) : (
                            <div className="favorite-img-placeholder">{f.title?.[0]}</div>
                          )}
                          <div className="favorite-info">
                            <span className="favorite-title">{f.title}</span>
                            <span className="badge badge-accent">{f.item_type}</span>
                          </div>
                          <button className="btn btn-sm btn-secondary" onClick={() => removeFavorite(f)}>Remove</button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'ratings' && (
            <div className="ratings-section">
              {ratings.length === 0 ? (
                <div className="empty-state">
                  <h3>No ratings yet</h3>
                  <p>Rate movies and books to get personalized recommendations!</p>
                </div>
              ) : (
                <div className="ratings-list">
                  {ratings.map(r => (
                    <div key={`${r.item_type}-${r.item_id}`} className="rating-item">
                      {r.image_url ? (
                        <img src={r.image_url} alt={r.title} className="rating-img" />
                      ) : (
                        <div className="rating-img-placeholder">{(r.title || '?')[0]}</div>
                      )}
                      <div className="rating-info">
                        <span className="rating-item-title">{r.title || `${r.item_type} #${r.item_id}`}</span>
                        <span className="badge badge-accent">{r.item_type}</span>
                      </div>
                      <Rating value={r.rating} readonly size="sm" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'taste' && (
            <div className="taste-section">
              {!taste || taste.stats.total_ratings === 0 ? (
                <div className="empty-state">
                  <h3>Not enough data</h3>
                  <p>Rate and favorite more content to build your taste profile!</p>
                </div>
              ) : (
                <>
                  <div className="taste-stats">
                    <div className="stat-card">
                      <span className="stat-number">{taste.stats.total_favorites}</span>
                      <span className="stat-label">Favorites</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-number">{taste.stats.total_ratings}</span>
                      <span className="stat-label">Ratings</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-number">{taste.stats.avg_rating?.toFixed(1)}</span>
                      <span className="stat-label">Avg Rating</span>
                    </div>
                  </div>

                  <h2 className="section-title">Your Top Genres</h2>
                  <div className="genre-bars">
                    {Object.entries(taste.top_genres || {}).map(([category, genres]) => (
                      <div key={category} className="genre-category">
                        <h3>{category === 'movie' ? 'Movies' : category === 'book' ? 'Books' : 'Music'}</h3>
                        {genres.slice(0, 5).map(g => {
                          const maxWeight = Math.max(...genres.map(x => x.weight), 1)
                          const pct = Math.max(10, (g.weight / maxWeight) * 100)
                          return (
                            <div key={g.genre} className="genre-bar-row">
                              <span className="genre-bar-label">{g.genre}</span>
                              <div className="genre-bar-track">
                                <div className="genre-bar-fill" style={{ width: `${pct}%` }}></div>
                              </div>
                              <span className="genre-bar-val">{g.weight.toFixed(1)}</span>
                            </div>
                          )
                        })}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
