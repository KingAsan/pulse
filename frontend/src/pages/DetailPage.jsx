import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Card from '../components/common/Card'
import Rating from '../components/common/Rating'
import api from '../api/client'
import './DetailPage.css'

export default function DetailPage({ type }) {
  const { id } = useParams()
  const { user } = useAuth()
  const [item, setItem] = useState(null)
  const [similar, setSimilar] = useState([])
  const [isFavorite, setIsFavorite] = useState(false)
  const [userRating, setUserRating] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    if (type === 'movie') {
      api.get(`/api/movies/${id}`).then(r => setItem(r.data)).finally(() => setLoading(false))
      api.get(`/api/movies/${id}/recommendations`).then(r => setSimilar(r.data)).catch(() => {})
    } else if (type === 'book') {
      const key = decodeURIComponent(id)
      api.get(`/api/books/detail${key}`).then(r => setItem(r.data)).finally(() => setLoading(false))
    }

    if (user) {
      const itemId = type === 'book' ? decodeURIComponent(id) : id
      api.get(`/api/profile/favorites/check?item_type=${type}&item_id=${encodeURIComponent(itemId)}`).then(r => setIsFavorite(r.data.is_favorite)).catch(() => {})
      api.get(`/api/profile/ratings/check?item_type=${type}&item_id=${encodeURIComponent(itemId)}`).then(r => setUserRating(r.data.rating)).catch(() => {})
    }
  }, [id, type, user])

  const toggleFavorite = async () => {
    if (!user) return
    const itemId = type === 'book' ? decodeURIComponent(id) : id
    if (isFavorite) {
      await api.delete('/api/profile/favorites', { data: { item_type: type, item_id: itemId } })
      setIsFavorite(false)
    } else {
      const genres = item?.genres?.map(g => g.name || g) || item?.subjects || []
      await api.post('/api/profile/favorites', {
        item_type: type,
        item_id: itemId,
        title: item?.title || '',
        image_url: item?.poster_url || item?.cover_url || '',
        metadata: { genres }
      })
      setIsFavorite(true)
    }
  }

  const handleRate = async (rating) => {
    if (!user) return
    const itemId = type === 'book' ? decodeURIComponent(id) : id
    await api.post('/api/profile/ratings', { item_type: type, item_id: itemId, rating })
    setUserRating(rating)
  }

  if (loading) return <div className="loader"><div className="spinner"></div></div>
  if (!item) return <div className="container empty-state"><h3>Not found</h3></div>

  const isMovie = type === 'movie'

  return (
    <div className="detail-page">
      {isMovie && item.backdrop_url && (
        <div className="detail-backdrop" style={{ backgroundImage: `url(${item.backdrop_url})` }}>
          <div className="detail-backdrop-overlay"></div>
        </div>
      )}

      <div className="container detail-content">
        <div className="detail-layout">
          <div className="detail-poster">
            {(item.poster_url || item.cover_url) ? (
              <img src={item.poster_url || item.cover_url} alt={item.title} />
            ) : (
              <div className="detail-poster-placeholder">
                <span>{item.title?.[0]}</span>
              </div>
            )}
          </div>

          <div className="detail-info">
            <h1 className="detail-title">{item.title}</h1>

            <div className="detail-meta">
              {isMovie && item.vote_average > 0 && (
                <span className="rating-badge">&#9733; {item.vote_average.toFixed(1)}</span>
              )}
              {isMovie && item.release_date && (
                <span className="badge badge-accent">{item.release_date.slice(0, 4)}</span>
              )}
              {!isMovie && item.first_publish_date && (
                <span className="badge badge-accent">{item.first_publish_date}</span>
              )}
              {!isMovie && item.authors?.length > 0 && (
                <span className="detail-authors">{item.authors.join(', ')}</span>
              )}
            </div>

            <div className="detail-genres">
              {(item.genres || item.subjects || []).map((g, i) => (
                <span key={i} className="badge badge-accent">{g.name || g}</span>
              ))}
            </div>

            {(item.overview || item.description) && (
              <p className="detail-overview">{item.overview || item.description}</p>
            )}

            {user && (
              <div className="detail-actions">
                <button className={`btn ${isFavorite ? 'btn-primary' : 'btn-secondary'}`} onClick={toggleFavorite}>
                  {isFavorite ? '&#9829; In Favorites' : '&#9825; Add to Favorites'}
                </button>
                <div className="detail-rating">
                  <span>Your rating:</span>
                  <Rating value={userRating} onChange={handleRate} size="lg" />
                </div>
              </div>
            )}
          </div>
        </div>

        {similar.length > 0 && (
          <section className="detail-similar">
            <h2 className="section-title">Similar Movies</h2>
            <div className="carousel">
              {similar.map(m => (
                <Card key={m.id} type="movie" image={m.poster_url} title={m.title}
                  subtitle={m.release_date?.slice(0, 4)} rating={m.vote_average} link={`/movies/${m.id}`} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
