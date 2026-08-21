'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { CurrentUser } from '@/types'

const roleLabelMap: Record<string, string> = {
  analyst: '분석가',
  domain_expert: '도메인 전문가',
  admin: '관리자',
}

const roleBadgeColorMap: Record<string, string> = {
  analyst: 'bg-blue-500',
  domain_expert: 'bg-emerald-500',
  admin: 'bg-rose-500',
}

interface NavbarProps {
  user: CurrentUser | null
  onLogout: () => void
}

export default function Navbar({ user, onLogout }: NavbarProps) {
  const pathname = usePathname()

  const isReviewVisible = user && (user.role === 'domain_expert' || user.role === 'admin')

  return (
    <nav className="bg-slate-800 text-white h-14 flex items-center px-6 shrink-0">
      <div className="flex items-center gap-6 flex-1">
        <span className="font-bold text-lg tracking-tight">워크플로우 맵</span>

        <div className="flex items-center gap-1">
          <Link
            href="/graph"
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              pathname === '/graph'
                ? 'bg-slate-600 text-white'
                : 'text-slate-300 hover:text-white hover:bg-slate-700'
            }`}
          >
            온톨로지 맵
          </Link>

          <Link
            href="/extract"
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              pathname === '/extract'
                ? 'bg-slate-600 text-white'
                : 'text-slate-300 hover:text-white hover:bg-slate-700'
            }`}
          >
            추출
          </Link>

          {isReviewVisible && (
            <Link
              href="/review"
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                pathname === '/review'
                  ? 'bg-slate-600 text-white'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700'
              }`}
            >
              검수 대기
            </Link>
          )}
        </div>
      </div>

      {user && (
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-300">{user.username}</span>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full text-white ${
              roleBadgeColorMap[user.role] ?? 'bg-slate-500'
            }`}
          >
            {roleLabelMap[user.role] ?? user.role}
          </span>
          <button
            onClick={onLogout}
            className="ml-2 text-xs text-slate-400 hover:text-white border border-slate-600 hover:border-slate-400 rounded px-2.5 py-1 transition-colors"
          >
            로그아웃
          </button>
        </div>
      )}
    </nav>
  )
}
