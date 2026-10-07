'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { 
  LayoutGrid, 
  Trophy, 
  BookOpen,
  Database,
  FileText
} from 'lucide-react';
import CSMLogo from '@/components/CSMLogo';

const NAV_ITEMS = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutGrid,
    badge: null
  },
  {
    name: 'Data Ingestion',
    href: '/data',
    icon: Database,
    badge: null
  },
  {
    name: 'Leaderboard',
    href: '/students',
    icon: Trophy,
    badge: null
  },
  {
    name: 'Subjects',
    href: '/subjects',
    icon: BookOpen,
    badge: null
  },
  {
    name: 'Reports',
    href: '/reports',
    icon: FileText,
    badge: null
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 lg:w-60 bg-white p-7 flex flex-col justify-between shrink-0 select-none border-r border-slate-100">
      <div>
        {/* Brand Header */}
        <div className="mb-10 pl-1 group cursor-default">
          <div className="flex items-center space-x-3">
            <CSMLogo size="sm" />
            <div>
              <div className="font-black text-2xl text-slate-900 tracking-tight leading-none group-hover:text-emerald-700 transition-colors duration-300">
                CSM
              </div>
              <div className="text-[11px] font-semibold text-slate-500 tracking-wider mt-1">
                VCE College
              </div>
            </div>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="space-y-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href));

            return (
              <a
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-4 py-3 rounded-2xl text-[13px] font-semibold transition-all duration-250 ease-out group ${
                  isActive
                    ? 'bg-[#d9f99d] text-slate-950 shadow-sm translate-x-1 font-bold'
                    : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100/70 hover:translate-x-0.5'
                }`}
              >
                <div className="flex items-center space-x-3.5">
                  <Icon className={`w-4 h-4 transition-transform duration-250 ${isActive ? 'text-slate-950 stroke-[2.5] scale-105' : 'text-slate-600 stroke-[1.8] group-hover:scale-110'}`} />
                  <span className={isActive ? 'font-bold' : 'font-medium'}>{item.name}</span>
                </div>

                {item.badge && (
                  <span className="bg-slate-900 text-white text-[10px] font-extrabold w-5 h-5 rounded-full flex items-center justify-center transition-transform group-hover:scale-105">
                    {item.badge}
                  </span>
                )}
              </a>
            );
          })}
        </nav>
      </div>

      {/* Footer HOD info & copyright */}
      <div className="pt-6 space-y-3">
        <div className="p-3 bg-slate-50 border border-slate-100 rounded-2xl">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-xl bg-[#d9f99d] flex items-center justify-center font-black text-[11px] text-slate-900 shrink-0">
              MJ
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-bold text-slate-900 truncate">
                Prof. M A JABBAR
              </p>
              <p className="text-[10px] font-semibold text-emerald-700">
                HOD • CSM Dept
              </p>
            </div>
          </div>
        </div>

        <p className="text-[10px] text-slate-400 font-normal px-2">
          © 2026 CSM • VCE College
        </p>
      </div>
    </aside>
  );
}

