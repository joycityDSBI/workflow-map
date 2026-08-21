'use client'
import { useState, useEffect } from 'react'
import { CurrentUser } from '@/types'
import { authApi } from './api'

const TOKEN_KEY = 'wfmap_token'

export const getToken = () =>
  typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null

export const setToken = (token: string) =>
  localStorage.setItem(TOKEN_KEY, token)

export const removeToken = () =>
  localStorage.removeItem(TOKEN_KEY)

export const useAuth = () => {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (!token) { setLoading(false); return }
    authApi.me()
      .then((res) => setUser(res.data))
      .catch(() => removeToken())
      .finally(() => setLoading(false))
  }, [])

  const logout = () => {
    removeToken()
    window.location.href = '/login'
  }

  return { user, loading, logout }
}
