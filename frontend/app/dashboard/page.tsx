'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';
import { 
  Calendar as CalendarIcon, 
  ChevronRight,
  TrendingUp,
  RefreshCw,
  Sparkles,
  Award,
  Trophy,
  Medal,
  ExternalLink
} from 'lucide-react';

const cardColorMap: Record<string, { bg: string; border: string; bar: string; badge: string; text: string }> = {
  peach: {
    bg: 'bg-[#ffedd5]',
    border: 'border-[#fed7aa]',
    bar: 'bg-[#ea580c]',
    badge: 'text-[#c2410c]',
    text: 'text-[#9a3412]'
  },
  purple: {
    bg: 'bg-[#f3e8ff]',
    border: 'border-[#e9d5ff]',
    bar: 'bg-[#9333ea]',
    badge: 'text-[#7e22ce]',
    text: 'text-[#6b21a8]'
  },
  rose: {
    bg: 'bg-[#ffe4e6]',
    border: 'border-[#fecdd3]',
    bar: 'bg-[#e11d48]',
    badge: 'text-[#be123c]',
    text: 'text-[#9f1239]'
  },
  lime: {
    bg: 'bg-[#ecfccb]',
    border: 'border-[#d9f99d]',
    bar: 'bg-[#65a30d]',
    badge: 'text-[#4d7c0f]',
    text: 'text-[#3f6212]'
  },
  sky: {
    bg: 'bg-[#e0f2fe]',
    border: 'border-[#bae6fd]',
    bar: 'bg-[#0284c7]',
    badge: 'text-[#0369a1]',
    text: 'text-[#075985]'
  }
};

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<string>('All');
  const [topperSectionFilter, setTopperSectionFilter] = useState<string>('ALL');
  const [passMetric, setPassMetric] = useState<'all_clear' | 'exam_pass'>('all_clear');
  const router = useRouter();

  const fetchDashboardData = async () => {
    try {
      const res = await api.get('/api/dashboard/overview');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const rawSubjectCards = data?.subject_cards || [];

  const availableSemesters = React.useMemo(() => {
    const sems = Array.from(new Set(rawSubjectCards.map((c: any) => c.semester))).filter(Boolean).sort((a: any, b: any) => a - b);
    return sems.length > 0 ? sems : [1, 2];
  }, [rawSubjectCards]);

  const subjectCards = activeFilter === 'All'
    ? rawSubjectCards
    : rawSubjectCards.filter((c: any) => activeFilter === `Sem ${c.semester}`);

  // Section-Wise Pass / All-Clear Percentage Bars
  const sectionBars = data?.section_pass_rates || [];

  const maxMetricVal = sectionBars.length > 0
    ? Math.max(...sectionBars.map((b: any) => passMetric === 'all_clear' ? (b.student_pass_rate ?? b.pass_rate) : b.pass_rate))
    : 100;

  const avgDeptRate = sectionBars.length > 0
    ? (
        sectionBars.reduce(
          (acc: number, b: any) => acc + (passMetric === 'all_clear' ? (b.student_pass_rate ?? b.pass_rate) : b.pass_rate),
          0
        ) / sectionBars.length
      ).toFixed(1)
    : '0.0';

  // Academic Toppers
  const toppers = data?.toppers || [];

  const filteredToppers = topperSectionFilter === 'ALL'
    ? toppers
    : toppers.filter((t: any) => t.section === topperSectionFilter);

  return (
    <AppShell>
      <div className="space-y-6 animate-fade-in">
        {/* Main Heading */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Courses & Academic Performance
            </h1>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              CSM Department (AI & ML) • Head of Department: <span className="font-bold text-slate-800">Prof. M A JABBAR</span>
            </p>
          </div>

          <button
            onClick={fetchDashboardData}
            className="p-2 text-slate-400 hover:text-slate-900 rounded-full transition-colors cursor-pointer"
            title="Refresh Live Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Section Header: "Most Failed Subjects" + Filter Tabs */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center flex-wrap gap-3">
              <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <span>Most Failed Subjects</span>
                <span className="text-[11px] font-bold text-rose-700 bg-rose-50 border border-rose-200/80 px-2.5 py-0.5 rounded-full">
                  High Risk
                </span>
              </h2>

              {/* Filter Pills */}
              <div className="flex items-center space-x-1 text-xs font-semibold text-slate-500 bg-slate-100/80 p-1 rounded-full shadow-2xs flex-wrap">
                <button
                  onClick={() => setActiveFilter('All')}
                  className={`transition-all duration-200 ease-out cursor-pointer ${
                    activeFilter === 'All'
                      ? 'bg-slate-900 text-white px-3 py-1 rounded-full font-bold shadow-xs scale-100'
                      : 'text-slate-500 hover:text-slate-900 px-2.5 py-1 hover:bg-slate-200/60 rounded-full'
                  }`}
                >
                  All
                </button>
                {availableSemesters.map((semNum: any) => {
                  const filterLabel = `Sem ${semNum}`;
                  return (
                    <button
                      key={semNum}
                      onClick={() => setActiveFilter(filterLabel)}
                      className={`transition-all duration-200 ease-out cursor-pointer ${
                        activeFilter === filterLabel
                          ? 'bg-slate-900 text-white px-3 py-1 rounded-full font-bold shadow-xs scale-100'
                          : 'text-slate-500 hover:text-slate-900 px-2.5 py-1 hover:bg-slate-200/60 rounded-full'
                      }`}
                    >
                      {filterLabel}
                    </button>
                  );
                })}
              </div>
            </div>

            <a
              href="/subjects"
              className="text-xs font-bold text-slate-900 hover:text-slate-600 transition-colors self-end sm:self-auto hover:translate-x-0.5 duration-200 inline-flex items-center space-x-1"
            >
              <span>View all subjects</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </a>
          </div>

          {/* Pastel Cards Grid (Rendering LIVE Backend Data or Empty State) */}
          {subjectCards.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {subjectCards.map((card: any) => {
                const theme = cardColorMap[card.theme || 'peach'] || cardColorMap.peach;
                const passRate = card.pass_percentage ?? card.pass_rate ?? 0;
                return (
                  <div
                    key={card.subject_code}
                    className={`${theme.bg} border ${theme.border} rounded-3xl p-5 shadow-xs hover:shadow-lg hover:-translate-y-1.5 transition-all duration-300 ease-out flex flex-col justify-between group cursor-default min-h-[190px]`}
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-black px-2.5 py-0.5 rounded-full bg-white/90 shadow-2xs text-slate-900 border border-black/5 group-hover:scale-105 transition-transform duration-250">
                          {card.subject_code}
                        </span>
                        <div className="inline-flex items-center space-x-1 text-[10px] font-bold text-slate-700 bg-white/70 backdrop-blur-xs px-2 py-0.5 rounded-full shadow-2xs">
                          <CalendarIcon className="w-2.5 h-2.5 text-slate-500" />
                          <span>Sem {card.semester}</span>
                        </div>
                      </div>

                      <h3 className="text-sm font-extrabold text-slate-900 mt-2.5 leading-snug truncate group-hover:text-slate-950 transition-colors" title={card.subject_name}>
                        {card.subject_name}
                      </h3>

                      {/* Metric Pills: Pass / Fail / Pass % */}
                      <div className="grid grid-cols-3 gap-1.5 mt-3">
                        <div className="bg-white/85 backdrop-blur-xs rounded-xl p-1.5 text-center border border-emerald-200/60 shadow-2xs hover:shadow-xs hover:-translate-y-0.5 transition-all duration-200">
                          <div className="text-[9px] font-bold text-emerald-700 uppercase">Pass</div>
                          <div className="text-xs font-black text-slate-900 font-mono">{card.total_pass ?? 0}</div>
                        </div>
                        <div className="bg-white/85 backdrop-blur-xs rounded-xl p-1.5 text-center border border-rose-200/60 shadow-2xs hover:shadow-xs hover:-translate-y-0.5 transition-all duration-200">
                          <div className="text-[9px] font-bold text-rose-700 uppercase">Fail</div>
                          <div className="text-xs font-black text-slate-900 font-mono">{card.total_fail ?? 0}</div>
                        </div>
                        <div className="bg-white/85 backdrop-blur-xs rounded-xl p-1.5 text-center border border-slate-200/60 shadow-2xs hover:shadow-xs hover:-translate-y-0.5 transition-all duration-200">
                          <div className="text-[9px] font-bold text-slate-600 uppercase">Pass %</div>
                          <div className="text-xs font-black text-slate-900 font-mono">{passRate}%</div>
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 pt-2 border-t border-black/5">
                      <div className="flex items-center justify-between text-[10px] font-bold text-slate-700 mb-1">
                        <span>{card.student_count} Candidates</span>
                        <span>{Math.round(card.average_attendance || 0)}% Attn</span>
                      </div>
                      <div className="w-full bg-white/90 h-1.5 rounded-full overflow-hidden border border-black/5">
                        <div
                          className={`${theme.bar} h-full rounded-full transition-all duration-700 ease-out`}
                          style={{ width: `${Math.min(100, passRate)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-slate-50 border border-slate-200/80 rounded-3xl p-8 text-center">
              <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-3 text-slate-400">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-800">No Course Performance Data Available</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                No examination results or student marks have been uploaded yet. Upload semester results in Data Ingestion to analyze high-risk failure subjects.
              </p>
              <a
                href="/data"
                className="inline-flex items-center space-x-1.5 mt-4 px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <span>Upload Datasets in Data Ingestion</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </a>
            </div>
          )}
        </div>

        {/* Bottom 2-Column Section: Section-Wise Pass Percentage + Top 5 Academic Toppers */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
          {/* Left Column: Section-Wise All-Clear / Pass Percentage */}
          <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-100 p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    {passMetric === 'all_clear' ? 'Section-Wise All-Clear Rate (0 Backlogs)' : 'Section-Wise Pass Percentage'}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {passMetric === 'all_clear'
                      ? 'Students with 0 Backlogs across Sections'
                      : 'Examination Pass Rates across Sections'}
                  </p>
                </div>
                
                {/* Metric Toggle: All-Clear (0 Backlogs) vs Exam Pass Rate */}
                <div className="flex items-center space-x-1 bg-slate-100/90 p-1 rounded-full text-xs font-semibold self-start sm:self-auto shadow-2xs">
                  <button
                    type="button"
                    onClick={() => setPassMetric('all_clear')}
                    className={`px-3 py-1 rounded-full transition-all cursor-pointer text-xs ${
                      passMetric === 'all_clear'
                        ? 'bg-slate-900 text-white font-bold shadow-xs'
                        : 'text-slate-500 hover:text-slate-900 font-medium'
                    }`}
                  >
                    All-Clear (0 Backlogs)
                  </button>
                  <button
                    type="button"
                    onClick={() => setPassMetric('exam_pass')}
                    className={`px-3 py-1 rounded-full transition-all cursor-pointer text-xs ${
                      passMetric === 'exam_pass'
                        ? 'bg-slate-900 text-white font-bold shadow-xs'
                        : 'text-slate-500 hover:text-slate-900 font-medium'
                    }`}
                  >
                    Exam Pass Rate
                  </button>
                </div>
              </div>

              <div className="flex items-center space-x-2 mt-3">
                <span className="text-2xl font-extrabold text-slate-900">
                  {sectionBars.length} Section{sectionBars.length === 1 ? '' : 's'} Tracked
                </span>
                <span className="bg-[#ecfdf5] text-[#10b981] text-xs font-bold px-2.5 py-0.5 rounded-full ml-auto">
                  {avgDeptRate}% {passMetric === 'all_clear' ? 'Avg Dept All-Clear Rate' : 'Avg Dept Pass Rate'}
                </span>
              </div>

              {/* Bar Chart (Rendering LIVE Section-Wise Bars or Empty State) */}
              {sectionBars.length > 0 ? (
                <div className="mt-7">
                  <div className="h-44 flex items-end justify-between gap-4 px-2 border-b border-slate-100 pb-3 relative">
                    {/* Left Y-axis labels */}
                    <div className="absolute -left-2 top-0 bottom-3 flex flex-col justify-between text-[10px] text-slate-400 font-mono pointer-events-none">
                      <span>100%</span>
                      <span>80%</span>
                      <span>60%</span>
                      <span>40%</span>
                      <span>20%</span>
                      <span>0%</span>
                    </div>

                    {/* Spacer for y-axis */}
                    <div className="w-6 shrink-0" />

                    {sectionBars.map((bar: any) => {
                      const currentVal = passMetric === 'all_clear' ? (bar.student_pass_rate ?? bar.pass_rate) : bar.pass_rate;
                      const isTop = currentVal === maxMetricVal;

                      return (
                        <div key={bar.short_label} className="flex-1 flex flex-col items-center h-full group relative">
                          {/* 100% Height Track with colored fill */}
                          <div className="w-full max-w-[44px] h-full bg-slate-100/80 rounded-2xl flex flex-col justify-end p-1 relative border border-slate-200/50 group-hover:border-slate-300 transition-colors shadow-2xs">
                            <div
                              className={`w-full rounded-xl transition-all duration-700 ease-out relative ${
                                passMetric === 'all_clear'
                                  ? isTop
                                    ? 'bg-gradient-to-t from-emerald-600 to-emerald-400 shadow-xs'
                                    : 'bg-gradient-to-t from-teal-500 to-emerald-400 shadow-2xs'
                                  : isTop
                                    ? 'bg-gradient-to-t from-indigo-600 to-indigo-400 shadow-xs'
                                    : 'bg-gradient-to-t from-sky-500 to-indigo-400 shadow-2xs'
                              }`}
                              style={{ height: `${Math.min(100, Math.max(8, currentVal))}%` }}
                            >
                              <div className="w-full h-1 bg-white/40 rounded-t-xl" />
                            </div>

                            {/* Hover Tooltip */}
                            <div className="absolute -top-11 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 bg-slate-900 text-white text-[9px] py-1.5 px-2.5 rounded-lg pointer-events-none transition-opacity whitespace-nowrap z-30 font-bold shadow-xl text-center">
                              <div>{bar.label}: {currentVal}% {passMetric === 'all_clear' ? '(0 Backlogs)' : ''}</div>
                              <div className="text-[8px] text-slate-300 font-normal mt-0.5">
                                {passMetric === 'all_clear'
                                  ? `Exam Pass Rate: ${bar.pass_rate}% • ${bar.student_count} Students`
                                  : `All-Clear: ${bar.student_pass_rate ?? '—'}% • ${bar.student_count} Students`}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Section Labels underneath bars */}
                  <div className="flex justify-between text-[10px] font-bold text-slate-500 mt-2.5 px-2 pl-8">
                    {sectionBars.map((bar: any) => {
                      const currentVal = passMetric === 'all_clear' ? (bar.student_pass_rate ?? bar.pass_rate) : bar.pass_rate;
                      const isHighlighted = currentVal === maxMetricVal;

                      return (
                        <div
                          key={bar.short_label}
                          className={`flex-1 text-center font-mono ${
                            isHighlighted ? 'text-slate-900 font-extrabold text-[11px]' : ''
                          }`}
                        >
                          <span className="block">{bar.short_label}</span>
                          <span className={`text-[10px] font-bold font-mono ${
                            passMetric === 'all_clear' ? 'text-emerald-700' : 'text-slate-500'
                          }`}>
                            {currentVal}%
                          </span>
                          {passMetric === 'all_clear' && (
                            <span className="text-[8px] text-slate-400 font-sans block font-normal -mt-0.5">
                              0 backlog
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center text-slate-400 text-xs">
                  No section performance data available yet. Ingest semester results to view section breakdown.
                </div>
              )}
            </div>

            {/* Bottom 4 Summary Metrics (LIVE Real Dataset Metrics from DB) */}
            <div className="grid grid-cols-4 gap-2 pt-6 mt-6 border-t border-slate-100 text-left">
              <div>
                <p className="text-[10px] text-slate-400 font-medium">Total Students</p>
                <p className="text-xl font-bold text-slate-900 mt-0.5">
                  {data?.overview?.total_students ?? 0}
                </p>
                <p className="text-[9px] text-slate-400 font-medium">CSM Dept</p>
              </div>

              <div>
                <p className="text-[10px] text-slate-400 font-medium">Sem 1 Count</p>
                <p className="text-xl font-bold text-slate-900 mt-0.5">
                  {data?.overview?.sem1_students ?? 0}
                </p>
                <p className="text-[9px] text-slate-400 font-medium">
                  {data?.overview?.sem1_students ? `${data.overview.sem1_students} Enrolled` : 'No data'}
                </p>
              </div>

              <div>
                <p className="text-[10px] text-slate-400 font-medium">Sem 2 Count</p>
                <p className="text-xl font-bold text-slate-900 mt-0.5">
                  {data?.overview?.sem2_students ?? 0}
                </p>
                <p className="text-[9px] text-slate-400 font-medium">
                  {data?.overview?.sem2_students ? `${data.overview.sem2_students} Active` : 'No data'}
                </p>
              </div>

              <div>
                <p className="text-[10px] text-slate-400 font-medium">Mapping Rate</p>
                <p className="text-xl font-bold text-emerald-600 mt-0.5">
                  {data?.overview?.mapping_success_rate ?? 0}%
                </p>
                <p className="text-[9px] text-emerald-600 font-medium">
                  {data?.overview?.mapping_success_rate ? `${data.overview.mapping_success_rate}% Matched` : 'No data'}
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Top 5 Academic Toppers across Overall CSM */}
          <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-100 p-6 shadow-sm flex flex-col justify-between">
            <div>
              {/* Header */}
              <div className="flex items-center justify-between pb-3">
                <div className="flex items-center space-x-2">
                  <div className="w-7 h-7 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
                    <Trophy className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Academic Toppers
                    </h3>
                    <p className="text-[10px] text-slate-500 font-medium">
                      Top Students • Overall CSM Department
                    </p>
                  </div>
                </div>

                <a
                  href="/students"
                  className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors flex items-center space-x-1"
                >
                  <span>All students</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </a>
              </div>

              {/* Section Filter Pills */}
              <div className="flex items-center space-x-1.5 py-3 border-y border-slate-100 text-xs">
                {[
                  { label: 'Overall CSM', val: 'ALL' },
                  { label: 'Sec A', val: 'A' },
                  { label: 'Sec B', val: 'B' },
                  { label: 'Sec C', val: 'C' },
                ].map((sec) => (
                  <button
                    key={sec.val}
                    onClick={() => setTopperSectionFilter(sec.val)}
                    className={`px-3 py-1 rounded-full text-[11px] font-bold transition-all cursor-pointer ${
                      topperSectionFilter === sec.val
                        ? 'bg-slate-900 text-white shadow-xs'
                        : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
                    }`}
                  >
                    {sec.label}
                  </button>
                ))}
              </div>

              {/* Top Toppers List */}
              <div className="space-y-3 mt-4">
                {filteredToppers.length > 0 ? (
                  filteredToppers.map((top: any) => {
                    const rankColors: Record<number, { bg: string; text: string; badge: string }> = {
                      1: { bg: 'bg-amber-100 border-amber-300 text-amber-900', text: 'text-amber-800', badge: 'bg-amber-400 text-slate-950 font-black' },
                      2: { bg: 'bg-slate-200 border-slate-300 text-slate-800', text: 'text-slate-700', badge: 'bg-slate-300 text-slate-900 font-black' },
                      3: { bg: 'bg-amber-50 border-amber-200 text-amber-800', text: 'text-amber-700', badge: 'bg-amber-200 text-amber-950 font-bold' },
                      4: { bg: 'bg-purple-100 border-purple-200 text-purple-800', text: 'text-purple-700', badge: 'bg-purple-200 text-purple-900 font-bold' },
                      5: { bg: 'bg-emerald-100 border-emerald-200 text-emerald-800', text: 'text-emerald-700', badge: 'bg-emerald-200 text-emerald-900 font-bold' },
                    };
                    const styling = rankColors[top.rank] || rankColors[4];

                    return (
                      <a
                        key={top.roll_no}
                        href={`/students?search=${top.roll_no}`}
                        className="flex items-center justify-between p-2.5 rounded-2xl border border-slate-100 hover:border-slate-300 hover:shadow-xs bg-white hover:bg-slate-50/80 transition-all group cursor-pointer"
                      >
                        {/* Left: Rank Badge + Student Name & Roll */}
                        <div className="flex items-center space-x-3 min-w-0 pr-2">
                          <div className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs border ${styling.bg}`}>
                            <span className="font-extrabold">#{top.rank}</span>
                          </div>

                          <div className="min-w-0">
                            <p className="text-xs font-bold text-slate-900 group-hover:text-indigo-600 transition-colors truncate">
                              {top.student_name}
                            </p>
                            <div className="flex items-center space-x-2 mt-0.5 text-[10px]">
                              <span className="font-mono text-slate-500 font-semibold">{top.roll_no}</span>
                              <span>•</span>
                              <span className={`px-1.5 py-0.2 rounded font-bold ${
                                top.section === 'A' ? 'bg-indigo-50 text-indigo-700' : (top.section === 'B' ? 'bg-purple-50 text-purple-700' : 'bg-emerald-50 text-emerald-700')
                              }`}>
                                Sec {top.section}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Right: CGPA Score Badge */}
                        <div className="text-right shrink-0">
                          <div className="inline-flex items-center space-x-1 bg-[#d9f99d] px-2 py-0.5 rounded-lg text-slate-950 font-extrabold text-xs shadow-2xs">
                            <span>{top.cgpa}</span>
                            <span className="text-[9px] font-semibold text-slate-700">CGPA</span>
                          </div>
                          <div className="text-[9px] text-slate-400 mt-0.5 font-medium">
                            {top.attendance}% Attn
                          </div>
                        </div>
                      </a>
                    );
                  })
                ) : (
                  <div className="py-8 text-center text-slate-400 text-xs">
                    No academic toppers available yet. Upload student results to view leaderboard.
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Footer Note */}
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
              <span>Cumulative Performance across Semesters</span>
              <span className="font-bold text-slate-700">
                Max CGPA: {toppers.length > 0 ? toppers[0].cgpa : '—'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
