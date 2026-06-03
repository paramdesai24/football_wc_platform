import { useEffect, useRef, useState } from 'react'

export function useAnimatedNumber(
  target: number,
  duration: number = 400,
  formatter?: (n: number) => string
): string {
  const [display, setDisplay] = useState(target)
  const startRef  = useRef(target)
  const startTime = useRef<number | null>(null)
  const rafRef    = useRef<number | undefined>(undefined)
  const fmt = formatter ?? ((n: number) => Math.round(n).toLocaleString())

  useEffect(() => {
    const from = startRef.current
    if (from === target) return

    startTime.current = null
    if (rafRef.current) cancelAnimationFrame(rafRef.current)

    function tick(now: number) {
      if (!startTime.current) startTime.current = now
      const elapsed  = now - startTime.current
      const progress = Math.min(elapsed / duration, 1)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(from + (target - from) * eased)
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick)
      } else {
        startRef.current = target
        setDisplay(target)
      }
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [target, duration])

  return fmt(display)
}
