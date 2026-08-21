'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Navbar from '@/components/Navbar'
import { extractionApi } from '@/lib/api'
import { useAuth } from '@/lib/auth'

type SourceType = 'text' | 'notion'

interface Job {
  id: string
  status: 'RUNNING' | 'COMPLETED' | 'PARTIAL_SUCCESS' | 'FAILED' | 'RATE_LIMITED'
  source_type: string
  total_docs: number
  success_docs: number
  failed_docs: number
  error_details: Array<{ ref: string; error: string }>
  created_at: string
  completed_at: string | null
}

const STATUS_CONFIG: Record<Job['status'], { label: string; color: string; dot: string }> = {
  RUNNING:         { label: '실행 중',      color: 'bg-blue-100 text-blue-700',   dot: 'bg-blue-500 animate-pulse' },
  COMPLETED:       { label: '완료',         color: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500' },
  PARTIAL_SUCCESS: { label: '일부 성공',    color: 'bg-amber-100 text-amber-700', dot: 'bg-amber-500' },
  FAILED:          { label: '실패',         color: 'bg-red-100 text-red-700',     dot: 'bg-red-500' },
  RATE_LIMITED:    { label: '속도 제한',    color: 'bg-orange-100 text-orange-700', dot: 'bg-orange-500' },
}

export default function ExtractPage() {
  const router = useRouter()
  const { user, loading: authLoading, logout } = useAuth()

  const [sourceType, setSourceType] = useState<SourceType>('text')
  const [textInput, setTextInput] = useState('')
  const [notionUrls, setNotionUrls] = useState<string[]>([''])
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const [jobs, setJobs] = useState<Job[]>([])
  const [jobsLoading, setJobsLoading] = useState(true)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!authLoading && !user) router.replace('/login')
  }, [authLoading, user, router])

  const fetchJobs = useCallback(async () => {
    try {
      const res = await extractionApi.list()
      const data = res.data
      setJobs(Array.isArray(data) ? data : (data.items ?? []))
    } catch {
      // silent
    } finally {
      setJobsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (authLoading || !user) return
    fetchJobs()
    pollingRef.current = setInterval(fetchJobs, 4000)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [authLoading, user, fetchJobs])

  const handleSubmit = async () => {
    setSubmitError(null)
    const refs =
      sourceType === 'text'
        ? [textInput.trim()].filter(Boolean)
        : notionUrls.map((u) => u.trim()).filter(Boolean)

    if (refs.length === 0) {
      setSubmitError(sourceType === 'text' ? '텍스트를 입력하세요.' : 'Notion URL을 하나 이상 입력하세요.')
      return
    }

    setSubmitting(true)
    try {
      await extractionApi.create(sourceType, refs)
      if (sourceType === 'text') setTextInput('')
      else setNotionUrls([''])
      fetchJobs()
    } catch (err: any) {
      setSubmitError(err?.response?.data?.detail ?? '추출 요청에 실패했습니다.')
    } finally {
      setSubmitting(false)
    }
  }

  const addUrl = () => setNotionUrls((prev) => [...prev, ''])
  const removeUrl = (i: number) => setNotionUrls((prev) => prev.filter((_, idx) => idx !== i))
  const updateUrl = (i: number, val: string) =>
    setNotionUrls((prev) => prev.map((u, idx) => (idx === i ? val : u)))

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-slate-400 border-t-transparent" />
      </div>
    )
  }
  if (!user) return null

  return (
    <div className="flex flex-col h-screen bg-slate-100">
      <Navbar user={user} onLogout={logout} />

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-6 py-8 space-y-8">

          {/* ── 입력 폼 ─────────────────────────────────────────── */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h1 className="text-lg font-bold text-slate-800 mb-5">온톨로지 추출</h1>

            {/* Source type toggle */}
            <div className="flex gap-1 mb-5 bg-slate-100 p-1 rounded-lg w-fit">
              {(['text', 'notion'] as SourceType[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setSourceType(t)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    sourceType === t
                      ? 'bg-white text-slate-800 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {t === 'text' ? '📝 텍스트 직접 입력' : '🔗 Notion URL'}
                </button>
              ))}
            </div>

            {/* Text input */}
            {sourceType === 'text' && (
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                rows={8}
                placeholder="온톨로지를 추출할 문서 내용을 입력하세요.&#10;예) 플레이어는 골드와 젬을 보유한다. 상점에서 아이템을 구매할 수 있다..."
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent resize-none"
              />
            )}

            {/* Notion URL inputs */}
            {sourceType === 'notion' && (
              <div className="space-y-2">
                {notionUrls.map((url, i) => (
                  <div key={i} className="flex gap-2">
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => updateUrl(i, e.target.value)}
                      placeholder="https://www.notion.so/..."
                      className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                    />
                    {notionUrls.length > 1 && (
                      <button
                        onClick={() => removeUrl(i)}
                        className="text-slate-400 hover:text-red-500 transition-colors px-2"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button
                  onClick={addUrl}
                  className="text-sm text-indigo-600 hover:text-indigo-800 transition-colors mt-1"
                >
                  + URL 추가
                </button>
              </div>
            )}

            {submitError && (
              <p className="mt-3 text-sm text-red-500">{submitError}</p>
            )}

            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="mt-5 w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  추출 요청 중...
                </>
              ) : '추출 시작'}
            </button>
          </div>

          {/* ── 최근 잡 목록 ────────────────────────────────────── */}
          <div>
            <h2 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wide">최근 추출 작업</h2>

            {jobsLoading && (
              <div className="flex items-center justify-center py-10">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-slate-400 border-t-transparent" />
              </div>
            )}

            {!jobsLoading && jobs.length === 0 && (
              <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
                <p className="text-slate-400 text-sm">추출 작업 이력이 없습니다</p>
              </div>
            )}

            {!jobsLoading && jobs.length > 0 && (
              <div className="space-y-3">
                {jobs.map((job) => {
                  const cfg = STATUS_CONFIG[job.status] ?? STATUS_CONFIG.FAILED
                  return (
                    <div key={job.id} className="bg-white rounded-xl border border-slate-200 p-4">
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`inline-block h-2 w-2 rounded-full ${cfg.dot}`} />
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cfg.color}`}>
                            {cfg.label}
                          </span>
                          <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                            {job.source_type}
                          </span>
                        </div>
                        <span className="text-xs text-slate-400">
                          {new Date(job.created_at).toLocaleString('ko-KR')}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-slate-600">
                          문서 <span className="font-semibold text-slate-800">{job.total_docs}</span>개
                        </span>
                        <span className="text-emerald-600">
                          성공 <span className="font-semibold">{job.success_docs}</span>
                        </span>
                        {job.failed_docs > 0 && (
                          <span className="text-red-500">
                            실패 <span className="font-semibold">{job.failed_docs}</span>
                          </span>
                        )}
                      </div>

                      {job.error_details.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {job.error_details.map((e, i) => (
                            <p key={i} className="text-xs text-red-400 bg-red-50 rounded px-2 py-1 truncate" title={e.error}>
                              {e.ref}: {e.error}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}
