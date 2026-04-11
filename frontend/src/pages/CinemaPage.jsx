import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import './CinemaPage.css'

export default function CinemaPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('movies')
  
  // HDRezka state
  const [hdRezkaContent, setHdRezkaContent] = useState([])
  const [hdRezkaCategories, setHdRezkaCategories] = useState([])
  const [activeCategory, setActiveCategory] = useState('films')
  const [hdRezkaQuery, setHdRezkaQuery] = useState('')
  const [hdRezkaLoading, setHdRezkaLoading] = useState(true)
  const [selectedItem, setSelectedItem] = useState(null)
  const [detail, setDetail] = useState(null)
  const [seasons, setSeasons] = useState([])
  const [selectedSeason, setSelectedSeason] = useState(0)
  const [selectedEpisode, setSelectedEpisode] = useState(0)
  const [voiceTracks, setVoiceTracks] = useState([])
  const [activeTrack, setActiveTrack] = useState(null)
  const [playerLoading, setPlayerLoading] = useState(false)
  
  // AniLibria state
  const [animeContent, setAnimeContent] = useState([])
  const [animeCategories, setAnimeCategories] = useState([])
  const [activeAnimeCategory, setActiveAnimeCategory] = useState(null)
  const [animeQuery, setAnimeQuery] = useState('')
  const [animeLoading, setAnimeLoading] = useState(true)
  const [selectedAnime, setSelectedAnime] = useState(null)
  const [animeDetail, setAnimeDetail] = useState(null)
  const [selectedAnimeEpisode, setSelectedAnimeEpisode] = useState(null)
  const [playerQuality, setPlayerQuality] = useState('720')

  const isAdmin = user?.is_admin

  // Load HDRezka categories
  useEffect(() => {
    if (!isAdmin || activeTab !== 'movies') return
    api.get('/api/hdrezka/categories')
      .then(r => setHdRezkaCategories(r.data))
      .catch(() => {})
  }, [activeTab, isAdmin])

  // Load HDRezka content
  useEffect(() => {
    if (!isAdmin || activeTab !== 'movies') return

    setHdRezkaLoading(true)
    api.get(`/api/hdrezka/browse?category=${activeCategory}`)
      .then(r => {
        const data = Array.isArray(r.data) ? r.data : []
        setHdRezkaContent(data)
      })
      .catch(() => setHdRezkaContent([]))
      .finally(() => setHdRezkaLoading(false))
  }, [activeCategory, activeTab, isAdmin])

  // Search HDRezka
  const handleHdRezkaSearch = useCallback((e) => {
    e.preventDefault()
    if (!hdRezkaQuery.trim() || !isAdmin) return

    setHdRezkaLoading(true)

    api.get(`/api/hdrezka/search?q=${encodeURIComponent(hdRezkaQuery)}`)
      .then(r => setHdRezkaContent(Array.isArray(r.data) ? r.data : []))
      .catch(() => setHdRezkaContent([]))
      .finally(() => setHdRezkaLoading(false))
  }, [hdRezkaQuery, isAdmin])

  // Get HDRezka detail
  const handleHdRezkaClick = useCallback(async (item) => {
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
      // Fetch detail
      const detailRes = await api.get(`/api/hdrezka/detail?url=${encodeURIComponent(item.url)}`)
      setDetail(detailRes.data)

      // If it's a series/cartoon/anime, fetch seasons
      if (['series', 'cartoon', 'anime'].includes(detailRes.data.content_type)) {
        const seasonsRes = await api.get(`/api/hdrezka/seasons?url=${encodeURIComponent(item.url)}`)
        setSeasons(seasonsRes.data.seasons || [])
      }

      // If there's a player URL, fetch streams
      if (detailRes.data.player_url) {
        const streamsRes = await api.get(`/api/hdrezka/streams?embed_url=${encodeURIComponent(detailRes.data.player_url)}`)
        const tracks = streamsRes.data.tracks || []
        setVoiceTracks(tracks)
        if (tracks.length > 0) {
          setActiveTrack(tracks[0])
        }
      }
    } catch (err) {
      console.error('Error loading detail:', err)
    } finally {
      setPlayerLoading(false)
    }
  }, [isAdmin])

  // Handle season change
  const handleSeasonChange = useCallback((seasonIndex) => {
    setSelectedSeason(seasonIndex)
    setSelectedEpisode(0)
    // Reload streams for new season/episode
    if (detail?.player_url && voiceTracks.length > 0) {
      loadStreams(detail.player_url)
    }
  }, [detail, voiceTracks])

  // Handle episode change
  const handleEpisodeChange = useCallback((episodeIndex) => {
    setSelectedEpisode(episodeIndex)
    // Reload streams for new episode
    if (detail?.player_url && voiceTracks.length > 0) {
      loadStreams(detail.player_url)
    }
  }, [detail, voiceTracks])

  // Load streams
  const loadStreams = useCallback(async (embedUrl) => {
    try {
      const res = await api.get(`/api/hdrezka/streams?embed_url=${encodeURIComponent(embedUrl)}`)
      const tracks = res.data.tracks || []
      setVoiceTracks(tracks)
      if (tracks.length > 0) {
        setActiveTrack(tracks[0])
      }
    } catch (err) {
      console.error('Error loading streams:', err)
    }
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

  // AniLibria functions (same as before)
  useEffect(() => {
    if (!isAdmin || activeTab !== 'anime') return
    api.get('/api/anilibria/genres')
      .then(r => setAnimeCategories(r.data))
      .catch(() => {})
  }, [activeTab, isAdmin])

  useEffect(() => {
    if (!isAdmin || activeTab !== 'anime') return
    setAnimeLoading(true)
    const endpoint = activeAnimeCategory
      ? `/api/anilibria/genre/${activeAnimeCategory}`
      : '/api/anilibria/browse'

    api.get(endpoint)
      .then(r => setAnimeContent(Array.isArray(r.data) ? r.data : []))
      .catch(() => setAnimeContent([]))
      .finally(() => setAnimeLoading(false))
  }, [activeAnimeCategory, activeTab, isAdmin])

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

  const handleAnimeClick = useCallback((anime) => {
    if (!isAdmin) return
    setSelectedAnime(anime)
    setAnimeDetail(null)
    setSelectedAnimeEpisode(null)

    api.get(`/api/anilibria/detail?code=${anime.code}`)
      .then(r => setAnimeDetail(r.data))
      .catch(() => setAnimeDetail(null))
  }, [])

  const closeAnimeDetail = useCallback(() => {
    setSelectedAnime(null)
    setAnimeDetail(null)
    setSelectedAnimeEpisode(null)
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
        <p className="cinema-subtitle">HDRezka + AniLibria — Администрирование контента</p>
      </div>

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

      {/* HDRezka Content */}
      {activeTab === 'movies' && (
        <div className="hdrezka-content">
          <form onSubmit={handleHdRezkaSearch} className="hdrezka-search">
            <input
              type="text"
              placeholder="Поиск фильмов и сериалов..."
              value={hdRezkaQuery}
              onChange={(e) => setHdRezkaQuery(e.target.value)}
              className="hdrezka-search-input"
            />
            <button type="submit" className="hdrezka-search-btn">
              <i className="ri-search-line"></i> Поиск
            </button>
          </form>

          {hdRezkaCategories.length > 0 && (
            <div className="hdrezka-category-filters">
              {hdRezkaCategories.map(cat => (
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

          {hdRezkaLoading && (
            <div className="hdrezka-loading">
              <div className="spinner"></div>
              <p>Загрузка контента...</p>
            </div>
          )}

          {!hdRezkaLoading && hdRezkaContent.length === 0 && (
            <div className="hdrezka-empty">
              <i className="ri-movie-2-line"></i>
              <h3>Нет результатов</h3>
              <p>Попробуйте изменить запрос или категорию</p>
            </div>
          )}

          {!hdRezkaLoading && hdRezkaContent.length > 0 && (
            <div className="hdrezka-grid">
              {hdRezkaContent.map(item => (
                <div
                  key={item.id}
                  className="hdrezka-card"
                  onClick={() => handleHdRezkaClick(item)}
                >
                  <div className="hdrezka-card-poster">
                    <img
                      src={item.image || '/placeholder.jpg'}
                      alt={item.title}
                      loading="lazy"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 300"><rect fill="%231a1a2e" width="200" height="300"/><text fill="%234a4a6a" font-family="sans-serif" font-size="40" x="50%" y="50%" text-anchor="middle" dy=".3em">?</text></svg>'
                      }}
                    />
                  </div>
                  <div className="hdrezka-card-info">
                    <h3 className="hdrezka-card-title">{item.title}</h3>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* HDRezka Detail Modal */}
      {selectedItem && detail && (
        <div className="hdrezka-detail-modal" onClick={closeDetail}>
          <div className="hdrezka-detail-content" onClick={(e) => e.stopPropagation()}>
            <button className="hdrezka-detail-close" onClick={closeDetail}>
              <i className="ri-close-line"></i>
            </button>

            <div className="hdrezka-detail-header">
              <div className="hdrezka-detail-poster">
                <img src={detail.poster || selectedItem.image} alt={detail.title} />
              </div>
              <div className="hdrezka-detail-info">
                <h2>{detail.title}</h2>
                {detail.original_title && (
                  <p className="hdrezka-detail-original">{detail.original_title}</p>
                )}
                <div className="hdrezka-detail-meta">
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
                  <div className="hdrezka-detail-genres">
                    {detail.genres.map((g, i) => (
                      <span key={i} className="genre-tag">{g}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {detail.description && (
              <div className="hdrezka-description-section">
                <h3><i className="ri-file-text-line"></i> Описание</h3>
                <p className="hdrezka-description">{detail.description}</p>
              </div>
            )}

            {/* Season & Episode Selection for Series */}
            {seasons.length > 0 && (
              <div className="hdrezka-seasons-section">
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
                {seasons[selectedSeason] && seasons[selectedSeason].episodes && (
                  <div className="episodes-list">
                    {seasons[selectedSeason].episodes.map((ep, idx) => (
                      <button
                        key={idx}
                        className={`episode-btn ${selectedEpisode === idx ? 'active' : ''}`}
                        onClick={() => handleEpisodeChange(idx)}
                      >
                        {ep.name || `Эпизод ${ep.episode}`}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Voice Track Selection */}
            {voiceTracks.length > 1 && (
              <div className="hdrezka-voice-section">
                <h3><i className="ri-mic-line"></i> Озвучка</h3>
                <div className="voice-tracks-list">
                  {voiceTracks.map((track, idx) => (
                    <button
                      key={idx}
                      className={`voice-btn ${activeTrack?.voice_id === track.voice_id ? 'active' : ''}`}
                      onClick={() => selectTrack(track)}
                    >
                      {track.title}
                      {track.has_quality && <span className="hd-badge">HD</span>}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Player */}
            {activeTrack && (
              <div className="hdrezka-player-section">
                <div className="player-header">
                  <h3><i className="ri-play-circle-line"></i> Плеер</h3>
                  {activeTrack && (
                    <span className="current-track">{activeTrack.title}</span>
                  )}
                </div>
                <div className="hdrezka-player-wrapper">
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
                      className="hdrezka-player-iframe"
                      title="Video Player"
                    />
                  )}
                </div>
              </div>
            )}

            {/* Source URL fallback */}
            {detail.source_url && (
              <div className="hdrezka-source-link">
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

      {/* Anime Content */}
      {activeTab === 'anime' && (
        <div className="anime-content">
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

          {animeLoading && (
            <div className="anime-loading">
              <div className="spinner"></div>
              <p>Загрузка аниме...</p>
            </div>
          )}

          {!animeLoading && animeContent.length === 0 && (
            <div className="anime-empty">
              <i className="ri-robot-2-line"></i>
              <h3>Нет результатов</h3>
              <p>Попробуйте изменить запрос или фильтры</p>
            </div>
          )}

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
        <div className="anime-detail-modal" onClick={closeAnimeDetail}>
          <div className="anime-detail-content" onClick={(e) => e.stopPropagation()}>
            <button className="anime-detail-close" onClick={closeAnimeDetail}>
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

            {animeDetail.episodes && animeDetail.episodes.length > 0 && (
              <div className="anime-episodes-section">
                <h3><i className="ri-play-list-line"></i> Эпизоды</h3>
                <div className="anime-episode-list">
                  {animeDetail.episodes.map(ep => (
                    <button
                      key={ep.episode}
                      className={`episode-btn ${selectedAnimeEpisode === ep.episode ? 'active' : ''}`}
                      onClick={() => {
                        setSelectedAnimeEpisode(ep.episode)
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

            {selectedAnimeEpisode && animeDetail.player && (
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

            {animeDetail.description && (
              <div className="anime-description-section">
                <h3><i className="ri-file-text-line"></i> Описание</h3>
                <p className="anime-description">{animeDetail.description}</p>
              </div>
            )}

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
    </div>
  )
}
