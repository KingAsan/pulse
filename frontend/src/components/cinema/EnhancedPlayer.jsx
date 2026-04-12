import { useState, useEffect, useRef, useCallback } from 'react'
import './EnhancedPlayer.css'

/**
 * Enhanced Player Wrapper for HDRezka iframe
 * Adds keyboard shortcuts, cinema mode, PiP, and better UX
 */
export default function EnhancedPlayer({ 
  embedUrl, 
  title, 
  poster,
  onEpisodeEnd,
  hasNextEpisode,
  onNextEpisode 
}) {
  const iframeRef = useRef(null)
  const containerRef = useRef(null)
  
  const [isCinemaMode, setIsCinemaMode] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const controlsTimeoutRef = useRef(null)

  // Cinema mode - dim the rest of the page
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
    if (!container) return

    const handleMouseMove = () => {
      setShowControls(true)
      clearTimeout(controlsTimeoutRef.current)
      controlsTimeoutRef.current = setTimeout(() => {
        if (!isFullscreen || showControls) {
          setShowControls(false)
        }
      }, 3000)
    }

    container.addEventListener('mousemove', handleMouseMove)
    return () => {
      container.removeEventListener('mousemove', handleMouseMove)
      clearTimeout(controlsTimeoutRef.current)
    }
  }, [isFullscreen, showControls])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Only handle if player is visible
      if (!containerRef.current) return
      
      const tagName = document.activeElement?.tagName
      if (tagName === 'INPUT' || tagName === 'TEXTAREA') return

      switch(e.key.toLowerCase()) {
        case 'f':
          e.preventDefault()
          toggleFullscreen()
          break
        case 'c':
          e.preventDefault()
          setIsCinemaMode(prev => !prev)
          break
        case 'm':
          e.preventDefault()
          toggleMute()
          break
        case 'arrowright':
          e.preventDefault()
          seekForward()
          break
        case 'arrowleft':
          e.preventDefault()
          seekBackward()
          break
        case 'escape':
          if (isCinemaMode) {
            setIsCinemaMode(false)
          }
          break
        default:
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isCinemaMode, isFullscreen])

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen?.()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen?.()
      setIsFullscreen(false)
    }
  }, [])

  const toggleMute = useCallback(() => {
    // Try to communicate with iframe
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ action: 'toggleMute' }, '*')
    }
  }, [])

  const seekForward = useCallback(() => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ action: 'seek', seconds: 10 }, '*')
    }
  }, [])

  const seekBackward = useCallback(() => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ action: 'seek', seconds: -10 }, '*')
    }
  }, [])

  const togglePiP = useCallback(async () => {
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture()
      } else if (iframeRef.current) {
        // Request PiP from iframe if supported
        iframeRef.current.contentWindow?.postMessage({ action: 'togglePiP' }, '*')
      }
    } catch (err) {
      console.warn('PiP not supported:', err)
    }
  }, [])

  const setSpeed = useCallback((speed) => {
    setPlaybackSpeed(speed)
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({ action: 'setSpeed', speed }, '*')
    }
  }, [])

  return (
    <div 
      ref={containerRef}
      className={`enhanced-player ${isCinemaMode ? 'cinema-mode' : ''} ${isFullscreen ? 'fullscreen' : ''}`}
    >
      {/* Player Header */}
      <div className={`player-header ${!showControls && 'hidden'}`}>
        <div className="player-title">
          <span className="player-icon">▶</span>
          <h3>{title}</h3>
        </div>
        <div className="player-actions">
          <button 
            className="player-btn" 
            onClick={() => setIsCinemaMode(!isCinemaMode)}
            title="Кинематографический режим (C)"
          >
            <span className="btn-icon">🎬</span>
            <span className="btn-label">Cinema</span>
          </button>
          <button 
            className="player-btn" 
            onClick={togglePiP}
            title="Picture-in-Picture"
          >
            <span className="btn-icon">📌</span>
          </button>
        </div>
      </div>

      {/* Iframe Container */}
      <div className="player-iframe-wrapper">
        <iframe
          ref={iframeRef}
          src={embedUrl}
          allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
          allowFullScreen
          className="player-iframe"
          title={title}
        />
        
        {/* Custom Controls Overlay */}
        <div className={`player-overlay ${!showControls && 'hidden'}`}>
          {/* Speed Controls */}
          <div className="speed-controls">
            <span className="speed-label">Скорость:</span>
            {[0.5, 0.75, 1, 1.25, 1.5, 2].map(speed => (
              <button
                key={speed}
                className={`speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
                onClick={() => setSpeed(speed)}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Player Footer */}
      <div className={`player-footer ${!showControls && 'hidden'}`}>
        <div className="player-controls">
          <button className="control-btn" onClick={() => seekBackward()} title="Назад 10с (←)">
            ⏪
          </button>
          <button className="control-btn" onClick={toggleMute} title="Mute (M)">
            🔊
          </button>
          <button className="control-btn" onClick={() => seekForward()} title="Вперед 10с (→)">
            ⏩
          </button>
        </div>
        <div className="player-info">
          <span className="info-item">F - Fullscreen</span>
          <span className="info-item">C - Cinema Mode</span>
          <span className="info-item">M - Mute</span>
        </div>
        <button className="control-btn fullscreen-btn" onClick={toggleFullscreen} title="Fullscreen (F)">
          ⛶
        </button>
      </div>

      {/* Next Episode Button */}
      {hasNextEpisode && onEpisodeEnd && (
        <div className="next-episode-prompt">
          <div className="prompt-content">
            <span className="prompt-icon">⏭</span>
            <span>Следующая серия?</span>
            <button className="next-btn" onClick={onNextEpisode}>
              Смотреть дальше
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
