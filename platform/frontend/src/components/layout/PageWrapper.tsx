import type { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'

interface PageWrapperProps {
  children: ReactNode
}

export function PageWrapper({ children }: PageWrapperProps) {
  const { pathname } = useLocation()

  return (
    <div key={pathname} className="page-fade">
      {children}
    </div>
  )
}