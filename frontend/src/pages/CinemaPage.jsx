import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import './CinemaPage.css'

export default function CinemaPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('movies') // 'movies' or 'anime'
  const [animeContent, setAnimeContent] = useState([])
  const [animeCategories, setAnimeCategories] = useState([])
  const [activeAnimeCategory, setActiveAnimeCategory] = useState(null)
  const [animeQuery, setAnimeQuery] = useState('')
  const [animeLoading, setAnimeLoading] = useState(true)
  const [selectedAnime, setSelectedAnime] = useState(null)
  const [animeDetail, setAnimeDetail] = useState(null)
  const [selectedEpisode, setSelectedEpisode] = useState(null)
  const [playerQuality, setPlayerQuality] = useState('720')

  const isAdmin = user?.is_admin

  // Load anime categories
  useEffect(() => {
    if (!isAdmin || activeTab !== 'anime') return
    api.get('/api/anilibria/genres')
      .then(r => setAnimeCategories(r.data))
      .catch(() => {})
  }, [activeTab, isAdmin])

  // Load anime content
  useEffect(() => {
    if (!isAdmin || activeTab !== 'anime') return

    setAnimeLoading(true)
    const endpoint = activeAnimeCategory
      ? `/api/anilibria/genre/${activeAnimeCategory}`
      : '/api/anilibria/browse'

    api.get(endpoint)
      .then(r => {
        const data = Array.isArray(r.data) ? r.data : []
        setAnimeContent(data)
      })
      .catch(() => setAnimeContent([]))
      .finally(() => setAnimeLoading(false))
  }, [activeAnimeCategory, activeTab, isAdmin])

  // Search anime
  const handleAnimeSearch = useCallback((e) => {
    e.preventDefault()
    if (!animeQuery.trim() || !isAdmin) return

    setAnimeLoading(true)
    setActiveAnimeCategory(null)

    api.get(`/api/anilibria/search?q=${encodeURIComponent(animeQuery)}`)
      .then(r => setAnimeContent(Array.isArray(r.data) ? r.data : []))
      .catch(() => setAnimeContent([]))
      .finally(() => setAnimeLoading(false))
  }, [animeQuery, isAdmin])

  // Get anime detail
  const handleAnimeClick = useCallback((anime) => {
    if (!isAdmin) return
    setSelectedAnime(anime)
    setAnimeDetail(null)
    setSelectedEpisode(null)

    api.get(`/api/anilibria/detail?code=${anime.code}`)
      .then(r => setAnimeDetail(r.data))
      .catch(() => setAnimeDetail(null))
  }, [])

  // Close detail view
  const closeDetail = useCallback(() => {
    setSelectedAnime(null)
    setAnimeDetail(null)
    setSelectedEpisode(null)
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
      {/* Header */}
      <div className="cinema-header">
        <h1><i className="ri-film-line"></i> Cinema</h1>
        <p className="cinema-subtitle">HDRezka + AniLibria — Администрирование контента</p>
      </div>

      {/* Tabs */}
      <div className="cinema-tabs">
        <button
          className={`cinema-tab ${activeTab === 'movies' ? 'active' : ''}`}
          onClick={() => setActiveTab('movies')}
        >
          <i className="ri-movie-2-line"></i> Кино (HDRezka)
        </button>
        <button
          className={`cinema-tab ${activeTab === 'anime' ? 'active' : ''}`}
          onClick={() => setActiveTab('anime')}
        >
          <i className="ri-robot-2-line"></i> Аниме (AniLibria)
        </button>
      </div>

      {/* Anime Content */}
      {activeTab === 'anime' && (
        <div className="anime-content">
          {/* Search */}
          <form onSubmit={handleAnimeSearch} className="anime-search">
            <input
              type="text"
              placeholder="Поиск аниме на AniLibria..."
              value={animeQuery}
              onChange={(e) => setAnimeQuery(e.target.value)}
              className="anime-search-input"
            />
            <button type="submit" className="anime-search-btn">
              <i className="ri-search-line"></i> Поиск
            </button>
          </form>

          {/* Genre Filters */}
          {animeCategories.length > 0 && (
            <div className="anime-genre-filters">
              <button
                className={`genre-btn ${!activeAnimeCategory ? 'active' : ''}`}
                onClick={() => setActiveAnimeCategory(null)}
              >
                Все
              </button>
              {animeCategories.map(genre => (
                <button
                  key={genre.id}
                  className={`genre-btn ${activeAnimeCategory === genre.id ? 'active' : ''}`}
                  onClick={() => setActiveAnimeCategory(genre.id)}
                >
                  {genre.name}
                </button>
              ))}
            </div>
          )}

          {/* Loading State */}
          {animeLoading && (
            <div className="anime-loading">
              <div className="spinner"></div>
              <p>Загрузка аниме...</p>
            </div>
          )}

          {/* Empty State */}
          {!animeLoading && animeContent.length === 0 && (
            <div className="anime-empty">
              <i className="ri-robot-2-line"></i>
              <h3>Нет результатов</h3>
              <p>Попробуйте изменить запрос или фильтры</p>
            </div>
          )}

          {/* Anime Grid */}
          {!animeLoading && animeContent.length > 0 && (
            <div className="anime-grid">
              {animeContent.map(anime => (
                <div
                  key={anime.id}
                  className="anime-card"
                  onClick={() => handleAnimeClick(anime)}
                >
                  <div className="anime-card-poster">
                    <img
                      src={anime.poster}
                      alt={anime.title}
                      loading="lazy"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 300"><rect fill="%231a1a2e" width="200" height="300"/><text fill="%234a4a6a" font-family="sans-serif" font-size="40" x="50%" y="50%" text-anchor="middle" dy=".3em">?</text></svg>'
                      }}
                    />
                    {anime.status === 'ongoing' && (
                      <span className="anime-badge ongoing">Онгоинг</span>
                    )}
                    {anime.rating > 0 && (
                      <span className="anime-rating">
                        <i className="ri-star-fill"></i> {anime.rating.toFixed(1)}
                      </span>
                    )}
                  </div>
                  <div className="anime-card-info">
                    <h3 className="anime-card-title">{anime.title}</h3>
                    <p className="anime-card-meta">
                      {anime.year} • {anime.type}
                    </p>
                    <div className="anime-card-genres">
                      {anime.genres?.slice(0, 3).map((g, i) => (
                        <span key={i} className="anime-genre-tag">{g}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Anime Detail Modal */}
      {selectedAnime && animeDetail && (
        <div className="anime-detail-modal" onClick={closeDetail}>
          <div className="anime-detail-content" onClick={(e) => e.stopPropagation()}>
            <button className="anime-detail-close" onClick={closeDetail}>
              <i className="ri-close-line"></i>
            </button>

            <div className="anime-detail-header">
              <div className="anime-detail-poster">
                <img src={animeDetail.poster} alt={animeDetail.title} />
              </div>
              <div className="anime-detail-info">
                <h2>{animeDetail.title}</h2>
                {animeDetail.title_en && (
                  <p className="anime-detail-title-en">{animeDetail.title_en}</p>
                )}
                <div className="anime-detail-meta">
                  <span className="meta-item">
                    <i className="ri-calendar-line"></i> {animeDetail.year}
                  </span>
                  <span className="meta-item">
                    <i className="ri-film-line"></i> {animeDetail.type}
                  </span>
                  <span className="meta-item">
                    <i className="ri-star-line"></i> {animeDetail.rating?.toFixed(1) || 'N/A'}
                  </span>
                  <span className="meta-item">
                    <i className="ri-list-check"></i> {animeDetail.episodes_count} эп.
                  </span>
                  <span className={`meta-item status-${animeDetail.status}`}>
                    {animeDetail.status === 'ongoing' ? 'Онгоинг' :
                     animeDetail.status === 'completed' ? 'Завершён' : 'Анонс'}
                  </span>
                </div>
                <div className="anime-detail-genres">
                  {animeDetail.genres?.map((g, i) => (
                    <span key={i} className="genre-tag">{g}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Episode List */}
            {animeDetail.episodes && animeDetail.episodes.length > 0 && (
              <div className="anime-episodes-section">
                <h3><i className="ri-play-list-line"></i> Эпизоды</h3>
                <div className="anime-episode-list">
                  {animeDetail.episodes.map(ep => (
                    <button
                      key={ep.episode}
                      className={`episode-btn ${selectedEpisode === ep.episode ? 'active' : ''}`}
                      onClick={() => {
                        setSelectedEpisode(ep.episode)
                        // Auto-select best quality
                        if (animeDetail.player?.mp4) {
                          const qualities = Object.keys(animeDetail.player.mp4)
                          setPlayerQuality(qualities.includes('720') ? '720' : qualities[0])
                        }
                      }}
                    >
                      {ep.name || `Эпизод ${ep.episode}`}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Player */}
            {selectedEpisode && animeDetail.player && (
              <div className="anime-player-section">
                <div className="player-header">
                  <h3><i className="ri-play-circle-line"></i> Плеер</h3>
                  <div className="quality-selector">
                    {animeDetail.player.mp4 && Object.keys(animeDetail.player.mp4).map(q => (
                      <button
                        key={q}
                        className={`quality-btn ${playerQuality === q ? 'active' : ''}`}
                        onClick={() => setPlayerQuality(q)}
                      >
                        {q}
                      </button>
                    ))}
                    {animeDetail.player.hls && (
                      <button
                        className={`quality-btn ${playerQuality === 'hls' ? 'active' : ''}`}
                        onClick={() => setPlayerQuality('hls')}
                      >
                        HLS
                      </button>
                    )}
                  </div>
                </div>
                <div className="anime-player-wrapper">
                  {playerQuality === 'hls' && animeDetail.player.hls ? (
                    <video
                      controls
                      autoPlay
                      className="anime-player-video"
                      src={animeDetail.player.hls}
                    >
                      Ваш браузер не поддерживает видео
                    </video>
                  ) : animeDetail.player.mp4?.[playerQuality] ? (
                    <video
                      controls
                      autoPlay
                      className="anime-player-video"
                      src={animeDetail.player.mp4[playerQuality]}
                    >
                      Ваш браузер не поддерживает видео
                    </video>
                  ) : (
                    <div className="player-error">
                      <i className="ri-error-warning-line"></i>
                      <p>Видео недоступно в выбранном качестве</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Description */}
            {animeDetail.description && (
              <div className="anime-description-section">
                <h3><i className="ri-file-text-line"></i> Описание</h3>
                <p className="anime-description">{animeDetail.description}</p>
              </div>
            )}

            {/* Torrent Info */}
            {animeDetail.torrent && (
              <div className="anime-torrent-section">
                <h3><i className="ri-download-line"></i> Торрент</h3>
                <div className="torrent-info">
                  <span>Качество: {animeDetail.torrent.quality}</span>
                  <span>Размер: {animeDetail.torrent.size}</span>
                  {animeDetail.torrent.url && (
                    <a
                      href={animeDetail.torrent.url}
                      className="torrent-download-btn"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <i className="ri-download-2-line"></i> Скачать
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Movies Content (HDRezka - placeholder) */}
      {activeTab === 'movies' && (
        <div className="movies-placeholder">
          <div className="placeholder-icon">
            <i className="ri-movie-2-line"></i>
          </div>
          <h2>Кино (HDRezka)</h2>
          <p>Раздел кино в разработке. Скоро здесь появится контент с HDRezka.</p>
        </div>
      )}
    </div>
  )
}
