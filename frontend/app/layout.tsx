import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'CSM Academic Risk & Performance Intelligence System',
  description: 'AI-Based Academic Risk & Performance Intelligence Platform for HOD of CSM Department',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
