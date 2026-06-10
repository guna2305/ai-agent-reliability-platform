import { type LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'

interface StatCardProps {
  title: string
  value: string | number
  delta?: string
  deltaPositive?: boolean
  icon: LucideIcon
  iconColor?: string
}

export function StatCard({ title, value, delta, deltaPositive, icon: Icon, iconColor = 'text-brand-400' }: StatCardProps) {
  return (
    <div className="card flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-400 font-medium">{title}</p>
        <p className="mt-1 text-2xl font-bold text-white">{value}</p>
        {delta && (
          <p className={clsx('mt-1 text-xs font-medium', deltaPositive ? 'text-green-400' : 'text-red-400')}>
            {deltaPositive ? '↑' : '↓'} {delta}
          </p>
        )}
      </div>
      <div className={clsx('p-2.5 rounded-lg bg-gray-800', iconColor)}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  )
}
