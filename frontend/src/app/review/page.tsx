'use client'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Navbar from '@/components/Navbar'
import ReviewCard from '@/components/ReviewCard'
import { objectsApi, linksApi, actionsApi, rulesApi, reviewApi } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { OntologyObject } from '@/types'

type TabKey = 'objects' | 'links' | 'actions' | 'rules'

const TAB_LABELS: Record<TabKey, string> = {
  objects: '개체',
  links: '관계',
  actions: '행동',
  rules: '규칙',
}

const STATUS = 'PENDING_REVIEW'

export default function ReviewPage() {
  const router = useRouter()
  const { user, loading: authLoading, logout } = useAuth()
  const [tab, setTab] = useState<TabKey>('objects')
  const [items, setItems] = useState<Record<TabKey, OntologyObject[]>>({
    objects: [],
    links: [],
    actions: [],
    rules: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) router.replace('/login')
  }, [authLoading, user, router])

  const fetchAll = useCallback(() => {
    if (authLoading || !user) return
    setLoading(true)
    setError(null)
    Promise.all([
      objectsApi.list(STATUS),
      linksApi.list(STATUS),
      actionsApi.list(STATUS),
      rulesApi.list(STATUS),
    ])
      .then(([objRes, linkRes, actRes, ruleRes]) => {
        const parse = (res: any) => {
          const d = res.data
          return Array.isArray(d) ? d : (d.items ?? d.results ?? [])
        }
        setItems({ objects: parse(objRes), links: parse(linkRes), actions: parse(actRes), rules: parse(ruleRes) })
      })
      .catch(() => setError('목록을 불러오는 데 실패했습니다.'))
      .finally(() => setLoading(false))
  }, [authLoading, user])

  useEffect(() => { fetchAll() }, [fetchAll])

  const handleApprove = async (id: string) => {
    await reviewApi.approve(id)
    fetchAll()
  }

  const handleReject = async (id: string, reason: string) => {
    await reviewApi.reject(id, reason)
    fetchAll()
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-slate-400 border-t-transparent" />
      </div>
    )
  }
  if (!user) return null

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

  const currentItems = items[tab]
  const totalAll = items.objects.length + items.links.length + items.actions.length

  return (
    <div className="flex flex-col h-screen bg-slate-100">
      <Navbar user={user} onLogout={logout} />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-6 py-8">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-slate-800">검수 대기 목록</h1>
              {!loading && !error && (
                <p className="text-sm text-slate-500 mt-0.5">
                  전체 <span className="font-semibold text-slate-700">{totalAll}</span>개 항목 대기 중
                </p>
              )}
            </div>
            <button
              onClick={fetchAll}
              disabled={loading}
              className="text-sm text-slate-600 hover:text-slate-800 border border-slate-300 hover:border-slate-400 rounded-lg px-3 py-1.5 transition-colors disabled:opacity-50"
            >
              새로고침
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-slate-200 p-1 rounded-lg w-fit">
            {(Object.keys(TAB_LABELS) as TabKey[]).map((key) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  tab === key
                    ? 'bg-white text-slate-800 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {TAB_LABELS[key]}
                {!loading && items[key].length > 0 && (
                  <span className="ml-1.5 bg-amber-100 text-amber-700 text-xs font-semibold px-1.5 py-0.5 rounded-full">
                    {items[key].length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Content */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-slate-400 border-t-transparent" />
              <span className="text-slate-500 text-sm">목록을 불러오는 중...</span>
            </div>
          )}

          {error && !loading && (
            <div className="flex flex-col items-center justify-center py-20 gap-2">
              <p className="text-red-500 font-medium">{error}</p>
              <button onClick={fetchAll} className="text-sm text-slate-600 underline hover:text-slate-800">
                다시 시도
              </button>
            </div>
          )}

          {!loading && !error && currentItems.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <p className="text-4xl mb-3">✅</p>
              <p className="text-slate-600 font-medium">{TAB_LABELS[tab]} 검수 대기 항목이 없습니다</p>
              <p className="text-slate-400 text-sm mt-1">모든 {TAB_LABELS[tab]}이 검수 완료됐습니다.</p>
            </div>
          )}

          {!loading && !error && currentItems.length > 0 && (
            <div className="space-y-4">
              {currentItems.map((item) => (
                <ReviewCard
                  key={item.id}
                  item={item}
                  itemType={tab}
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
