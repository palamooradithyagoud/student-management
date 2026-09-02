'use client';

import React, { useState, useEffect, useMemo } from 'react';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';
import {
  BookOpen,
  ArrowRightLeft,
  Search,
  CheckCircle2,
  XCircle,
  Percent,
  Users,
  RefreshCw,
  X,
  AlertTriangle,
  GraduationCap,
  Copy,
  Check,
  Download,
  ExternalLink,
} from 'lucide-react';

interface FailedStudent {
  roll_no: string;
  student_name: string;
  section: string;
  grade: string;
  marks: number | null;
  grade_points: number | null;
  attendance_percentage: number | null;
}

interface FailedStudentsData {
  subject_code: string;
  semester: number;
  total: number;
  failed_students: FailedStudent[];
}

const CARD_THEMES = [
  {
    bg: 'bg-[#ffedd5]',
    border: 'border-[#fed7aa]',
    codeBg: 'bg-[#ffedd5] text-[#c2410c] border-[#fdba74]',
    bar: 'bg-[#ea580c]',
  },
  {
    bg: 'bg-[#f3e8ff]',
    border: 'border-[#e9d5ff]',
    codeBg: 'bg-[#f3e8ff] text-[#7e22ce] border-[#d8b4fe]',
    bar: 'bg-[#9333ea]',
  },
  {
    bg: 'bg-[#ecfccb]',
    border: 'border-[#d9f99d]',
    codeBg: 'bg-[#ecfccb] text-[#4d7c0f] border-[#bef264]',
    bar: 'bg-[#65a30d]',
  },
  {
    bg: 'bg-[#e0f2fe]',
    border: 'border-[#bae6fd]',
    codeBg: 'bg-[#e0f2fe] text-[#0369a1] border-[#7dd3fc]',
    bar: 'bg-[#0284c7]',
  },
];

// ─────────────────────────────────────────────
// Failed Students Modal
// ─────────────────────────────────────────────
function FailedStudentsModal({
  subject,
  onClose,
}: {
  subject: { subject_code: string; subject_name: string; semester: number };
  onClose: () => void;
}) {
  const [data, setData] = useState<FailedStudentsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');
  const [copiedRolls, setCopiedRolls] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    let isMounted = true;
    const fetchFailed = async () => {
      setLoading(true);
      try {
        const res = await api.get(
          `/api/subjects/${encodeURIComponent(subject.subject_code)}/failed-students?semester=${subject.semester}`
        );
        if (isMounted) {
          setData(res.data);
        }
      } catch (err) {
        console.error('Failed to fetch failed students:', err);
        if (isMounted) {
          setData({ subject_code: subject.subject_code, semester: subject.semester, failed_students: [], total: 0 });
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    fetchFailed();
    return () => {
      isMounted = false;
    };
  }, [subject]);

  const students: FailedStudent[] = useMemo(() => data?.failed_students || [], [data]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return students.filter((s) => {
      const matchSearch =
        !q ||
        (s.student_name && s.student_name.toLowerCase().includes(q)) ||
        (s.roll_no && s.roll_no.toLowerCase().includes(q));
      const matchSec = !sectionFilter || s.section === sectionFilter;
      return matchSearch && matchSec;
    });
  }, [students, search, sectionFilter]);

  const sections = useMemo(() => {
    const set = new Set<string>();
    students.forEach((s) => {
      if (s.section) set.add(s.section);
    });
    return Array.from(set).sort();
  }, [students]);

  const lowAttnCount = useMemo(() => {
    return students.filter((s) => s.attendance_percentage !== null && s.attendance_percentage < 75).length;
  }, [students]);

  const handleCopyRolls = () => {
    const rolls = filtered.map((s) => s.roll_no).join(', ');
    if (navigator.clipboard) {
      navigator.clipboard.writeText(rolls);
      setCopiedRolls(true);
      setTimeout(() => setCopiedRolls(false), 2000);
    }
  };

  const handleDownloadCsv = () => {
    if (filtered.length === 0) return;
    const headers = ['Roll Number', 'Student Name', 'Section', 'Subject Code', 'Subject Name', 'Semester', 'Grade', 'Marks', 'Attendance %'];
    const rows = filtered.map((s) => [
      `"${s.roll_no}"`,
      `"${s.student_name || ''}"`,
      `"${s.section || ''}"`,
      `"${subject.subject_code}"`,
      `"${subject.subject_name}"`,
      subject.semester,
      `"${s.grade || 'F'}"`,
      s.marks !== null ? s.marks : '',
      s.attendance_percentage !== null ? s.attendance_percentage : '',
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `failed_students_${subject.subject_code}_sem${subject.semester}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  function attnColor(v: number | null | undefined) {
    if (v === null || v === undefined) return 'text-slate-400';
    if (v >= 75) return 'text-emerald-600';
    return 'text-rose-600 font-bold';
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-fade-in"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-100 w-full max-w-3xl max-h-[92vh] overflow-hidden flex flex-col animate-scale-in">
        {/* Modal Header */}
        <div className="flex items-start justify-between px-6 pt-5 pb-4 border-b border-slate-100 shrink-0 bg-slate-50/50">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="inline-flex items-center gap-1.5 bg-rose-100 text-rose-700 border border-rose-200 px-3 py-0.5 rounded-full text-[11px] font-black uppercase tracking-wider shadow-2xs">
                <XCircle className="w-3.5 h-3.5 text-rose-600" />
                Failed Students Roster
              </span>
              <span className="text-[11px] font-bold text-slate-700 bg-white border border-slate-200 px-2.5 py-0.5 rounded-full">
                Semester {subject.semester}
              </span>
              <span className="text-[11px] font-mono font-bold text-indigo-700 bg-indigo-50 border border-indigo-100 px-2.5 py-0.5 rounded-full">
                {subject.subject_code}
              </span>
            </div>
            <h2 className="text-lg font-extrabold text-slate-900 leading-tight">
              {subject.subject_name}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            {!loading && data && (
              <span className="text-xs font-black text-rose-700 bg-rose-50 border border-rose-200 px-3 py-1 rounded-full shadow-2xs">
                {data.total} {data.total === 1 ? 'student' : 'students'} failed
              </span>
            )}
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-900 rounded-full hover:bg-slate-200/70 transition-all cursor-pointer active:scale-95"
              title="Close modal (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filter and Action Bar */}
        {!loading && students.length > 0 && (
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5 px-6 py-3 border-b border-slate-100 bg-slate-50/80 shrink-0">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              {/* Search Bar */}
              <div className="relative flex-1 min-w-[180px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search student name or roll number..."
                  className="w-full pl-8 pr-8 py-1.5 bg-white border border-slate-200 rounded-full text-xs font-medium text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-900/5 transition-all shadow-2xs"
                />
                {search && (
                  <button
                    onClick={() => setSearch('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>

              {/* Section Filter Pills */}
              {sections.length > 1 && (
                <div className="flex items-center gap-1 bg-white border border-slate-200 p-0.5 rounded-full text-xs font-semibold shrink-0 shadow-2xs">
                  <button
                    onClick={() => setSectionFilter('')}
                    className={`px-3 py-1 rounded-full transition-all cursor-pointer text-xs ${
                      !sectionFilter
                        ? 'bg-slate-900 text-white font-bold shadow-xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    All
                  </button>
                  {sections.map((sec) => (
                    <button
                      key={sec}
                      onClick={() => setSectionFilter(sec === sectionFilter ? '' : sec)}
                      className={`px-2.5 py-1 rounded-full transition-all cursor-pointer text-xs ${
                        sectionFilter === sec
                          ? 'bg-slate-900 text-white font-bold shadow-xs'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                      }`}
                    >
                      Sec {sec}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Action Buttons: Copy & Export CSV */}
            <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
              <button
                onClick={handleCopyRolls}
                disabled={filtered.length === 0}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-full text-xs font-bold transition-all shadow-2xs cursor-pointer active:scale-95 disabled:opacity-50"
                title="Copy all filtered roll numbers"
              >
                {copiedRolls ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-700">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-slate-500" />
                    <span>Copy Roll Nos</span>
                  </>
                )}
              </button>

              <button
                onClick={handleDownloadCsv}
                disabled={filtered.length === 0}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-full text-xs font-bold transition-all shadow-2xs cursor-pointer active:scale-95 disabled:opacity-50"
                title="Export failed students list to CSV"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export CSV</span>
              </button>
            </div>
          </div>
        )}

        {/* Modal Body */}
        <div className="overflow-y-auto flex-1 bg-slate-50/30">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-400 text-xs">
              <RefreshCw className="w-6 h-6 animate-spin text-slate-600" />
              <span className="font-semibold text-slate-600">Loading student exam records...</span>
            </div>
          ) : students.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-400 text-center px-4">
              <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shadow-inner">
                <GraduationCap className="w-7 h-7" />
              </div>
              <p className="text-base font-extrabold text-slate-800">No Failures Recorded!</p>
              <p className="text-xs text-slate-500 max-w-sm">
                Every candidate enrolled in this course has successfully cleared the examination for Semester {subject.semester}.
              </p>
            </div>
          ) : (
            <div className="p-5">
              {/* Meta & Stats Pill Banner */}
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3.5 text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-slate-600 font-medium">
                    Showing <strong className="text-slate-900">{filtered.length}</strong> of{' '}
                    <strong className="text-rose-700">{students.length}</strong> failed students
                  </span>
                  {lowAttnCount > 0 && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
                      <AlertTriangle className="w-3 h-3 text-amber-600" />
                      {lowAttnCount} with &lt;75% Attendance
                    </span>
                  )}
                </div>

                {sections.length > 0 && (
                  <div className="flex gap-1.5 flex-wrap">
                    {sections.map((sec) => {
                      const count = students.filter((s) => s.section === sec).length;
                      return (
                        <span
                          key={sec}
                          className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700 shadow-2xs"
                        >
                          Section {sec}: <strong className="text-rose-600">{count}</strong>
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Table of Failed Students */}
              <div className="bg-white border border-slate-200/80 rounded-2xl overflow-hidden shadow-xs">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100/80 text-slate-500 font-bold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4 w-10">#</th>
                      <th className="py-3 px-4">Student Details</th>
                      <th className="py-3 px-3 text-center">Section</th>
                      <th className="py-3 px-3 text-center">Grade</th>
                      <th className="py-3 px-3 text-center">Marks</th>
                      <th className="py-3 px-4 text-center">Attendance %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filtered.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-12 text-center text-slate-400">
                          <p className="font-semibold text-slate-600">No students match your query</p>
                          <p className="text-[11px] text-slate-400 mt-1">
                            Try searching with a different name, roll number, or section filter.
                          </p>
                        </td>
                      </tr>
                    ) : (
                      filtered.map((s, idx) => (
                        <tr
                          key={s.roll_no}
                          className="hover:bg-rose-50/40 transition-colors group"
                        >
                          <td className="py-3 px-4 text-slate-400 font-mono font-bold text-[11px]">
                            {idx + 1}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-3">
                              <div
                                className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-black shrink-0 shadow-2xs ${
                                  s.section === 'A'
                                    ? 'bg-indigo-600'
                                    : s.section === 'B'
                                    ? 'bg-purple-600'
                                    : 'bg-teal-600'
                                }`}
                              >
                                {s.student_name ? s.student_name.slice(0, 2).toUpperCase() : 'ST'}
                              </div>
                              <div>
                                <p className="font-extrabold text-slate-900 leading-tight group-hover:text-rose-950 transition-colors">
                                  {s.student_name || '—'}
                                </p>
                                <p className="text-[11px] font-mono font-semibold text-slate-500 mt-0.5">
                                  {s.roll_no}
                                </p>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <span
                              className={`inline-block px-2.5 py-0.5 rounded-md text-[11px] font-bold ${
                                s.section === 'A'
                                  ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                                  : s.section === 'B'
                                  ? 'bg-purple-50 text-purple-700 border border-purple-200'
                                  : 'bg-teal-50 text-teal-700 border border-teal-200'
                              }`}
                            >
                              Sec {s.section || '—'}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg text-xs font-black bg-rose-100 text-rose-800 border border-rose-300 shadow-2xs">
                              {s.grade || 'F'}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-center font-mono font-bold text-slate-800">
                            {s.marks !== null && s.marks !== undefined ? s.marks : '—'}
                          </td>
                          <td className={`py-3 px-4 text-center ${attnColor(s.attendance_percentage)}`}>
                            <div className="inline-flex items-center justify-center gap-1">
                              <span>
                                {s.attendance_percentage !== null && s.attendance_percentage !== undefined
                                  ? `${s.attendance_percentage}%`
                                  : '—'}
                              </span>
                              {s.attendance_percentage !== null &&
                                s.attendance_percentage !== undefined &&
                                s.attendance_percentage < 75 && (
                                  <span title="Attendance below required 75% threshold" className="inline-flex">
                                    <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                                  </span>
                                )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500 shrink-0">
          <span>Click outside or press <kbd className="px-1.5 py-0.5 bg-white border border-slate-300 rounded font-mono text-[10px] text-slate-700 font-bold">Esc</kbd> to exit</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-full font-bold text-xs transition-all cursor-pointer active:scale-95 shadow-2xs"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Main Page Component
// ─────────────────────────────────────────────
export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [mappings, setMappings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [semFilter, setSemFilter] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [failedModal, setFailedModal] = useState<{
    subject_code: string;
    subject_name: string;
    semester: number;
  } | null>(null);

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const res = await api.get('/api/subjects');
        setSubjects(res.data.items || []);
        setMappings(res.data.mappings || []);
      } catch (err) {
        console.error('Failed to load subjects:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSubjects();
  }, []);

  const filteredSubjects = useMemo(() => {
    return subjects.filter((s) => {
      const matchesSem = semFilter === null || s.semester === semFilter;
      const matchesSearch =
        !searchQuery.trim() ||
        s.subject_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.subject_code.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSem && matchesSearch;
    });
  }, [subjects, semFilter, searchQuery]);

  return (
    <AppShell>
      <div className="space-y-7 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-2">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-1.5 bg-[#d9f99d] text-slate-950 rounded-xl font-bold">
                <BookOpen className="w-5 h-5" />
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                Subjects & Academic Performance
              </h1>
            </div>
            <p className="text-xs text-slate-500 mt-1 font-medium">
              Curriculum catalog, examination pass/fail distribution, and deterministic course code resolution.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="relative group">
              <Search className="w-3.5 h-3.5 text-slate-400 group-focus-within:text-slate-900 transition-colors duration-200 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search subject code or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-3 py-1.5 bg-slate-100 hover:bg-slate-150 focus:bg-white text-xs rounded-full border border-slate-200 focus:border-slate-400 focus:ring-2 focus:ring-slate-900/5 focus:outline-none transition-all duration-200 w-full sm:w-60 font-medium placeholder:text-slate-400 shadow-2xs"
              />
            </div>

            <div className="flex items-center space-x-1.5 bg-slate-100/90 p-1 rounded-full text-xs font-semibold self-start sm:self-auto shadow-2xs">
              {[
                { label: 'All Semesters', val: null },
                { label: 'Semester 1', val: 1 },
                { label: 'Semester 2', val: 2 },
              ].map((tab) => (
                <button
                  key={tab.label}
                  onClick={() => setSemFilter(tab.val)}
                  className={`px-3.5 py-1 rounded-full transition-all duration-200 ease-out cursor-pointer ${
                    semFilter === tab.val
                      ? 'bg-slate-900 text-white shadow-xs scale-100 font-bold'
                      : 'text-slate-500 hover:text-slate-900 hover:bg-slate-200/60'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Subjects Cards Grid */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider">
              Course Catalog & Performance Cards ({filteredSubjects.length}{' '}
              {filteredSubjects.length === 1 ? 'Subject' : 'Subjects'})
            </h2>
            <span className="text-xs text-slate-500 font-semibold">
              Tip: Click any <span className="text-rose-600 font-bold bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">Fail</span> block to inspect students who failed
            </span>
          </div>

          {loading ? (
            <div className="py-16 text-center text-slate-400 text-xs">
              <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-slate-900 mb-2"></div>
              <div>Loading subjects and performance data...</div>
            </div>
          ) : filteredSubjects.length === 0 ? (
            <div className="bg-white border border-slate-100 rounded-3xl p-12 text-center text-slate-400 text-xs animate-scale-in">
              No subjects found matching the filter criteria.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredSubjects.map((sub, idx) => {
                const theme = CARD_THEMES[idx % CARD_THEMES.length];
                const passRate =
                  sub.pass_percentage ??
                  (sub.total_students > 0
                    ? Math.round((sub.total_pass / sub.total_students) * 1000) / 10
                    : 0);

                const hasFails = Boolean(sub.total_fail && sub.total_fail > 0);

                return (
                  <div
                    key={sub.subject_id || sub.subject_code}
                    className={`${theme.bg} border ${theme.border} rounded-3xl p-5 shadow-xs hover:shadow-lg hover:-translate-y-1.5 transition-all duration-300 ease-out flex flex-col justify-between group cursor-default`}
                  >
                    <div>
                      {/* Top: Code, Semester & Credits */}
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-black font-mono tracking-wide shadow-xs border ${theme.codeBg} group-hover:scale-105 transition-transform duration-250`}
                        >
                          <span>{sub.subject_code}</span>
                        </span>
                        <div className="flex items-center space-x-1.5">
                          <span className="text-[11px] font-bold text-slate-700 bg-white/80 backdrop-blur-xs px-2.5 py-0.5 rounded-full border border-black/5 shadow-2xs">
                            Sem {sub.semester}
                          </span>
                          <span className="text-[11px] font-bold text-slate-600 bg-white/60 px-2 py-0.5 rounded-full">
                            {sub.credits ? `${sub.credits} Credits` : '4.0 Cr'}
                          </span>
                        </div>
                      </div>

                      {/* Subject Name */}
                      <h3 className="text-base font-extrabold text-slate-900 mt-3.5 leading-snug tracking-tight group-hover:text-slate-950 transition-colors">
                        {sub.subject_name}
                      </h3>

                      {/* Performance Metric Blocks */}
                      <div className="grid grid-cols-3 gap-2 mt-4">
                        {/* PASS */}
                        <div className="bg-white/90 backdrop-blur-xs border border-emerald-200/80 rounded-2xl p-2.5 text-center shadow-2xs hover:shadow-xs hover:-translate-y-0.5 transition-all duration-200">
                          <div className="flex items-center justify-center space-x-1 text-emerald-700 mb-0.5">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span className="text-[10px] font-extrabold uppercase tracking-wider">Pass</span>
                          </div>
                          <p className="text-base font-black text-slate-900 font-mono">{sub.total_pass ?? 0}</p>
                          <p className="text-[9px] font-semibold text-emerald-600">Total Pass</p>
                        </div>

                        {/* FAIL — Clickable button with clear visual cue */}
                        <button
                          type="button"
                          onClick={() =>
                            hasFails &&
                            setFailedModal({
                              subject_code: sub.subject_code,
                              subject_name: sub.subject_name,
                              semester: sub.semester,
                            })
                          }
                          disabled={!hasFails}
                          className={`rounded-2xl p-2.5 text-center transition-all duration-200 select-none ${
                            hasFails
                              ? 'bg-rose-50/90 hover:bg-rose-100/90 border-2 border-rose-300 hover:border-rose-400 shadow-xs hover:shadow-md hover:-translate-y-0.5 cursor-pointer active:scale-95 group/failbtn ring-2 ring-rose-400/20'
                              : 'bg-white/70 border border-slate-200 cursor-default opacity-60'
                          }`}
                          title={hasFails ? `Click to see all ${sub.total_fail} students who failed ${sub.subject_code}` : 'No failures in this course'}
                        >
                          <div className="flex items-center justify-center space-x-1 text-rose-700 mb-0.5">
                            <XCircle className={`w-3.5 h-3.5 ${hasFails ? 'animate-pulse text-rose-600' : ''}`} />
                            <span className="text-[10px] font-black uppercase tracking-wider text-rose-800">
                              Fail
                            </span>
                          </div>
                          <p className="text-base font-black text-rose-900 font-mono">
                            {sub.total_fail ?? 0}
                          </p>
                          <p className={`text-[9px] font-extrabold ${hasFails ? 'text-rose-700 underline underline-offset-2' : 'text-slate-400'}`}>
                            {hasFails ? 'View Who Failed' : 'No Fails'}
                          </p>
                        </button>

                        {/* RATE */}
                        <div className="bg-white/90 backdrop-blur-xs border border-slate-200 rounded-2xl p-2.5 text-center shadow-2xs hover:shadow-xs hover:-translate-y-0.5 transition-all duration-200">
                          <div className="flex items-center justify-center space-x-1 text-slate-700 mb-0.5">
                            <Percent className="w-3.5 h-3.5" />
                            <span className="text-[10px] font-extrabold uppercase tracking-wider">Rate</span>
                          </div>
                          <p className="text-base font-black text-slate-900 font-mono">{passRate}%</p>
                          <p className="text-[9px] font-semibold text-slate-500">Pass %</p>
                        </div>
                      </div>
                    </div>

                    {/* Bottom: Progress bar and action banner */}
                    <div className="mt-4 pt-3 border-t border-black/5 space-y-2">
                      <div className="flex items-center justify-between text-[11px] font-bold text-slate-800">
                        <span className="text-slate-600 font-medium">
                          Total Candidates:{' '}
                          <span className="text-slate-900 font-bold">
                            {sub.total_students || (sub.total_pass || 0) + (sub.total_fail || 0)}
                          </span>
                        </span>
                        <span>
                          {sub.avg_attendance ? `${sub.avg_attendance}% Attn` : `Pass: ${passRate}%`}
                        </span>
                      </div>
                      <div className="w-full bg-white/90 h-2 rounded-full overflow-hidden border border-black/5">
                        <div
                          className={`${theme.bar} h-full rounded-full transition-all duration-700 ease-out`}
                          style={{ width: `${Math.min(100, Math.max(0, passRate))}%` }}
                        />
                      </div>

                      {hasFails && (
                        <button
                          type="button"
                          onClick={() =>
                            setFailedModal({
                              subject_code: sub.subject_code,
                              subject_name: sub.subject_name,
                              semester: sub.semester,
                            })
                          }
                          className="w-full mt-2 py-1.5 px-3 bg-white/90 hover:bg-rose-50 border border-rose-200 hover:border-rose-300 rounded-xl text-[11px] font-extrabold text-rose-700 flex items-center justify-center gap-1.5 transition-all shadow-2xs cursor-pointer active:scale-98"
                        >
                          <XCircle className="w-3.5 h-3.5 text-rose-600" />
                          <span>View {sub.total_fail} Failed Students</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Subject Mappings Table */}
        <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
            <ArrowRightLeft className="w-4 h-4 text-emerald-500" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Deterministic Ingested vs Standard Subject Mappings (subject_mapping.csv)
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-bold">
                  <th className="py-2.5 px-3">Dataset Source</th>
                  <th className="py-2.5 px-3">Original Raw Code</th>
                  <th className="py-2.5 px-3">Original Raw Title</th>
                  <th className="py-2.5 px-3">Standard Course Code</th>
                  <th className="py-2.5 px-3">Standard Course Name</th>
                  <th className="py-2.5 px-3">Resolution Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-[11px] font-mono">
                {mappings.map((m, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 text-slate-500">{m.source_file}</td>
                    <td className="py-2.5 px-3 text-amber-700 font-bold">{m.original_subject_code}</td>
                    <td className="py-2.5 px-3 text-slate-800 font-sans">{m.original_subject_name}</td>
                    <td className="py-2.5 px-3 text-slate-900 font-bold">{m.standard_subject_code}</td>
                    <td className="py-2.5 px-3 text-slate-800 font-sans">{m.standard_subject_name}</td>
                    <td className="py-2.5 px-3">
                      <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full text-[10px] font-bold font-sans">
                        {m.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Failed Students Modal */}
      {failedModal && (
        <FailedStudentsModal subject={failedModal} onClose={() => setFailedModal(null)} />
      )}
    </AppShell>
  );
}
