import { RouterProvider } from "react-router-dom";
import { router } from "@/routes";
import { useEffect } from 'react'
import useAuthStore from '@/store/authStore'

export default function App() {
  const init = useAuthStore((s) => s.init)
  const user = useAuthStore((s) => s.user)
  const loading = useAuthStore((s) => s.loading)
  const initialized = useAuthStore((s) => s.initialized)

  useEffect(() => {
    init()
  }, [init])

  useEffect(() => {
    if (initialized && !loading && user) {
      const redirect = localStorage.getItem('auth_redirect')
      if (redirect) {
        localStorage.removeItem('auth_redirect')
        void router.navigate(redirect, { replace: true })
      }
    }
  }, [initialized, loading, user])

  return <RouterProvider router={router} />;
}
