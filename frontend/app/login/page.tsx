'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, User, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';
import CSMLogo from '@/components/CSMLogo';
import api from '@/lib/api';
import { setAuthSession } from '@/lib/auth';

export default function LoginPage() {
  const [username, setUsername] = useState('hod.csm');
  const [password, setPassword] = useState('hod_csm_secure_2026');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.post('/api/auth/login', {
        username,
        password,
      });

      const { access_token } = res.data;
      
      const meRes = await api.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` },
      });

      setAuthSession(access_token, meRes.data);
      router.push('/dashboard');
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to connect to authentication server. Ensure backend is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-4 flex items-center justify-center">
      <div className="bg-white rounded-3xl sm:rounded-4xl shadow-sm border border-slate-100 p-8 sm:p-10 max-w-md w-full animate-fade-in relative overflow-hidden">
        {/* Top Brand Logo */}
        <div className="flex flex-col items-center text-center mb-7">
          <CSMLogo size="xl" className="mb-3" />
          
          <h1 className="font-black text-3xl text-slate-900 tracking-tight">
            CSM
          </h1>

          <p className="text-xs text-slate-500 font-medium mt-1">
            Academic Risk & Performance Intelligence System
          </p>

          <div className="mt-3.5 inline-flex items-center gap-1.5 bg-[#d9f99d] px-3.5 py-1.5 rounded-full text-xs font-bold text-slate-900 shadow-xs">
            <ShieldCheck className="w-4 h-4 text-slate-900" />
            <span>HOD: Professor M A JABBAR</span>
          </div>
        </div>

        {/* Login Form */}
        <form className="space-y-4" onSubmit={handleLogin}>
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-2xl flex items-start space-x-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5 pl-1">
              HOD Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <User className="w-4 h-4" />
              </div>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="hod.csm"
                className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200/80 rounded-2xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-slate-400 transition-all font-medium"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1.5 pl-1">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Lock className="w-4 h-4" />
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200/80 rounded-2xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-slate-400 transition-all font-medium"
              />
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-3.5 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-2xl text-xs font-bold transition-all shadow-md hover:shadow-lg disabled:opacity-50 cursor-pointer"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In as CSM HOD'}</span>
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-100 text-center">
          <p className="text-[11px] text-slate-400 font-medium">
            Single Authentication Guard • <span className="font-mono text-slate-600 font-bold">JWT / Bcrypt</span>
          </p>
        </div>
      </div>
    </div>
  );
}
