'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getToken } from '@/lib/auth'

export default function RootPage() {
  const router = useRouter()

  useEffect(() => {
    if (getToken()) {
      router.replace('/graph')
    } else {
      router.replace('/login')
    }
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="animate-spin rounded-full h-10 w-10 border-4 border-slate-400 border-t-transparent" />
    </div>
  )
}
