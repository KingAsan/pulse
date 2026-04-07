import { useState, useEffect } from 'react'
import api from '../api/client'
import './MusicPage.css'

export default function MusicPage() {
  const [tracks, setTracks] = useState([])
  const [genres, setGenres] = useState([])
  const [moods, setMoods] = useState([])
  const [activeGenre, setActiveGenre] = useState(null)
  const [activeMood, setActiveMood] = useState(null)
  const [playlist, setPlaylist] = useState(null)
  const [query, setQuery] = useState('')
  const [playing, setPlaying] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/music/browse').then(r => setTracks(r.data)),
      api.get('/api/music/genres').then(r => setGenres(r.data)),
      api.get('/api/music/moods').then(r => setMoods(r.data)),
    ]).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleFilter = (genre, mood) => {
    setActiveGenre(genre)
    setActiveMood(mood)
    setPlaylist(null)
    setLoading(true)
    const params = new URLSearchParams()
    if (genre) params.set('genre', genre)
    if (mood) params.set('mood', mood)
    api.get(`/api/music/browse?${params}`).then(r => setTracks(r.data)).finally(() => setLoading(false))
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (query.trim()) {
      setLoading(true)
      setPlaylist(null)
      api.get(`/api/music/search?q=${encodeURIComponent(query)}`).then(r => setTracks(r.data)).finally(() => setLoading(false))
    }
  }

  const generatePlaylist = (mood) => {
    setLoading(true)
    api.get(`/api/music/playlist?mood=${mood}`).then(r => {
      setPlaylist(r.data)
      setTracks(r.data.tracks)
    }).finally(() => setLoading(false))
  }

  return (
    <div className="container music-page">
      <div className="page-header">
        <h1>Music</h1>
        <p>Discover tracks, create playlists by mood</p>
      </div>

      <form onSubmit={handleSearch} className="search-bar">
        <input type="text" className="input" placeholder="Search by artist, track or album..."
          value={query} onChange={e => setQuery(e.target.value)} />
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      <div className="music-moods">
        <h3>Generate Playlist by Mood</h3>
        <div className="mood-buttons">
          {moods.map(m => (
            <button key={m} className={`btn btn-sm ${activeMood === m ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => generatePlaylist(m)}>
              {m}
            </button>
          ))}
        </div>
      </div>

      {playlist && (
        <div className="playlist-header">
          <h2>{playlist.name}</h2>
          <span className="badge badge-accent">{playlist.tracks?.length} tracks</span>
        </div>
      )}

      <div className="tabs" style={{ marginTop: 16 }}>
        <button className={`tab ${!activeGenre ? 'active' : ''}`} onClick={() => handleFilter(null, null)}>All</button>
        {genres.slice(0, 15).map(g => (
          <button key={g} className={`tab ${activeGenre === g ? 'active' : ''}`} onClick={() => handleFilter(g, null)}>
            {g}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loader"><div className="spinner"></div></div>
      ) : tracks.length === 0 ? (
        <div className="empty-state"><h3>No tracks found</h3></div>
      ) : (
        <div className="track-list">
          {tracks.map((t, i) => (
            <div key={t.id} className={`track-row ${playing === t.id ? 'track-playing' : ''}`}
              onClick={() => setPlaying(playing === t.id ? null : t.id)}>
              <span className="track-num">{i + 1}</span>
              <div className="track-play-icon">{playing === t.id ? '||' : '>'}</div>
              <div className="track-info">
                <span className="track-title">{t.title}</span>
                <span className="track-artist">{t.artist}</span>
              </div>
              <span className="track-album">{t.album}</span>
              <div className="track-genres">
                {t.genres?.slice(0, 2).map(g => (
                  <span key={g} className="badge badge-accent">{g}</span>
                ))}
              </div>
              <span className="track-duration">{t.duration}</span>
            </div>
          ))}
        </div>
      )}

      {playing && (
        <div className="music-player-bar">
          <div className="player-content">
            <div className="player-icon">&#9835;</div>
            <div className="player-info">
              <span className="player-title">{tracks.find(t => t.id === playing)?.title}</span>
              <span className="player-artist">{tracks.find(t => t.id === playing)?.artist}</span>
            </div>
            <div className="player-controls">
              <button className="btn btn-icon btn-secondary" onClick={() => setPlaying(null)}>&#9724;</button>
            </div>
            <div className="player-progress">
              <div className="progress-bar"><div className="progress-fill" style={{ width: '35%' }}></div></div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
