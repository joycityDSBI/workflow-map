'use client'
import { useState } from 'react'
import { OntologyObject, ObjectCategory } from '@/types'

const CATEGORY_LABELS: Record<ObjectCategory, string> = {
  actor: '행위자',
  domain: '도메인',
  tx: '거래',
  cs: '고객 서비스',
  record: '기록',
}

const CATEGORY_COLORS: Record<ObjectCategory, string> = {
  actor: 'bg-indigo-100 text-indigo-700',
  domain: 'bg-emerald-100 text-emerald-700',
  tx: 'bg-amber-100 text-amber-700',
  cs: 'bg-red-100 text-red-700',
  record: 'bg-violet-100 text-violet-700',
}

type ItemType = 'objects' | 'links' | 'actions' | 'rules'

interface ReviewCardProps {
  item: any   // OntologyObject | Link | Action
  itemType: ItemType
  onApprove: (id: string) => Promise<void>
  onReject: (id: string, reason: string) => Promise<void>
}

function ItemSummary({ item, itemType }: { item: any; itemType: ItemType }) {
  if (itemType === 'objects') {
    return (
      <div className="flex items-center gap-2 flex-wrap mb-2">
        <h3 className="font-semibold text-slate-800 text-base">{item.name}</h3>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${CATEGORY_COLORS[item.category as ObjectCategory] ?? 'bg-slate-100 text-slate-700'}`}>
          {CATEGORY_LABELS[item.category as ObjectCategory] ?? item.category}
        </span>
      </div>
    )
  }
  if (itemType === 'links') {
    return (
      <div className="mb-2">
        <h3 className="font-semibold text-slate-800 text-base flex items-center gap-2 flex-wrap">
          <span className="bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded font-mono">{item.from_id?.slice(0, 8)}…</span>
          <span className="text-slate-400">─{item.label}→</span>
          <span className="bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded font-mono">{item.to_id?.slice(0, 8)}…</span>
        </h3>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs text-slate-500">대응: {item.cardinality}</span>
          {item.is_derived && <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">파생</span>}
        </div>
      </div>
    )
  }
  if (itemType === 'rules') {
    return (
      <div className="mb-2">
        <h3 className="font-semibold text-slate-800 text-base">{item.title ?? item.name}</h3>
        {item.description && (
          <p className="text-sm text-slate-500 mt-1">{item.description}</p>
        )}
        {item.applies_to_actions?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {item.applies_to_actions.map((a: string, i: number) => (
              <span key={i} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">{a}</span>
            ))}
          </div>
        )}
      </div>
    )
  }
  // actions
  return (
    <div className="mb-2">
      <h3 className="font-semibold text-slate-800 text-base">{item.name}</h3>
      {item.trigger && (
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded mt-1 inline-block">{item.trigger}</span>
      )}
    </div>
  )
}

export default function ReviewCard({ item, itemType, onApprove, onReject }: ReviewCardProps) {
  const [rejectOpen, setRejectOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)

  const handleApprove = async () => {
    setApproving(true)
    try { await onApprove(item.id) } finally { setApproving(false) }
  }

  const handleReject = async () => {
    if (!reason.trim()) return
    setRejecting(true)
    try {
      await onReject(item.id, reason.trim())
      setRejectOpen(false)
      setReason('')
    } finally { setRejecting(false) }
  }

  const createdDate = new Date(item.created_at).toLocaleDateString('ko-KR', {
    year: 'numeric', month: 'short', day: 'numeric',
  })

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <ItemSummary item={item} itemType={itemType} />
          <div className="flex items-center gap-4 text-sm text-slate-500">
            {item.confidence != null && (
              <span>신뢰도: {Math.round(Number(item.confidence) * 100)}%</span>
            )}
            <span>생성일: {createdDate}</span>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleApprove}
            disabled={approving || rejecting}
            className="px-4 py-1.5 rounded-lg text-sm font-medium bg-emerald-500 hover:bg-emerald-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {approving ? (
              <span className="flex items-center gap-1">
                <span className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-white border-t-transparent" />
                처리 중
              </span>
            ) : '승인'}
          </button>
          <button
            onClick={() => setRejectOpen((p) => !p)}
            disabled={approving || rejecting}
            className="px-4 py-1.5 rounded-lg text-sm font-medium bg-red-500 hover:bg-red-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            반려
          </button>
        </div>
      </div>

      {rejectOpen && (
        <div className="mt-4 pt-4 border-t border-slate-100">
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            반려 사유 <span className="text-red-500">*</span>
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            placeholder="반려 사유를 입력하세요"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent resize-none"
          />
          <div className="flex gap-2 mt-2 justify-end">
            <button
              onClick={() => { setRejectOpen(false); setReason('') }}
              className="px-3 py-1.5 text-sm text-slate-600 hover:text-slate-800 border border-slate-300 rounded-lg transition-colors"
            >
              취소
            </button>
            <button
              onClick={handleReject}
              disabled={rejecting || !reason.trim()}
              className="px-4 py-1.5 text-sm font-medium bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {rejecting ? '처리 중...' : '반려 확인'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
