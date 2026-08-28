'use client';

import React from 'react';

interface CSMLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export default function CSMLogo({ size = 'md', className = '' }: CSMLogoProps) {
  const sizeMap = {
    sm: 'w-7 h-7',
    md: 'w-10 h-10',
    lg: 'w-14 h-14',
    xl: 'w-16 h-16'
  };

  const currentSize = sizeMap[size] || sizeMap.md;

  return (
    <div className={`relative flex items-center justify-center shrink-0 select-none ${currentSize} ${className}`}>
      <svg
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full drop-shadow-sm"
      >
        <defs>
          <linearGradient id="csm-bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0f172a" />
            <stop offset="60%" stopColor="#064e3b" />
            <stop offset="100%" stopColor="#047857" />
          </linearGradient>

          <linearGradient id="csm-accent-glow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="100%" stopColor="#a7f3d0" />
          </linearGradient>

          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Shield / Rounded Base with Subtle Border */}
        <rect
          x="2"
          y="2"
          width="60"
          height="60"
          rx="18"
          fill="url(#csm-bg-gradient)"
          stroke="#10b981"
          strokeWidth="1.5"
          strokeOpacity="0.4"
        />

        {/* AI Circuit / Neural Interconnect lines in background */}
        <path
          d="M16 22H24M24 22L32 30M32 30V44M40 22H48M32 30L40 22"
          stroke="#10b981"
          strokeWidth="1.5"
          strokeOpacity="0.3"
          strokeLinecap="round"
        />

        {/* Central Geometric Node */}
        <circle cx="32" cy="30" r="3.5" fill="#34d399" filter="url(#glow)" />
        <circle cx="16" cy="22" r="2" fill="#6ee7b7" />
        <circle cx="48" cy="22" r="2" fill="#6ee7b7" />
        <circle cx="32" cy="44" r="2" fill="#6ee7b7" />

        {/* Bold Modern "CSM" Monogram */}
        <text
          x="32"
          y="48"
          textAnchor="middle"
          fill="url(#csm-accent-glow)"
          fontFamily="system-ui, -apple-system, sans-serif"
          fontWeight="900"
          fontSize="14"
          letterSpacing="1.5"
        >
          CSM
        </text>
      </svg>
    </div>
  );
}
