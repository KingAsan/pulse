import { useState, memo, useCallback } from 'react'
import './Rating.css'

const Rating = memo(function Rating({ value = 0, onChange, size = 'md', readonly = false }) {
  const [hovered, setHovered] = useState(0)

  const handleClick = useCallback((star) => {
    if (!readonly && onChange) {
      onChange(star)
    }
  }, [readonly, onChange])

  const handleMouseEnter = useCallback((star) => {
    if (!readonly) setHovered(star)
  }, [readonly])

  const handleMouseLeave = useCallback(() => {
    if (!readonly) setHovered(0)
  }, [readonly])

  return (
    <div className={`star-rating star-rating-${size} ${readonly ? 'readonly' : ''}`}>
      {[1, 2, 3, 4, 5].map(star => (
        <span
          key={star}
          className={`star ${(hovered || value) >= star ? 'star-filled' : ''}`}
          onClick={() => handleClick(star)}
          onMouseEnter={() => handleMouseEnter(star)}
          onMouseLeave={handleMouseLeave}
          role={readonly ? 'img' : 'button'}
          aria-label={`${star} star${star > 1 ? 's' : ''}`}
          tabIndex={readonly ? -1 : 0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              handleClick(star)
            }
          }}
        >
          &#9733;
        </span>
      ))}
    </div>
  )
})

export default Rating
