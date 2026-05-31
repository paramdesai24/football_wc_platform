import { create } from 'zustand'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
  id: string
  message: string
  type: ToastType
  duration: number
}

interface ToastState {
  toasts: Toast[]
  add: (message: string, type?: ToastType, duration?: number) => void
  remove: (id: string) => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  add: (message, type = 'info', duration = 3000) => {
    const id = Math.random().toString(36).slice(2)
    set((state) => ({ toasts: [...state.toasts, { id, message, type, duration }] }))
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }))
    }, duration)
  },
  remove: (id) => set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) })),
}))

export const toast = {
  success: (msg: string) => useToastStore.getState().add(msg, 'success'),
  error: (msg: string) => useToastStore.getState().add(msg, 'error', 4000),
  info: (msg: string) => useToastStore.getState().add(msg, 'info'),
  warning: (msg: string) => useToastStore.getState().add(msg, 'warning'),
}