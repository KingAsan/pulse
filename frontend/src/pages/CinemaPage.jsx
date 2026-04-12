import { useState, useEffect, useCallback, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import './CinemaPage.css'

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
  const [selectedTranslator, setSelectedTranslator] = useState(null)
  const [selectedQuality, setSelectedQuality] = useState('720p')
  const [activeTrack, setActiveTrack] = useState(null)
  const [playerLoading, setPlayerLoading] = useState(false)
  const [availableQualities, setAvailableQualities] = useState([])
  
  // Enhanced player features
  const [isCinemaMode, setIsCinemaMode] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const controlsTimeoutRef = useRef(null)
  const containerRef = useRef(null)

  const isAdmin = user?.is_admin

  // Cinema mode - dim background
  useEffect(() => {
    if (isCinemaMode) {
      document.body.classList.add('cinema-mode-active')
    } else {
      document.body.classList.remove('cinema-mode-active')
    }
    return () => document.body.classList.remove('cinema-mode-active')
  }, [isCinemaMode])

  // Auto-hide controls
  useEffect(() => {
    const container = containerRef.current
    if (!container || !activeTrack) return

    const handleMouseMove = () => {
      setShowControls(true)
      clearTimeout(controlsTimeoutRef.current)
      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false)
      }, 3000)
    }

    const handleMouseLeave = () => {
      setShowControls(false)
      clearTimeout(controlsTimeoutRef.current)
    }

    // Show controls initially
    setShowControls(true)
    controlsTimeoutRef.current = setTimeout(() => {
      setShowControls(false)
    }, 3000)

    container.addEventListener('mousemove', handleMouseMove)
    container.addEventListener('mouseleave', handleMouseLeave)
    return () => {
      container.removeEventListener('mousemove', handleMouseMove)
      container.removeEventListener('mouseleave', handleMouseLeave)
      clearTimeout(controlsTimeoutRef.current)
    }
  }, [activeTrack])

  // Keyboard shortcuts
  useEffect(() => {
    if (!activeTrack) return

    const handleKeyDown = (e) => {
      const tagName = document.activeElement?.tagName
      if (tagName === 'INPUT' || tagName === 'TEXTAREA') return

      switch(e.key.toLowerCase()) {
        case 'f':
          e.preventDefault()
          if (!document.fullscreenElement) {
            containerRef.current?.requestFullscreen?.()
          } else {
            document.exitFullscreen?.()
          }
          break
        case 'c':
          e.preventDefault()
          setIsCinemaMode(prev => !prev)
          break
        case 'escape':
          if (isCinemaMode) setIsCinemaMode(false)
          break
        default:
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeTrack, isCinemaMode])

  // Save progress (for iframe we can't track time, so just track last watched episode)
  useEffect(() => {
    if (!selectedItem) return
    
    const progress = {
      url: selectedItem.url,
      season: selectedSeason,
      episode: selectedEpisode,
      timestamp: Date.now()
    }
    localStorage.setItem(`hdrezka_progress_${selectedItem.id}`, JSON.stringify(progress))
  }, [selectedItem, selectedSeason, selectedEpisode, activeTrack])

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

  // Get detail
  const handleClick = useCallback(async (item) => {
    if (!isAdmin) return
    setSelectedItem(item)
    setDetail(null)
    setSeasons([])
    setSelectedSeason(0)
    setSelectedEpisode(0)
    setSelectedTranslator(null)
    setActiveTrack(null)
    setPlayerLoading(true)
    setAvailableQualities([])

    try {
      const detailRes = await api.get(`/api/hdrezka/detail?url=${encodeURIComponent(item.url)}`)
      setDetail(detailRes.data)

      // If it's a series/cartoon/anime, fetch seasons
      if (['series', 'cartoon', 'anime'].includes(detailRes.data.content_type)) {
        const seasonsRes = await api.get(`/api/hdrezka/seasons?url=${encodeURIComponent(item.url)}`)
        setSeasons(seasonsRes.data.seasons || [])
      }

      // Get streams from HDRezkaApi
      if (detailRes.data.translator_list && detailRes.data.translator_list.length > 0) {
        // Выбрать первого переводчика по умолчанию
        const defaultTranslator = detailRes.data.translator_list[0]
        setSelectedTranslator(defaultTranslator.id)

        await loadStreams(item.url, defaultTranslator.id)
      }
    } catch (err) {
      console.error('Error loading detail:', err)
    } finally {
      setPlayerLoading(false)
    }
  }, [isAdmin])

  // Load streams
  const loadStreams = useCallback(async (url, translatorId, seasonIdx, episodeIdx) => {
    try {
      setPlayerLoading(true)
      const season = seasons[seasonIdx || selectedSeason]
      const episode = season?.episodes?.[episodeIdx || selectedEpisode]

      const params = new URLSearchParams({
        url,
        translator_id: translatorId,
      })

      // Добавить сезон и эпизод если это сериал
      if (season && episode) {
        params.append('season', season.season)
        params.append('episode', episode.episode)
      }

      const streamsRes = await api.get(`/api/hdrezka/streams?${params.toString()}`)
      
      if (streamsRes.data.tracks && streamsRes.data.tracks.length > 0) {
        const track = streamsRes.data.tracks[0]
        setActiveTrack(track)
        
        // Извлечь доступные качества
        const qualities = Object.keys(track.videos || {})
        setAvailableQualities(qualities)
        
        // Выбрать качество по умолчанию (предпочтительно 720p)
        if (qualities.includes('720p')) {
          setSelectedQuality('720p')
        } else if (qualities.length > 0) {
          setSelectedQuality(qualities[0])
        }
      }
    } catch (err) {
      console.error('Error loading streams:', err)
      // Fallback к ссылке на источник
      setActiveTrack(null)
    } finally {
      setPlayerLoading(false)
    }
  }, [seasons, selectedSeason, selectedEpisode])

  // Handle season change
  const handleSeasonChange = useCallback((seasonIndex) => {
    setSelectedSeason(seasonIndex)
    setSelectedEpisode(0)
    // Перезагрузить стримы для нового сезона/эпизода
    if (selectedTranslator && selectedItem?.url) {
      loadStreams(selectedItem.url, selectedTranslator, seasonIndex, 0)
    }
  }, [selectedTranslator, selectedItem, loadStreams])

  // Handle episode change
  const handleEpisodeChange = useCallback((episodeIndex) => {
    setSelectedEpisode(episodeIndex)
    // Перезагрузить стримы для нового эпизода
    if (selectedTranslator && selectedItem?.url) {
      loadStreams(selectedItem.url, selectedTranslator, selectedSeason, episodeIndex)
    }
  }, [selectedTranslator, selectedItem, selectedSeason, loadStreams])

  // Handle translator change
  const handleTranslatorChange = useCallback((translatorId) => {
    setSelectedTranslator(translatorId)
    // Перезагрузить стримы для нового переводчика
    if (translatorId && selectedItem?.url) {
      loadStreams(selectedItem.url, translatorId)
    }
  }, [selectedItem, loadStreams])

  // Handle quality change
  const handleQualityChange = useCallback((quality) => {
    setSelectedQuality(quality)
  }, [])

  // Close detail view
  const closeDetail = useCallback(() => {
    setSelectedItem(null)
    setDetail(null)
    setSeasons([])
    setSelectedSeason(0)
    setSelectedEpisode(0)
    setSelectedTranslator(null)
    setActiveTrack(null)
    setAvailableQualities([])
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

            {/* Season Info */}
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
                
                {/* Episode selector */}
                {seasons[selectedSeason]?.episodes && seasons[selectedSeason].episodes.length > 0 && (
                  <div className="episodes-tabs">
                    {seasons[selectedSeason].episodes.map((ep, idx) => (
                      <button
                        key={idx}
                        className={`episode-btn ${selectedEpisode === idx ? 'active' : ''}`}
                        onClick={() => handleEpisodeChange(idx)}
                      >
                        {ep.episode}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Translator selector */}
            {detail.translator_list && detail.translator_list.length > 1 && (
              <div className="cinema-translators-section">
                <h3><i className="ri-translate"></i> Озвучка</h3>
                <div className="translators-tabs">
                  {detail.translator_list.map((tr) => (
                    <button
                      key={tr.id}
                      className={`translator-btn ${selectedTranslator === tr.id ? 'active' : ''}`}
                      onClick={() => handleTranslatorChange(tr.id)}
                    >
                      {tr.title}
                      {tr.premium && <span className="premium-badge">Premium</span>}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Player */}
            {activeTrack && (
              <div className="cinema-player-section" ref={containerRef}>
                <div className={`player-header ${!showControls && 'hidden'}`}>
                  <div className="player-title">
                    <span className="player-icon">▶</span>
                    <h3>{detail.title}{selectedSeason !== null && seasons[selectedSeason] ? ` - ${seasons[selectedSeason].name}` : ''}{selectedEpisode !== null && seasons[selectedSeason]?.episodes ? `, Серия ${seasons[selectedSeason].episodes[selectedEpisode]?.episode}` : ''}</h3>
                  </div>
                  <div className="player-actions">
                    <button 
                      className="player-btn" 
                      onClick={() => setIsCinemaMode(!isCinemaMode)}
                      title="Кинематографический режим (C)"
                    >
                      <i className="ri-film-line"></i> Cinema
                    </button>
                    <button 
                      className="player-btn" 
                      onClick={() => {
                        const iframe = containerRef.current?.querySelector('iframe')
                        if (iframe?.requestPictureInPicture) {
                          iframe.requestPictureInPicture()
                        }
                      }}
                      title="Picture-in-Picture"
                    >
                      <i className="ri-picture-in-picture-line"></i>
                    </button>
                  </div>
                </div>

                <div className="cinema-player-wrapper">
                  {playerLoading ? (
                    <div className="player-loading">
                      <div className="spinner"></div>
                      <p>Загрузка плеера...</p>
                    </div>
                  ) : detail.player_url && detail.embed_sig ? (
                    <>
                      <iframe
                        src={`/api/hdrezka/embed?url=${encodeURIComponent(detail.player_url)}&sig=${detail.embed_sig}`}
                        allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
                        allowFullScreen
                        className="cinema-player-iframe"
                        title="Video Player"
                      />
                      
                      {/* Bottom Controls Overlay */}
                      <div className={`player-bottom-controls ${!showControls && 'hidden'}`}>
                        <div className="player-info">
                          <span className="info-item">F - Fullscreen</span>
                          <span className="info-item">C - Cinema Mode</span>
                        </div>
                        <button className="control-btn fullscreen-btn" onClick={() => {
                          if (!document.fullscreenElement) {
                            containerRef.current?.requestFullscreen?.()
                          } else {
                            document.exitFullscreen?.()
                          }
                        }} title="Fullscreen (F)">
                          <i className="ri-fullscreen-line"></i>
                        </button>
                      </div>
                    </>
                  ) : detail.source_url ? (
                    <div className="player-external-link">
                      <a
                        href={detail.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="external-play-btn"
                      >
                        <i className="ri-play-circle-line"></i> Смотреть на HDRezka
                      </a>
                    </div>
                  ) : (
                    <div className="player-no-video">
                      <i className="ri-error-warning-line"></i>
                      <p>Плеер недоступен</p>
                    </div>
                  )}
                </div>

                {/* Next Episode Prompt */}
                {seasons.length > 0 && selectedEpisode < seasons[selectedSeason]?.episodes?.length - 1 && (
                  <div className="next-episode-prompt">
                    <div className="prompt-content">
                      <span className="prompt-icon">⏭</span>
                      <span>Следующая серия?</span>
                      <button 
                        className="next-btn"
                        onClick={() => handleEpisodeChange(selectedEpisode + 1)}
                      >
                        Смотреть сейчас
                      </button>
                    </div>
                  </div>
                )}
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
