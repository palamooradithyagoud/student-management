'use client';

import React from 'react';
import Sidebar from '@/components/Sidebar';

interface AppShellProps {
  children: React.ReactNode;
  onSearch?: (query: string) => void;
}

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen w-full flex flex-col md:flex-row bg-white text-slate-900">
      {/* Full-height Left Sidebar */}
      <Sidebar />

      {/* Full-screen Main Content Area */}
      <main className="flex-1 min-h-screen p-6 lg:p-8 flex flex-col overflow-y-auto bg-white" suppressHydrationWarning>
        <div className="max-w-7xl w-full mx-auto flex-1 flex flex-col">
          <div className="flex-1">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
