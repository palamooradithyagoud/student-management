'use client';

import React, { useState, useEffect, Suspense } from 'react';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';
import {
  Trophy,
  Search,
  Eye,
  RefreshCw,
  X,
  Medal,
  Award,
  Crown,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Users,
  Star,
  Zap,
  ShieldAlert,
  GraduationCap,
  Clock,
} from 'lucide-react';


// Helper utilities

function cgpaColor(v: number | null | undefined) {
  if (!v) return 'text-slate-400';
  if (v >= 9.0) return 'text-emerald-600';
  if (v >= 8.0) return 'text-indigo-600';
  if (v >= 7.0) return 'text-blue-600';
  return 'text-amber-600';
}

function attnColor(v: number | null | undefined) {
  if (!v) return 'text-slate-400';
  if (v >= 90) return 'text-emerald-600';
  if (v >= 75) return 'text-amber-600';
  return 'text-rose-600';
}

function gradeColor(grade: string) {
  if (grade === 'O') return 'bg-emerald-100 text-emerald-800 border border-emerald-200';
  if (grade === 'A+') return 'bg-indigo-100 text-indigo-800 border border-indigo-200';
  if (grade === 'A') return 'bg-blue-100 text-blue-800 border border-blue-200';
  if (grade === 'B+') return 'bg-sky-100 text-sky-800 border border-sky-200';
  if (grade === 'B') return 'bg-cyan-100 text-cyan-800 border border-cyan-200';
  if (grade === 'C') return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
  if (grade === 'F' || grade === 'AB') return 'bg-rose-100 text-rose-800 border border-rose-200';
  return 'bg-slate-100 text-slate-700 border border-slate-200';
}


// Student Detail Modal

function StudentModal({ student, onClose }: { student: any; onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<'overview' | 'courses' | 'insights'>('overview');

  const sem1Records = student.records?.filter((r: any) => r.semester === 1) || [];
  const sem2Records = student.records?.filter((r: any) => r.semester === 2) || [];
  const sem1Sum = student.semester_summaries?.find((s: any) => s.semester === 1);
  const sem2Sum = student.semester_summaries?.find((s: any) => s.semester === 2);

  const sectionColor =
    student.section === 'A'
      ? 'bg-indigo-500'
      : student.section === 'B'
      ? 'bg-purple-500'
      : 'bg-emerald-500';

  const CourseTable = ({ records, semSum }: { records: any[]; semSum: any }) => (
    <div className="border border-slate-100 rounded-2xl overflow-hidden">
      <table className="w-full text-xs text-left">
        <thead className="bg-slate-50 text-slate-400 font-bold border-b border-slate-100">
          <tr>
            <th className="py-2 px-3">Subject</th>
            <th className="py-2 px-3 text-center">Grade</th>
            <th className="py-2 px-3 text-center">GP</th>
            <th className="py-2 px-3 text-center">Attn %</th>
            <th className="py-2 px-3 text-right">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {records.map((rec: any, idx: number) => (
            <tr key={idx} className={`hover:bg-slate-50/70 ${rec.is_backlog ? 'bg-rose-50/40' : ''}`}>
              <td className="py-2.5 px-3">
                <p className="font-bold text-slate-900 leading-snug">{rec.subject_name || rec.subject_code}</p>
                <p className="text-[10px] font-mono text-slate-400">{rec.subject_code}</p>
              </td>
              <td className="py-2.5 px-3 text-center">
                <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg text-xs font-black ${gradeColor(rec.grade)}`}>
                  {rec.grade || '—'}
                </span>
              </td>
              <td className="py-2.5 px-3 text-center font-mono font-bold text-slate-700">
                {rec.grade_point ?? '—'}
              </td>
              <td className={`py-2.5 px-3 text-center font-bold ${attnColor(rec.attendance_percentage)}`}>
                {rec.attendance_percentage ? `${rec.attendance_percentage}%` : '—'}
                {rec.is_low_attendance && <span title="Below 75%" className="inline"><AlertTriangle className="inline ml-1 w-3 h-3 text-rose-500" /></span>}
              </td>
              <td className="py-2.5 px-3 text-right">
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  rec.status === 'PASS' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                }`}>
                  {rec.status || '—'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-100 w-full max-w-3xl max-h-[93vh] overflow-hidden flex flex-col animate-scale-in">
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-4 border-b border-slate-100 shrink-0">
          <div className="flex items-center gap-3.5">
            <div className={`w-12 h-12 rounded-2xl ${sectionColor} text-white flex items-center justify-center text-base font-black shrink-0 shadow-sm`}>
              {student.student_name ? student.student_name.slice(0, 2).toUpperCase() : 'ST'}
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-slate-900 leading-tight">{student.student_name || '—'}</h2>
              <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                <span className="font-mono text-xs font-bold text-slate-700">{student.roll_no}</span>
                <span className="text-slate-300">•</span>
                <span className="text-xs font-bold text-slate-500">Section {student.section}</span>
                <span className="text-slate-300">•</span>
                <span className="text-xs font-semibold text-indigo-600">{student.batch || '2025-2029'}</span>
              </div>
              <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                {student.academic_standing && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                    {student.academic_standing}
                  </span>
                )}
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  student.status_category === 'Active'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                    : 'bg-rose-50 text-rose-700 border border-rose-100'
                }`}>
                  {student.status_category || 'Active'}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-900 rounded-full hover:bg-slate-100 transition-colors cursor-pointer active:scale-95 shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Bar */}
        <div className="flex gap-1 px-6 py-3 border-b border-slate-100 bg-slate-50/50 shrink-0">
          {(['overview', 'courses', 'insights'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer capitalize ${
                activeTab === tab
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {tab === 'overview' ? 'Overview' : tab === 'courses' ? 'Courses' : 'Insights'}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1">

          {/* OVERVIEW TAB */}
          {activeTab === 'overview' && (
            <div className="p-6 space-y-5">
              {/* Ranking & Key Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  {
                    label: 'Dept Rank', value: `#${student.department_rank}`,
                    sub: `of ${student.total_students_dept}`,
                    icon: <Trophy className="w-4 h-4 text-amber-500" />,
                    bg: 'bg-amber-50 border-amber-100', vcolor: 'text-amber-600',
                  },
                  {
                    label: 'Section Rank', value: `#${student.section_rank}`,
                    sub: `of ${student.total_students_section}`,
                    icon: <Users className="w-4 h-4 text-indigo-500" />,
                    bg: 'bg-indigo-50 border-indigo-100', vcolor: 'text-indigo-600',
                  },
                  {
                    label: 'Overall CGPA', value: student.overall_cgpa?.toFixed(2) ?? '—',
                    sub: 'Avg of Sem 1 & 2',
                    icon: <GraduationCap className="w-4 h-4 text-emerald-500" />,
                    bg: 'bg-emerald-50 border-emerald-100', vcolor: cgpaColor(student.overall_cgpa),
                  },
                  {
                    label: 'Attendance', value: student.overall_attendance ? `${student.overall_attendance}%` : '—',
                    sub: `${student.total_classes_attended ?? 0} / ${student.total_classes_conducted ?? 0} classes`,
                    icon: <Clock className="w-4 h-4 text-sky-500" />,
                    bg: 'bg-sky-50 border-sky-100', vcolor: attnColor(student.overall_attendance),
                  },
                ].map((card) => (
                  <div key={card.label} className={`${card.bg} border rounded-2xl p-3.5 flex flex-col justify-between`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{card.label}</span>
                      {card.icon}
                    </div>
                    <div>
                      <div className={`text-xl font-black ${card.vcolor}`}>{card.value}</div>
                      <div className="text-[10px] text-slate-400 font-medium mt-0.5">{card.sub}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Credit & Course Counts */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Credits Earned', value: student.total_credits_earned ?? 0, sub: `of ${student.total_credits_registered ?? 0} registered`, color: 'text-slate-900' },
                  { label: 'Courses Passed', value: student.total_courses_passed ?? 0, sub: `of ${student.total_courses_registered ?? 0} total`, color: 'text-emerald-700' },
                  { label: 'Active Backlogs', value: student.total_active_backlogs ?? 0, sub: 'across all semesters', color: (student.total_active_backlogs ?? 0) > 0 ? 'text-rose-700' : 'text-emerald-700' },
                  { label: 'Attendance Status', value: student.overall_attendance ? `${student.overall_attendance}%` : '—', sub: student.attendance_standing || '—', color: attnColor(student.overall_attendance) },
                ].map((stat) => (
                  <div key={stat.label} className="bg-slate-50 border border-slate-100 rounded-2xl p-3.5">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">{stat.label}</div>
                    <div className={`text-lg font-black ${stat.color}`}>{stat.value}</div>
                    <div className="text-[10px] text-slate-400 font-medium mt-0.5 truncate">{stat.sub}</div>
                  </div>
                ))}
              </div>

              {/* Semester Comparison */}
              {student.semester_summaries?.length > 0 && (
                <div>
                  <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Semester-wise Performance</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {student.semester_summaries.map((sum: any) => (
                      <div key={sum.semester} className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-xl bg-slate-900 text-white flex items-center justify-center text-xs font-black">
                              S{sum.semester}
                            </div>
                            <span className="text-sm font-extrabold text-slate-900">Semester {sum.semester}</span>
                          </div>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            sum.backlog_count === 0 ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                          }`}>
                            {sum.backlog_count === 0 ? 'No Backlogs' : `${sum.backlog_count} Backlog(s)`}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">SGPA</div>
                            <div className={`text-xl font-black mt-0.5 ${cgpaColor(sum.sgpa)}`}>{sum.sgpa?.toFixed(2) ?? '—'}</div>
                            {sum.sgpa_change !== null && sum.sgpa_change !== undefined && sum.semester > 1 && (
                              <div className={`flex items-center gap-0.5 text-[10px] font-bold mt-0.5 ${sum.sgpa_change >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                                {sum.sgpa_change >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                {sum.sgpa_change >= 0 ? `+${sum.sgpa_change}` : sum.sgpa_change} vs S1
                              </div>
                            )}
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Attendance</div>
                            <div className={`text-xl font-black mt-0.5 ${attnColor(sum.average_attendance)}`}>
                              {sum.average_attendance ? `${sum.average_attendance}%` : '—'}
                            </div>
                            {sum.attendance_change !== null && sum.attendance_change !== undefined && sum.semester > 1 && (
                              <div className={`flex items-center gap-0.5 text-[10px] font-bold mt-0.5 ${sum.attendance_change >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                                {sum.attendance_change >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                {sum.attendance_change >= 0 ? `+${sum.attendance_change}%` : `${sum.attendance_change}%`} vs S1
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-3 mt-3 pt-3 border-t border-slate-200/60 text-xs">
                          <div className="flex items-center gap-1 text-emerald-700 font-semibold">
                            <CheckCircle className="w-3 h-3" />{sum.passed_subject_count ?? 0} passed
                          </div>
                          {(sum.failed_subject_count ?? 0) > 0 && (
                            <div className="flex items-center gap-1 text-rose-700 font-semibold">
                              <AlertTriangle className="w-3 h-3" />{sum.failed_subject_count} failed
                            </div>
                          )}
                          <div className="ml-auto text-[10px] text-slate-400 font-medium">
                            {sum.credits_earned?.toFixed(0) ?? 0} / {sum.credits_registered?.toFixed(0) ?? 0} credits
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* COURSES TAB */}
          {activeTab === 'courses' && (
            <div className="p-6 space-y-5">
              {sem1Records.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-slate-900 text-white flex items-center justify-center text-[10px] font-black">S1</div>
                    <h4 className="text-xs font-extrabold text-slate-900">Semester 1</h4>
                    {sem1Sum && <span className={`ml-auto text-xs font-black ${cgpaColor(sem1Sum.sgpa)}`}>SGPA {sem1Sum.sgpa?.toFixed(2) ?? '—'}</span>}
                  </div>
                  <CourseTable records={sem1Records} semSum={sem1Sum} />
                </div>
              )}

              {sem2Records.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-indigo-700 text-white flex items-center justify-center text-[10px] font-black">S2</div>
                    <h4 className="text-xs font-extrabold text-slate-900">Semester 2</h4>
                    {sem2Sum && <span className={`ml-auto text-xs font-black ${cgpaColor(sem2Sum.sgpa)}`}>SGPA {sem2Sum.sgpa?.toFixed(2) ?? '—'}</span>}
                  </div>
                  <CourseTable records={sem2Records} semSum={sem2Sum} />
                </div>
              )}

              {student.records?.length === 0 && (
                <div className="py-12 text-center text-slate-400 text-xs">No course records available for this student.</div>
              )}
            </div>
          )}

          {/* INSIGHTS TAB */}
          {activeTab === 'insights' && (
            <div className="p-6 space-y-5">
              {/* Standing Banner */}
              <div className={`rounded-2xl p-4 flex items-center gap-3 ${
                (student.total_active_backlogs ?? 0) === 0
                  ? 'bg-emerald-50 border border-emerald-100'
                  : 'bg-rose-50 border border-rose-100'
              }`}>
                {(student.total_active_backlogs ?? 0) === 0
                  ? <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                  : <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0" />}
                <div>
                  <div className="text-xs font-extrabold text-slate-900">{student.academic_standing}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{student.attendance_standing}</div>
                </div>
              </div>

              {/* Strengths */}
              {student.strengths?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-3">
                    <Star className="w-3.5 h-3.5 text-amber-500" />
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Academic Strengths</h4>
                  </div>
                  <div className="space-y-2">
                    {student.strengths.map((s: string, i: number) => (
                      <div key={i} className="flex items-start gap-2.5 bg-emerald-50/70 border border-emerald-100 rounded-xl px-3.5 py-2.5">
                        <Zap className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                        <p className="text-xs font-semibold text-slate-800 leading-relaxed">{s}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Risks & Alerts */}
              {student.risks_and_alerts?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-3">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Risks & Alerts</h4>
                  </div>
                  <div className="space-y-2">
                    {student.risks_and_alerts.map((r: string, i: number) => {
                      const isOk = r.toLowerCase().startsWith('no critical');
                      return (
                        <div key={i} className={`flex items-start gap-2.5 rounded-xl px-3.5 py-2.5 border ${
                          isOk ? 'bg-slate-50 border-slate-100' : 'bg-rose-50/70 border-rose-100'
                        }`}>
                          {isOk
                            ? <CheckCircle className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                            : <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />}
                          <p className="text-xs font-semibold text-slate-800 leading-relaxed">{r}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Department Info */}
              <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 space-y-2">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Department Info</div>
                {[
                  { label: 'Department', value: student.department || 'CSE (AI & ML)' },
                  { label: 'Dept Code', value: student.department_code || 'CSM' },
                  { label: 'Batch', value: student.batch || '2025-2029' },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between text-xs">
                    <span className="text-slate-500 font-medium">{row.label}</span>
                    <span className="font-bold text-slate-900">{row.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StudentsContent() {
  const [students, setStudents] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [section, setSection] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [loadingDetail, setLoadingDetail] = useState<string | null>(null);

  // Initialize query parameters on client mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const q = urlParams.get('search');
      const sec = urlParams.get('section');
      if (q) setSearch(q);
      if (sec) setSection(sec);
    }
  }, []);

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.append('search', search.trim());
      if (section) params.append('section', section);
      params.append('limit', '300');

      const res = await api.get(`/api/students?${params.toString()}`);
      setStudents(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Failed to load leaderboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [section, search]);

  const viewStudentDetails = async (rollNo: string) => {
    if (loadingDetail) return;
    setLoadingDetail(rollNo);
    try {
      const res = await api.get(`/api/students/${rollNo}`);
      setSelectedStudent(res.data);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        `Could not load details for ${rollNo}. Please try again.`;
      alert(msg);
    } finally {
      setLoadingDetail(null);
    }
  };

  const top3 = !search && !section ? students.slice(0, 3) : [];

  return (
    <AppShell onSearch={(q) => setSearch(q)}>
      <div className="space-y-6 animate-fade-in">
        {/* Header & Section Filter Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
              <Trophy className="w-6 h-6 text-amber-500" />
              <span>Academic Leaderboard</span>
              <span className="text-xs bg-slate-100 text-slate-700 font-bold px-2.5 py-1 rounded-full">
                {total} Students
              </span>
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Top-to-bottom student rankings across Semester 1 & 2 with SGPA/CGPA and backlog performance.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 bg-slate-100/90 p-1 rounded-full text-xs font-semibold">
              {[
                { label: 'All Sections (193)', val: '' },
                { label: 'Section A (65)', val: 'A' },
                { label: 'Section B (64)', val: 'B' },
                { label: 'Section C (64)', val: 'C' },
              ].map((sec) => (
                <button
                  key={sec.val}
                  type="button"
                  onClick={() => setSection(sec.val)}
                  className={`px-3 py-1.5 rounded-full transition-all cursor-pointer text-xs ${
                    section === sec.val
                      ? 'bg-slate-900 text-white font-bold shadow-xs'
                      : 'text-slate-500 hover:text-slate-900 font-medium'
                  }`}
                >
                  {sec.label}
                </button>
              ))}
            </div>

            <button
              onClick={fetchStudents}
              className="p-2 text-slate-400 hover:text-slate-800 rounded-full cursor-pointer transition-colors"
              title="Refresh Leaderboard"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Top 3 Podium -- now clickable */}
        {top3.length === 3 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 1st Place - Gold */}
            <div
              className="bg-gradient-to-b from-amber-50/80 to-amber-100/40 border border-amber-200 rounded-3xl p-5 shadow-xs flex items-center justify-between relative overflow-hidden order-1 md:order-2 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => viewStudentDetails(top3[0]?.roll_no)}
            >
              <div className="flex items-center space-x-3.5">
                <div className="w-11 h-11 rounded-2xl bg-amber-400 text-slate-950 flex items-center justify-center font-extrabold shadow-sm">
                  <Crown className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[10px] font-black uppercase tracking-wider text-amber-700 bg-amber-200/80 px-2 py-0.5 rounded-full">
                      Rank #1
                    </span>
                    <span className="text-[10px] font-bold text-slate-500">Sec {top3[0]?.section}</span>
                  </div>
                  <h3 className="text-sm font-extrabold text-slate-900 mt-1 truncate max-w-[160px]">
                    {top3[0]?.student_name}
                  </h3>
                  <p className="text-[10px] font-mono text-slate-500">{top3[0]?.roll_no}</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Overall SGPA</span>
                <span className="text-xl font-black text-amber-600">{top3[0]?.overall_sgpa?.toFixed(2)}</span>
              </div>
            </div>

            {/* 2nd Place - Silver */}
            <div
              className="bg-gradient-to-b from-slate-50 to-slate-100/60 border border-slate-200 rounded-3xl p-5 shadow-xs flex items-center justify-between relative overflow-hidden order-2 md:order-1 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => viewStudentDetails(top3[1]?.roll_no)}
            >
              <div className="flex items-center space-x-3.5">
                <div className="w-11 h-11 rounded-2xl bg-slate-300 text-slate-800 flex items-center justify-center font-extrabold shadow-sm">
                  <Medal className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[10px] font-black uppercase tracking-wider text-slate-700 bg-slate-200 px-2 py-0.5 rounded-full">
                      Rank #2
                    </span>
                    <span className="text-[10px] font-bold text-slate-500">Sec {top3[1]?.section}</span>
                  </div>
                  <h3 className="text-sm font-extrabold text-slate-900 mt-1 truncate max-w-[160px]">
                    {top3[1]?.student_name}
                  </h3>
                  <p className="text-[10px] font-mono text-slate-500">{top3[1]?.roll_no}</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Overall SGPA</span>
                <span className="text-xl font-black text-slate-800">{top3[1]?.overall_sgpa?.toFixed(2)}</span>
              </div>
            </div>

            {/* 3rd Place - Bronze */}
            <div
              className="bg-gradient-to-b from-orange-50/60 to-orange-100/40 border border-orange-200 rounded-3xl p-5 shadow-xs flex items-center justify-between relative overflow-hidden order-3 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => viewStudentDetails(top3[2]?.roll_no)}
            >
              <div className="flex items-center space-x-3.5">
                <div className="w-11 h-11 rounded-2xl bg-orange-300 text-amber-950 flex items-center justify-center font-extrabold shadow-sm">
                  <Award className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[10px] font-black uppercase tracking-wider text-amber-800 bg-orange-200/80 px-2 py-0.5 rounded-full">
                      Rank #3
                    </span>
                    <span className="text-[10px] font-bold text-slate-500">Sec {top3[2]?.section}</span>
                  </div>
                  <h3 className="text-sm font-extrabold text-slate-900 mt-1 truncate max-w-[160px]">
                    {top3[2]?.student_name}
                  </h3>
                  <p className="text-[10px] font-mono text-slate-500">{top3[2]?.roll_no}</p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Overall SGPA</span>
                <span className="text-xl font-black text-amber-700">{top3[2]?.overall_sgpa?.toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Search Input Bar */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-md group">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-slate-900 transition-colors duration-200">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search student name or roll number (e.g. 25881A6693)..."
              className="w-full pl-10 pr-10 py-2.5 bg-white border border-slate-200 rounded-2xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-900/5 transition-all duration-200 font-medium shadow-xs"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-700 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {search && (
            <span className="text-xs text-slate-500 font-medium">
              Showing {students.length} matching students
            </span>
          )}
        </div>

        {/* Main Leaderboard Table */}
        <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-bold">
                  <th className="py-3 px-3 w-16 text-center">Rank</th>
                  <th className="py-3 px-3">Student Name</th>
                  <th className="py-3 px-3">Roll Number</th>
                  <th className="py-3 px-3 text-center">Sec</th>
                  <th className="py-3 px-3 text-center">Sem 1 CGPA</th>
                  <th className="py-3 px-3 text-center">Sem 2 CGPA</th>
                  <th className="py-3 px-3 text-center">Sem 1 Back</th>
                  <th className="py-3 px-3 text-center">Sem 2 Back</th>
                  <th className="py-3 px-3 text-center">Overall SGPA</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={10} className="py-12 text-center text-slate-400">
                      <div className="flex items-center justify-center space-x-2">
                        <RefreshCw className="w-4 h-4 animate-spin text-slate-400" />
                        <span>Loading Leaderboard Rankings...</span>
                      </div>
                    </td>
                  </tr>
                ) : students.length > 0 ? (
                  students.map((s) => {
                    const isTop1 = s.rank === 1;
                    const isTop2 = s.rank === 2;
                    const isTop3 = s.rank === 3;
                    const isLoadingThis = loadingDetail === s.roll_no;

                    return (
                      <tr
                        key={s.roll_no}
                        className={`hover:bg-slate-50/80 transition-colors ${isTop1 ? 'bg-amber-50/30 font-semibold' : ''}`}
                      >
                        {/* Rank */}
                        <td className="py-3 px-3 text-center font-bold">
                          {isTop1 ? (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-amber-400 text-slate-950 text-xs font-black shadow-xs">1</span>
                          ) : isTop2 ? (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-300 text-slate-900 text-xs font-black shadow-xs">2</span>
                          ) : isTop3 ? (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-300 text-amber-950 text-xs font-black shadow-xs">3</span>
                          ) : (
                            <span className="text-slate-400 font-mono text-xs font-semibold">#{s.rank}</span>
                          )}
                        </td>

                        {/* Student Name */}
                        <td className="py-3 px-3">
                          <div className="flex items-center space-x-2.5">
                            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0 ${
                              s.section === 'A' ? 'bg-indigo-500' : s.section === 'B' ? 'bg-purple-500' : 'bg-emerald-500'
                            }`}>
                              {s.student_name ? s.student_name.slice(0, 2) : 'ST'}
                            </div>
                            <button
                              className="font-bold text-slate-900 hover:text-indigo-600 transition-colors cursor-pointer flex items-center gap-1 text-left"
                              onClick={() => viewStudentDetails(s.roll_no)}
                            >
                              {s.student_name || '—'}
                              {isLoadingThis && <RefreshCw className="w-3 h-3 animate-spin text-indigo-400 ml-1" />}
                            </button>
                          </div>
                        </td>

                        {/* Roll Number */}
                        <td className="py-3 px-3 font-mono font-bold text-slate-700">{s.roll_no}</td>

                        {/* Section */}
                        <td className="py-3 px-3 text-center">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                            s.section === 'A' ? 'bg-indigo-50 text-indigo-700 border border-indigo-100' :
                            s.section === 'B' ? 'bg-purple-50 text-purple-700 border border-purple-100' :
                            'bg-emerald-50 text-emerald-700 border border-emerald-100'
                          }`}>
                            {s.section || 'A'}
                          </span>
                        </td>

                        {/* Sem 1 CGPA */}
                        <td className="py-3 px-3 text-center font-mono font-bold text-slate-700">
                          {s.sem1_sgpa !== null && s.sem1_sgpa !== undefined ? s.sem1_sgpa.toFixed(2) : '—'}
                        </td>

                        {/* Sem 2 CGPA */}
                        <td className="py-3 px-3 text-center font-mono font-bold text-slate-700">
                          {s.sem2_sgpa !== null && s.sem2_sgpa !== undefined ? s.sem2_sgpa.toFixed(2) : '—'}
                        </td>

                        {/* Sem 1 Back */}
                        <td className="py-3 px-3 text-center">
                          {s.sem1_back > 0 ? (
                            <span className="inline-flex items-center justify-center px-2 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded-full font-bold text-[10px]">
                              {s.sem1_back}
                            </span>
                          ) : (
                            <span className="text-slate-400 font-mono text-xs">0</span>
                          )}
                        </td>

                        {/* Sem 2 Back */}
                        <td className="py-3 px-3 text-center">
                          {s.sem2_back > 0 ? (
                            <span className="inline-flex items-center justify-center px-2 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded-full font-bold text-[10px]">
                              {s.sem2_back}
                            </span>
                          ) : (
                            <span className="text-slate-400 font-mono text-xs">0</span>
                          )}
                        </td>

                        {/* Overall SGPA */}
                        <td className="py-3 px-3 text-center">
                          {s.overall_sgpa !== null && s.overall_sgpa !== undefined ? (
                            <span className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-black ${
                              s.overall_sgpa >= 9.0 ? 'bg-[#d9f99d] text-slate-950 shadow-2xs' :
                              s.overall_sgpa >= 8.0 ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
                              s.overall_sgpa >= 7.0 ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                              'bg-amber-50 text-amber-800 border border-amber-200'
                            }`}>
                              {s.overall_sgpa.toFixed(2)}
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>

                        {/* Action */}
                        <td className="py-3 px-3 text-right">
                          <button
                            onClick={() => viewStudentDetails(s.roll_no)}
                            disabled={!!loadingDetail}
                            className="inline-flex items-center space-x-1 p-1.5 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
                            title="View Full Profile"
                          >
                            {isLoadingThis ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </button>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={10} className="py-12 text-center text-slate-400">
                      No students found matching current filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedStudent && (
        <StudentModal student={selectedStudent} onClose={() => setSelectedStudent(null)} />
      )}
    </AppShell>
  );
}

export default function StudentsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    }>
      <StudentsContent />
    </Suspense>
  );
}
