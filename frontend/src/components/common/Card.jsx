import { useNavigate } from 'react-router-dom'
import './Card.css'

export default function Card({ image, title, subtitle, rating, badge, link, type, children }) {
  const navigate = useNavigate()

  const handleClick = () => {
    if (link) navigate(link)
  }

  return (
    <div className={`card ${link ? 'card-clickable' : ''} card-${type || 'default'}`} onClick={handleClick}>
      <div className="card-image-wrapper">
        {image ? (
          <img src={image} alt={title} className="card-image" loading="lazy" />
        ) : (
          <div className="card-image-placeholder">
            <span>{title?.[0] || '?'}</span>
          </div>
        )}
        {rating > 0 && (
          <div className="card-rating">
            <span>&#9733;</span> {typeof rating === 'number' ? rating.toFixed(1) : rating}
          </div>
        )}
        {badge && <div className="card-badge">{badge}</div>}
      </div>
      <div className="card-body">
        <h3 className="card-title">{title}</h3>
        {subtitle && <p className="card-subtitle">{subtitle}</p>}
        {children}
      </div>
    </div>
  )
}
