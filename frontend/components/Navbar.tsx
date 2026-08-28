'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck, LogOut, GraduationCap } from 'lucide-react';
import { getAuthUser, clearAuthSession, UserProfile } from '@/lib/auth';

export default function Navbar() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const router = useRouter();

  useEffect(() => {
    const u = getAuthUser();
    setUser(u);
  }, []);

  const handleLogout = () => {
    clearAuthSession();
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Department info */}
          <div className="flex items-center space-x-3">
            <div className="bg-emerald-500/10 border border-emerald-500/30 p-2 rounded-xl text-emerald-400">
              <GraduationCap className="w-6 h-6" />
            </div>
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

          {/* HOD Profile & Logout */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-slate-800/80 border border-slate-700 px-3 py-1.5 rounded-lg">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <div className="text-left">
                <p className="text-xs font-semibold text-slate-200">
                  {user?.username || 'hod.csm'}
                </p>
                <p className="text-[10px] text-emerald-400 font-mono font-medium">
                  HOD • CSM
                </p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center space-x-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
