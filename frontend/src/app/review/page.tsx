'use client'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Navbar from '@/components/Navbar'
import ReviewCard from '@/components/ReviewCard'
import { objectsApi } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { OntologyObject } from '@/types'

export default function ReviewPage() {
  const router = useRouter()
  const { user, loading: authLoading, logout } = useAuth()
  const [items, setItems] = useState<OntologyObject[]>([])
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)

  // Auth guard
  useEffect(() => {
    if (!authLoading && !user) {
      router.replace('/login')
    }
  }, [authLoading, user, router])

  const fetchItems = useCallback(() => {
    if (authLoading || !user) return
    setListLoading(true)
    setListError(null)
    objectsApi
      .list('PENDING_REVIEW')
      .then((res) => {
        const data = res.data
        // Handle both array and paginated response shapes
        setItems(Array.isArray(data) ? data : (data.items ?? data.results ?? []))
      })
      .catch(() => setListError('목록을 불러오는 데 실패했습니다.'))
      .finally(() => setListLoading(false))
  }, [authLoading, user])

  useEffect(() => {
    fetchItems()
  }, [fetchItems])

  const handleApprove = async (id: string) => {
    await objectsApi.approve(id)
    fetchItems()
  }

  const handleReject = async (id: string, reason: string) => {
    await objectsApi.reject(id, reason)
    fetchItems()
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-slate-400 border-t-transparent" />
      </div>
    )
  }

  if (!user) return null

  // Role guard
  if (user.role === 'analyst') {
    return (
      <div className="flex flex-col h-screen bg-slate-100">
        <Navbar user={user} onLogout={logout} />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-2xl text-slate-400 mb-2">🚫</p>
            <p className="text-slate-600 font-medium">접근 권한이 없습니다</p>
            <p className="text-slate-400 text-sm mt-1">이 페이지는 도메인 전문가 또는 관리자만 접근 가능합니다.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-slate-100">
      <Navbar user={user} onLogout={logout} />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-8">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-slate-800">검수 대기 목록</h1>
              {!listLoading && !listError && (
                <p className="text-sm text-slate-500 mt-0.5">
                  총 <span className="font-semibold text-slate-700">{items.length}</span>개 항목
                </p>
              )}
            </div>
            <button
              onClick={fetchItems}
              disabled={listLoading}
              className="text-sm text-slate-600 hover:text-slate-800 border border-slate-300 hover:border-slate-400 rounded-lg px-3 py-1.5 transition-colors disabled:opacity-50"
            >
              새로고침
            </button>
          </div>

          {listLoading && (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-slate-400 border-t-transparent" />
              <span className="text-slate-500 text-sm">목록을 불러오는 중...</span>
            </div>
          )}

          {listError && !listLoading && (
            <div className="flex flex-col items-center justify-center py-20 gap-2">
              <p className="text-red-500 font-medium">{listError}</p>
              <button
                onClick={fetchItems}
                className="text-sm text-slate-600 underline hover:text-slate-800"
              >
                다시 시도
              </button>
            </div>
          )}

          {!listLoading && !listError && items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <p className="text-slate-400 text-lg mb-1">검수 대기 항목이 없습니다</p>
              <p className="text-slate-400 text-sm">PENDING_REVIEW 상태의 항목이 없습니다.</p>
            </div>
          )}

          {!listLoading && !listError && items.length > 0 && (
            <div className="space-y-4">
              {items.map((item) => (
                <ReviewCard
                  key={item.id}
                  item={item}
                  onApprove={handleApprove}
                  onReject={handleReject}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
