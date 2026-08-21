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

interface ReviewCardProps {
  item: OntologyObject
  onApprove: (id: string) => Promise<void>
  onReject: (id: string, reason: string) => Promise<void>
}

export default function ReviewCard({ item, onApprove, onReject }: ReviewCardProps) {
  const [rejectOpen, setRejectOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)

  const handleApprove = async () => {
    setApproving(true)
    try {
      await onApprove(item.id)
    } finally {
      setApproving(false)
    }
  }

  const handleReject = async () => {
    if (!reason.trim()) return
    setRejecting(true)
    try {
      await onReject(item.id, reason.trim())
      setRejectOpen(false)
      setReason('')
    } finally {
      setRejecting(false)
    }
  }

  const createdDate = new Date(item.created_at).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <h3 className="font-semibold text-slate-800 text-base truncate">{item.name}</h3>
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${
                CATEGORY_COLORS[item.category] ?? 'bg-slate-100 text-slate-700'
              }`}
            >
              {CATEGORY_LABELS[item.category] ?? item.category}
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <span>
              신뢰도:{' '}
              {item.confidence !== null && item.confidence !== undefined
                ? `${Math.round(item.confidence * 100)}%`
                : '—'}
            </span>
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
            ) : (
              '승인'
            )}
          </button>

          <button
            onClick={() => setRejectOpen((prev) => !prev)}
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
