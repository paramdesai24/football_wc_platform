import { useSpring, animated } from '@react-spring/web'
import { useEffect, useState } from 'react'

interface SpringCardProps {
  children:   React.ReactNode
  style?:     React.CSSProperties
  className?: string
  delay?:     number   // ms
  onClick?:   () => void
}

export function SpringCard({
  children, style, className, delay = 0, onClick
}: SpringCardProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  const spring = useSpring({
    from:   { opacity: 0, transform: 'translateY(12px) scale(0.98)' },
    to:     mounted
      ? { opacity: 1, transform: 'translateY(0px) scale(1)' }
      : { opacity: 0, transform: 'translateY(12px) scale(0.98)' },
    config: { tension: 280, friction: 22 },
  })

  return (
    <animated.div style={{ ...spring, ...style }} className={className} onClick={onClick}>
      {children}
    </animated.div>
  )
}
