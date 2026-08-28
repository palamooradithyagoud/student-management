import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  badge?: {
    text: string;
    variant: 'emerald' | 'amber' | 'blue' | 'rose' | 'slate';
  };
  trend?: string;
}

const variantStyles = {
  emerald: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  amber: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  blue: 'bg-blue-500/10 text-blue-300 border-blue-500/30',
  rose: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
  slate: 'bg-slate-800 text-slate-300 border-slate-700',
};

export default function MetricCard({ title, value, subtitle, icon: Icon, badge, trend }: MetricCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm hover:border-slate-700 transition-all">
      <div className="flex items-start justify-between">
        <div className="bg-slate-800/80 p-2.5 rounded-xl text-emerald-400 border border-slate-700">
          <Icon className="w-5 h-5" />
        </div>
        {badge && (
          <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${variantStyles[badge.variant]}`}>
            {badge.text}
          </span>
        )}
      </div>

      <div className="mt-4">
        <p className="text-xs font-medium text-slate-400">{title}</p>
        <p className="text-2xl font-bold text-white tracking-tight mt-1">{value}</p>
        {subtitle && (
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
