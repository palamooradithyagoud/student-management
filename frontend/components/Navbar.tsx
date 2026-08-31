'use client';

import React from 'react';
import { ShieldCheck } from 'lucide-react';
import CSMLogo from '@/components/CSMLogo';

export default function Navbar() {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Department info */}
          <div className="flex items-center space-x-3">
            <CSMLogo size="sm" />
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base sm:text-lg tracking-tight text-white">
                  CSM Academic Intelligence
                </span>
                <span className="bg-emerald-950 text-emerald-300 text-xs px-2 py-0.5 rounded-full border border-emerald-800 font-medium">
                  Phase 1
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Dept. of Computer Science & Engineering (AI & ML)
              </p>
            </div>
          </div>

          {/* HOD Profile */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-lg">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <div className="text-left">
                <p className="text-xs font-semibold text-slate-200">
                  Prof. M A JABBAR
                </p>
                <p className="text-[10px] text-emerald-400 font-mono font-medium">
                  HOD • CSM
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

