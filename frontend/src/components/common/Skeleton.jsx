import './Skeleton.css'

export function SkeletonCard({ count = 3 }) {
  return (
    <div className="skeleton-grid" style={{ '--count': count }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-image" />
          <div className="skeleton-body">
            <div className="skeleton-line skeleton-line-title" />
            <div className="skeleton-line skeleton-line-subtitle" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function SkeletonText({ lines = 3, width = '100%' }) {
  return (
    <div className="skeleton-text" style={{ width }}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton-line"
          style={{
            width: i === lines - 1 ? '60%' : '100%',
          }}
        />
      ))}
    </div>
  )
}

export function SkeletonAvatar({ size = 40 }) {
  return <div className="skeleton-avatar" style={{ width: size, height: size }} />
}

export function SkeletonCircle({ size = 24 }) {
  return <div className="skeleton-circle" style={{ width: size, height: size }} />
}

export function SkeletonButton({ width = 120, height = 40 }) {
  return <div className="skeleton-button" style={{ width, height }} />
}

// Page-specific skeletons
export function SkeletonMovieCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton-image" style={{ paddingTop: '150%' }} />
      <div className="skeleton-body">
        <div className="skeleton-line skeleton-line-title" />
        <div className="skeleton-line skeleton-line-subtitle" />
      </div>
    </div>
  )
}

export function SkeletonEventCard() {
  return (
    <div className="skeleton-card skeleton-event-card">
      <div className="skeleton-body" style={{ display: 'flex', gap: '12px' }}>
        <div className="skeleton-circle" style={{ width: 50, height: 50, flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div className="skeleton-line skeleton-line-title" />
          <div className="skeleton-line skeleton-line-subtitle" />
          <div className="skeleton-line" style={{ width: '30%', height: 18, marginTop: 6 }} />
        </div>
      </div>
    </div>
  )
}

export function SkeletonMusicCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton-image" style={{ paddingTop: '100%' }} />
      <div className="skeleton-body">
        <div className="skeleton-line skeleton-line-title" />
        <div className="skeleton-line skeleton-line-subtitle" />
      </div>
    </div>
  )
}

export function SkeletonProfile() {
  return (
    <div className="skeleton-profile">
      <div className="skeleton-profile-header">
        <SkeletonAvatar size={76} />
        <div style={{ flex: 1 }}>
          <div className="skeleton-line skeleton-line-title" style={{ width: '50%' }} />
          <div className="skeleton-line skeleton-line-subtitle" style={{ width: '40%' }} />
        </div>
      </div>
    </div>
  )
}

export function SkeletonChatMessage() {
  return (
    <div className="skeleton-chat-message">
      <SkeletonCircle size={32} />
      <div style={{ flex: 1 }}>
        <div className="skeleton-line" style={{ width: '20%', marginBottom: 8 }} />
        <div className="skeleton-line" style={{ width: '100%' }} />
        <div className="skeleton-line" style={{ width: '85%' }} />
        <div className="skeleton-line" style={{ width: '40%' }} />
      </div>
    </div>
  )
}

// Generic loading wrapper
export function SkeletonLoader({ type = 'card', count = 3, children, loading }) {
  if (!loading) return children

  const skeletons = {
    card: <SkeletonCard count={count} />,
    movie: <SkeletonCard count={count} />,
    event: Array.from({ length: count }).map((_, i) => <SkeletonEventCard key={i} />),
    music: Array.from({ length: count }).map((_, i) => <SkeletonMusicCard key={i} />),
    text: <SkeletonText lines={count} />,
    profile: <SkeletonProfile />,
    chat: Array.from({ length: count }).map((_, i) => <SkeletonChatMessage key={i} />),
  }

  return skeletons[type] || skeletons.card
}
