import { useSpring, animated } from '@react-spring/web'

interface SpringNumberProps {
  value:      number
  formatter?: (n: number) => string
  style?:     React.CSSProperties
  className?: string
}

export function SpringNumber({ value, formatter, style, className }: SpringNumberProps) {
  const fmt = formatter ?? ((n: number) => Math.round(n).toLocaleString())
  const { num } = useSpring({
    num:    value,
    config: { tension: 200, friction: 18 },
  })
  return (
    <animated.span style={style} className={className}>
      {num.to(n => fmt(n))}
    </animated.span>
  )
}
