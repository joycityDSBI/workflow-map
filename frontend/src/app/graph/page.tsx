'use client'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Navbar from '@/components/Navbar'
import OntologyGraph from '@/components/OntologyGraph'
import { graphApi } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { GraphData, ObjectCategory, OntologyStatus } from '@/types'

interface SelectedNode {
  id: string
  name: string
  category: ObjectCategory
  status: OntologyStatus
}

const CATEGORY_LABELS: Record<ObjectCategory, string> = {
  actor: '행위자',
  domain: '도메인',
  tx: '거래',
  cs: '고객 서비스',
  record: '기록',
}

const STATUS_LABELS: Record<OntologyStatus, string> = {
  DRAFT: '초안',
  PENDING_REVIEW: '검수 대기',
  PUBLISHED: '게시됨',
  REJECTED: '반려됨',
  ARCHIVED: '보관됨',
}

const STATUS_COLORS: Record<OntologyStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700',
  PENDING_REVIEW: 'bg-amber-100 text-amber-700',
  PUBLISHED: 'bg-emerald-100 text-emerald-700',
  REJECTED: 'bg-red-100 text-red-700',
  ARCHIVED: 'bg-slate-200 text-slate-600',
}

const CATEGORY_DOT_COLORS: Record<ObjectCategory, string> = {
  actor: '#6366f1',
  domain: '#10b981',
  tx: '#f59e0b',
  cs: '#ef4444',
  record: '#8b5cf6',
}

export default function GraphPage() {
  const router = useRouter()
  const { user, loading: authLoading, logout } = useAuth()
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [graphLoading, setGraphLoading] = useState(true)
  const [graphError, setGraphError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null)

  // Auth guard
  useEffect(() => {
    if (!authLoading && !user) {
      router.replace('/login')
    }
  }, [authLoading, user, router])

  // Fetch graph data
  useEffect(() => {
    if (authLoading || !user) return
    setGraphLoading(true)
    setGraphError(null)
    graphApi
      .getGraph()
      .then((res) => setGraphData(res.data))
      .catch(() => setGraphError('그래프 데이터를 불러오는 데 실패했습니다.'))
      .finally(() => setGraphLoading(false))
  }, [authLoading, user])

  const handleNodeClick = useCallback((node: SelectedNode) => {
    setSelectedNode(node)
  }, [])

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

      <div className="flex flex-1 overflow-hidden">
        {/* Graph area */}
        <div className="flex-1 relative">
          {graphLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-50 z-10 gap-3">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-slate-400 border-t-transparent" />
              <span className="text-slate-500 text-sm">그래프를 불러오는 중...</span>
            </div>
          )}

          {graphError && !graphLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-50 z-10">
              <div className="text-center">
                <p className="text-red-500 font-medium">{graphError}</p>
                <button
                  onClick={() => {
                    setGraphLoading(true)
                    setGraphError(null)
                    graphApi
                      .getGraph()
                      .then((res) => setGraphData(res.data))
                      .catch(() => setGraphError('그래프 데이터를 불러오는 데 실패했습니다.'))
                      .finally(() => setGraphLoading(false))
                  }}
                  className="mt-3 text-sm text-slate-600 underline hover:text-slate-800"
                >
                  다시 시도
                </button>
              </div>
            </div>
          )}

          {!graphLoading && !graphError && graphData && graphData.nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-50 z-10">
              <p className="text-slate-500">Published된 항목이 없습니다</p>
            </div>
          )}

          {!graphLoading && !graphError && graphData && graphData.nodes.length > 0 && (
            <OntologyGraph data={graphData} onNodeClick={handleNodeClick} />
          )}
        </div>

        {/* Side panel */}
        <div className="w-72 bg-white border-l border-slate-200 flex flex-col shrink-0">
          <div className="px-5 py-4 border-b border-slate-200">
            <h2 className="font-semibold text-slate-700 text-sm">노드 정보</h2>
          </div>

          {selectedNode ? (
            <div className="p-5 space-y-4">
              <div>
                <p className="text-xs text-slate-500 mb-1">이름</p>
                <p className="font-semibold text-slate-800 break-all">{selectedNode.name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">카테고리</p>
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-3 w-3 rounded-full shrink-0"
                    style={{ backgroundColor: CATEGORY_DOT_COLORS[selectedNode.category] }}
                  />
                  <span className="text-slate-800 text-sm">
                    {CATEGORY_LABELS[selectedNode.category] ?? selectedNode.category}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">상태</p>
                <span
                  className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${
                    STATUS_COLORS[selectedNode.status] ?? 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {STATUS_LABELS[selectedNode.status] ?? selectedNode.status}
                </span>
              </div>
              <div>
                <p className="text-xs text-slate-500 mb-1">ID</p>
                <p className="text-xs text-slate-400 font-mono break-all">{selectedNode.id}</p>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center p-5">
              <p className="text-slate-400 text-sm text-center">
                그래프에서 노드를 클릭하면
                <br />
                상세 정보가 표시됩니다
              </p>
            </div>
          )}

          {/* Legend */}
          <div className="mt-auto p-5 border-t border-slate-200">
            <p className="text-xs text-slate-500 mb-3 font-medium">카테고리 범례</p>
            <div className="space-y-2">
              {(Object.entries(CATEGORY_LABELS) as [ObjectCategory, string][]).map(([cat, label]) => (
                <div key={cat} className="flex items-center gap-2">
                  <span
                    className="inline-block h-3 w-3 rounded-full shrink-0"
                    style={{ backgroundColor: CATEGORY_DOT_COLORS[cat] }}
                  />
                  <span className="text-xs text-slate-600">{label}</span>
                  <span className="text-xs text-slate-400 ml-auto">({cat})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
