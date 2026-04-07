import { useState } from 'react'
import './Rating.css'

export default function Rating({ value = 0, onChange, size = 'md', readonly = false }) {
  const [hovered, setHovered] = useState(0)

  return (
    <div className={`star-rating star-rating-${size} ${readonly ? 'readonly' : ''}`}>
      {[1, 2, 3, 4, 5].map(star => (
        <span
          key={star}
          className={`star ${(hovered || value) >= star ? 'star-filled' : ''}`}
          onClick={() => !readonly && onChange?.(star)}
          onMouseEnter={() => !readonly && setHovered(star)}
          onMouseLeave={() => !readonly && setHovered(0)}
        >
          &#9733;
        </span>
      ))}
    </div>
  )
}
