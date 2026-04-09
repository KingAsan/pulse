import { useEffect, useRef, useCallback } from 'react'

export function useSwipe(onSwipeLeft, onSwipeRight, threshold = 50) {
  const touchStartRef = useRef(null)
  const touchEndRef = useRef(null)
  const onSwipeLeftRef = useRef(onSwipeLeft)
  const onSwipeRightRef = useRef(onSwipeRight)

  // Keep callbacks up-to-date without re-running effect
  useEffect(() => {
    onSwipeLeftRef.current = onSwipeLeft
    onSwipeRightRef.current = onSwipeRight
  }, [onSwipeLeft, onSwipeRight])

  useEffect(() => {
    const minSwipeDistance = threshold

    const handleTouchStart = (e) => {
      touchStartRef.current = e.targetTouches[0].clientX
      touchEndRef.current = null
    }

    const handleTouchMove = (e) => {
      touchEndRef.current = e.targetTouches[0].clientX
    }

    const handleTouchEnd = () => {
      if (!touchStartRef.current || !touchEndRef.current) return
      
      const distance = touchStartRef.current - touchEndRef.current
      const isLeftSwipe = distance > minSwipeDistance
      const isRightSwipe = distance < -minSwipeDistance

      if (isLeftSwipe && onSwipeLeftRef.current) {
        onSwipeLeftRef.current()
      }

      if (isRightSwipe && onSwipeRightRef.current) {
        onSwipeRightRef.current()
      }

      // Reset
      touchStartRef.current = null
      touchEndRef.current = null
    }

    // Add passive event listeners for better performance
    document.addEventListener('touchstart', handleTouchStart, { passive: true })
    document.addEventListener('touchmove', handleTouchMove, { passive: true })
    document.addEventListener('touchend', handleTouchEnd, { passive: true })

    return () => {
      document.removeEventListener('touchstart', handleTouchStart)
      document.removeEventListener('touchmove', handleTouchMove)
      document.removeEventListener('touchend', handleTouchEnd)
    }
  }, [threshold])
}
