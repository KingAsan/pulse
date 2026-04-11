import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import './CinemaPage.css'

// Helper to decode unicode escapes like \u0414 -> Д
const decodeUnicodeEscapes = (str) => {
  if (!str) return ''
  try {
    return str.replace(/\\u([0-9a-fA-F]{4})/g, (match, grp) => 
      String.fromCharCode(parseInt(grp, 16))
    )
  } catch {
    return str
  }
}

export default function CinemaPage() {
  const { user } = useAuth()
  const [activeCategory, setActiveCategory] = useState('films')
  const [content, setContent] = useState([])
  const [categories, setCategories] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedItem, setSelectedItem] = useState(null)
  const [detail, setDetail] = useState(null)
  const [seasons, setSeasons] = useState([])
  const [selectedSeason, setSelectedSeason] = useState(0)
  const [selectedEpisode, setSelectedEpisode] = useState(0)
  const [voiceTracks, setVoiceTracks] = useState([])
  const [activeTrack, setActiveTrack] = useState(null)
  const [playerLoading, setPlayerLoading] = useState(false)

  const isAdmin = user?.is_admin

  // Load categories
  useEffect(() => {
    if (!isAdmin) return
    api.get('/api/hdrezka/categories')
      .then(r => setCategories(r.data))
      .catch(() => {})
  }, [isAdmin])

  // Load content
  useEffect(() => {
    if (!isAdmin) return
    setLoading(true)
    api.get(`/api/hdrezka/browse?category=${activeCategory}`)
      .then(r => setContent(Array.isArray(r.data) ? r.data : []))
      .catch(() => setContent([]))
      .finally(() => setLoading(false))
  }, [activeCategory, isAdmin])

  // Search
  const handleSearch = useCallback((e) => {
    e.preventDefault()
    if (!query.trim() || !isAdmin) return
    setLoading(true)
    api.get(`/api/hdrezka/search?q=${encodeURIComponent(query)}`)
      .then(r => setContent(Array.isArray(r.data) ? r.data : []))
      .catch(() => setContent([]))
      .finally(() => setLoading(false))
  }, [query, isAdmin])

  // Load streams
  const loadStreams = useCallback(async (url, translatorId = '', season = '', episode = '') => {
    try {
      // For HDRezka, we need to use embed URL from detail
      // The iframe handles episode switching internally
      const params = { embed_url: url }
      if (translatorId) params.translator_id = translatorId

      const res = await api.get('/api/hdrezka/streams', { params })
      const tracks = res.data.tracks || []
      setVoiceTracks(tracks)
      if (tracks.length > 0) {
        setActiveTrack(tracks[0])
      }
      return tracks
    } catch (err) {
      console.error('Error loading streams:', err)
      return []
    }
  }, [])

  // Get detail
  const handleClick = useCallback(async (item) => {
    if (!isAdmin) return
    setSelectedItem(item)
    setDetail(null)
    setSeasons([])
    setSelectedSeason(0)
    setSelectedEpisode(0)
    setVoiceTracks([])
    setActiveTrack(null)
    setPlayerLoading(true)

    try {
      const detailRes = await api.get(`/api/hdrezka/detail?url=${encodeURIComponent(item.url)}`)
      setDetail(detailRes.data)

      // If it's a series/cartoon/anime, fetch seasons
      if (['series', 'cartoon', 'anime'].includes(detailRes.data.content_type)) {
        const seasonsRes = await api.get(`/api/hdrezka/seasons?url=${encodeURIComponent(item.url)}`)
        setSeasons(seasonsRes.data.seasons || [])
      }

      // Load streams for first episode
      if (detailRes.data.url) {
        // For series, use AJAX API with url parameter
        await loadStreams(detailRes.data.url, '', '1', '1')
      } else if (detailRes.data.player_url) {
        // For movies, use embed method
        await loadStreams(detailRes.data.player_url)
      }
    } catch (err) {
      console.error('Error loading detail:', err)
    } finally {
      setPlayerLoading(false)
    }
  }, [isAdmin, loadStreams])

  // Handle season change - show info message (iframe handles switching internally)
  const handleSeasonChange = useCallback((seasonIndex) => {
    setSelectedSeason(seasonIndex)
    setSelectedEpisode(0)
    // Note: HDRezka iframe handles episode switching internally
    // User needs to use the player controls to switch episodes
  }, [])

  // Handle episode change - show info message (iframe handles switching internally)
  const handleEpisodeChange = useCallback((episodeIndex) => {
    setSelectedEpisode(episodeIndex)
    // Note: HDRezka iframe handles episode switching internally
    // User needs to use the player controls to switch episodes
  }, [])

  // Select voice track
  const selectTrack = useCallback((track) => {
    setActiveTrack(track)
  }, [])

  // Close detail view
  const closeDetail = useCallback(() => {
    setSelectedItem(null)
    setDetail(null)
    setSeasons([])
    setSelectedSeason(0)
    setSelectedEpisode(0)
    setVoiceTracks([])
    setActiveTrack(null)
  }, [])

  if (!isAdmin) {
    return (
      <div className="cinema-access-denied">
        <div className="access-icon">
          <i className="ri-lock-line"></i>
        </div>
        <h2>Доступ ограничен</h2>
        <p>Просмотр кино и аниме доступен только администраторам</p>
      </div>
    )
  }

  return (
    <div className="cinema-page">
      <div className="cinema-header">
        <h1><i className="ri-film-line"></i> Cinema</h1>
        <p className="cinema-subtitle">HDRezka — Фильмы, Сериалы, Мультфильмы и Аниме</p>
      </div>

      <form onSubmit={handleSearch} className="cinema-search">
        <input
          type="text"
          placeholder="Поиск фильмов, сериалов, аниме..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="cinema-search-input"
        />
        <button type="submit" className="cinema-search-btn">
          <i className="ri-search-line"></i> Поиск
        </button>
      </form>

      {categories.length > 0 && (
        <div className="cinema-category-filters">
          {categories.map(cat => (
            <button
              key={cat.id}
              className={`category-btn ${activeCategory === cat.id ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat.id)}
            >
              {cat.name}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div className="cinema-loading">
          <div className="spinner"></div>
          <p>Загрузка контента...</p>
        </div>
      )}

      {!loading && content.length === 0 && (
        <div className="cinema-empty">
          <i className="ri-movie-2-line"></i>
          <h3>Нет результатов</h3>
          <p>Попробуйте изменить запрос или категорию</p>
        </div>
      )}

      {!loading && content.length > 0 && (
        <div className="cinema-grid">
          {content.map(item => (
            <div
              key={item.id}
              className="cinema-card"
              onClick={() => handleClick(item)}
            >
              <div className="cinema-card-poster">
                <img
                  src={item.image || '/placeholder.jpg'}
                  alt={item.title}
                  loading="lazy"
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 300"><rect fill="%231a1a2e" width="200" height="300"/><text fill="%234a4a6a" font-family="sans-serif" font-size="40" x="50%" y="50%" text-anchor="middle" dy=".3em">?</text></svg>'
                  }}
                />
              </div>
              <div className="cinema-card-info">
                <h3 className="cinema-card-title">{item.title}</h3>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedItem && detail && (
        <div className="cinema-detail-modal" onClick={closeDetail}>
          <div className="cinema-detail-content" onClick={(e) => e.stopPropagation()}>
            <button className="cinema-detail-close" onClick={closeDetail}>
              <i className="ri-close-line"></i>
            </button>

            <div className="cinema-detail-header">
              <div className="cinema-detail-poster">
                <img src={detail.poster || selectedItem.image} alt={detail.title} />
              </div>
              <div className="cinema-detail-info">
                <h2>{detail.title}</h2>
                {detail.original_title && (
                  <p className="cinema-detail-original">{detail.original_title}</p>
                )}
                <div className="cinema-detail-meta">
                  {detail.year && (
                    <span className="meta-item">
                      <i className="ri-calendar-line"></i> {detail.year}
                    </span>
                  )}
                  {detail.country && (
                    <span className="meta-item">
                      <i className="ri-map-pin-line"></i> {detail.country}
                    </span>
                  )}
                  {detail.duration && (
                    <span className="meta-item">
                      <i className="ri-time-line"></i> {detail.duration}
                    </span>
                  )}
                  {detail.quality && (
                    <span className="meta-item">
                      <i className="ri-film-line"></i> {detail.quality}
                    </span>
                  )}
                  {detail.imdb_rating && (
                    <span className="meta-item rating">
                      <i className="ri-star-fill"></i> IMDb {detail.imdb_rating}
                    </span>
                  )}
                  {detail.kp_rating && (
                    <span className="meta-item rating">
                      <i className="ri-star-fill"></i> KP {detail.kp_rating}
                    </span>
                  )}
                </div>
                {detail.genres && detail.genres.length > 0 && (
                  <div className="cinema-detail-genres">
                    {detail.genres.map((g, i) => (
                      <span key={i} className="genre-tag">{g}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {detail.description && (
              <div className="cinema-description-section">
                <h3><i className="ri-file-text-line"></i> Описание</h3>
                <p className="cinema-description">{detail.description}</p>
              </div>
            )}

            {/* Season & Episode Info */}
            {seasons.length > 0 && (
              <div className="cinema-seasons-section">
                <h3><i className="ri-list-check"></i> Сезоны и серии</h3>
                <div className="seasons-tabs">
                  {seasons.map((season, idx) => (
                    <button
                      key={idx}
                      className={`season-btn ${selectedSeason === idx ? 'active' : ''}`}
                      onClick={() => handleSeasonChange(idx)}
                    >
                      {season.name}
                    </button>
                  ))}
                </div>
                <p className="seasons-hint">
                  <i className="ri-information-line"></i>
                  Используйте плеер HDRezka для переключения серий
                </p>
              </div>
            )}

            {/* Voice Track Selection */}
            {voiceTracks.length > 0 && (
              <div className="cinema-voice-section">
                <h3><i className="ri-mic-line"></i> Озвучка</h3>
                <div className="voice-tracks-list">
                  {voiceTracks.map((track, idx) => {
                    // Decode unicode escapes on frontend
                    const decodedTitle = decodeUnicodeEscapes(track.title)
                    
                    return (
                      <button
                        key={idx}
                        className={`voice-btn ${activeTrack?.voice_id === track.voice_id ? 'active' : ''}`}
                        onClick={() => selectTrack(track)}
                      >
                        {decodedTitle}
                        {track.has_quality && <span className="hd-badge">HD</span>}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Player */}
            {activeTrack && (
              <div className="cinema-player-section">
                <div className="player-header">
                  <h3><i className="ri-play-circle-line"></i> Плеер</h3>
                  <span className="player-hint">
                    <i className="ri-information-line"></i>
                    Для переключения серий используйте плеер HDRezka
                  </span>
                </div>
                <div className="cinema-player-wrapper">
                  {playerLoading ? (
                    <div className="player-loading">
                      <div className="spinner"></div>
                      <p>Загрузка плеера...</p>
                    </div>
                  ) : (
                    <iframe
                      src={activeTrack.hls_url}
                      allow="autoplay; encrypted-media; fullscreen"
                      allowFullScreen
                      className="cinema-player-iframe"
                      title="Video Player"
                    />
                  )}
                </div>
              </div>
            )}

            {/* Source URL fallback */}
            {detail.source_url && (
              <div className="cinema-source-link">
                <a
                  href={detail.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-link-btn"
                >
                  <i className="ri-external-link-line"></i> Открыть на HDRezka
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
