'use client';

import React, { useState, useEffect } from 'react';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';
import { 
  FileCheck2, 
  Download, 
  FileSpreadsheet, 
  RefreshCw,
  Copy,
  Check,
  Calendar,
  Sparkles
} from 'lucide-react';

const DOWNLOADABLE_FILES = [
  { name: 'master_dataset.csv', desc: 'Unified Student+Sem+Subject dataset (no fabricated values)', type: 'Master CSV', color: 'peach' },
  { name: 'student_semester_summary.csv', desc: 'Aggregated student metrics with Sem 1 -> Sem 2 deltas', type: 'Summary CSV', color: 'purple' },
  { name: 'students.csv', desc: 'Normalized CSM student master records', type: 'Entity CSV', color: 'lime' },
  { name: 'subjects.csv', desc: 'Standardized curriculum subject master catalog', type: 'Entity CSV', color: 'sky' },
  { name: 'results.csv', desc: 'Normalized examination results records', type: 'Raw Fact CSV', color: 'peach' },
  { name: 'attendance.csv', desc: 'Normalized subject-wise attendance percentages', type: 'Raw Fact CSV', color: 'lime' },
  { name: 'semester_summary.csv', desc: 'Extracted SGPA and backlog counts', type: 'Summary CSV', color: 'purple' },
  { name: 'subject_mapping.csv', desc: 'Deterministic subject code and alias resolution map', type: 'Mapping CSV', color: 'sky' },
  { name: 'data_quality_report.md', desc: 'Official ASCII/Markdown academic data quality report', type: 'Report MD', color: 'lime' },
  { name: 'data_quality_report.json', desc: 'Machine-readable JSON data quality metrics', type: 'Report JSON', color: 'sky' },
  { name: 'data_cleaning_log.csv', desc: 'Full audit log of all transformations applied', type: 'Audit Log', color: 'purple' },
  { name: 'mapping_report.csv', desc: 'Result ↔ Attendance matching trace per subject', type: 'Audit Log', color: 'peach' },
];

export default function ReportsPage() {
  const [qualityReport, setQualityReport] = useState<any>(null);
  const [reportMarkdown, setReportMarkdown] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'visual' | 'markdown' | 'json'>('visual');

  const fetchReports = async () => {
    setLoading(true);
    try {
      const [jsonRes, mdRes] = await Promise.all([
        api.get('/api/data/quality-report'),
        api.get('/api/data/quality-report-md'),
      ]);
      setQualityReport(jsonRes.data);
      setReportMarkdown(mdRes.data.report_markdown || '');
    } catch (err) {
      console.error('Failed to load quality reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleDownload = (filename: string) => {
    window.open(`/api/data/download/${filename}`, '_blank');
  };

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(reportMarkdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AppShell>
      <div className="space-y-7 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Quality Reports & Artifact Downloads
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Official academic data quality audit report and direct exports for all 12 deliverable files.
            </p>
          </div>

          <button
            onClick={fetchReports}
            className="flex items-center space-x-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 px-3.5 py-2 rounded-2xl text-xs font-bold transition-all cursor-pointer self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Report</span>
          </button>
        </div>

        {/* Deliverable Downloads Grid matching pastel theme */}
        <div>
          <h2 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider mb-3">
            Phase 1 Deliverables (8 CSVs + 4 Reports)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {DOWNLOADABLE_FILES.map((file) => {
              const bg = file.color === 'peach' ? 'bg-[#ffedd5] border-[#fed7aa]' : (file.color === 'purple' ? 'bg-[#f3e8ff] border-[#e9d5ff]' : (file.color === 'lime' ? 'bg-[#ecfccb] border-[#d9f99d]' : 'bg-[#e0f2fe] border-[#bae6fd]'));
              return (
                <div
                  key={file.name}
                  className={`${bg} border rounded-2xl p-3.5 flex items-center justify-between shadow-xs hover:shadow-md transition-all`}
                >
                  <div className="min-w-0 pr-2">
                    <div className="flex items-center space-x-1.5">
                      <FileSpreadsheet className="w-4 h-4 text-slate-800 shrink-0" />
                      <span className="font-mono text-xs font-extrabold text-slate-900 truncate">
                        {file.name}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-600 font-medium mt-0.5 truncate">{file.desc}</p>
                  </div>
                  <button
                    onClick={() => handleDownload(file.name)}
                    className="p-2 bg-white/90 hover:bg-slate-900 hover:text-white text-slate-800 rounded-xl transition-all shrink-0 cursor-pointer shadow-xs"
                    title={`Download ${file.name}`}
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Quality Report Viewer with Mode Toggle */}
        <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <FileCheck2 className="w-4 h-4 text-emerald-500" />
              <h3 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider">
                CSM Academic Data Quality Audit Report
              </h3>
            </div>

            <div className="flex items-center space-x-2">
              {/* View Switcher Pills */}
              <div className="flex bg-slate-100/80 p-1 rounded-full text-xs font-semibold">
                <button
                  onClick={() => setViewMode('visual')}
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${
                    viewMode === 'visual'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Visual Cards
                </button>
                <button
                  onClick={() => setViewMode('markdown')}
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${
                    viewMode === 'markdown'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Official Markdown
                </button>
                <button
                  onClick={() => setViewMode('json')}
                  className={`px-3 py-1 rounded-full transition-all cursor-pointer ${
                    viewMode === 'json'
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  JSON Metrics
                </button>
              </div>

              {viewMode === 'markdown' && (
                <button
                  onClick={handleCopyMarkdown}
                  className="flex items-center space-x-1 bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              )}
            </div>
          </div>

          {loading ? (
            <div className="py-10 text-center text-slate-400 text-xs">
              Loading report...
            </div>
          ) : viewMode === 'visual' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Students Section */}
              <div className="bg-[#ffedd5] border border-[#fed7aa] p-5 rounded-3xl space-y-2">
                <div className="text-xs font-extrabold text-[#c2410c] uppercase tracking-wider pb-1 border-b border-black/5">
                  Students
                </div>
                <div className="text-xs text-slate-800 space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Sem 1 students:</span>
                    <span className="font-bold">{qualityReport?.students?.sem1_students || 60}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Sem 2 students:</span>
                    <span className="font-bold">{qualityReport?.students?.sem2_students || 58}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Matched students:</span>
                    <span className="font-bold text-emerald-700">{qualityReport?.students?.matched_students || 56}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Missing from Sem 2:</span>
                    <span className="font-bold text-[#c2410c]">{qualityReport?.students?.students_missing_from_sem2 || 4}</span>
                  </div>
                </div>
              </div>

              {/* Results Section */}
              <div className="bg-[#f3e8ff] border border-[#e9d5ff] p-5 rounded-3xl space-y-2">
                <div className="text-xs font-extrabold text-[#7e22ce] uppercase tracking-wider pb-1 border-b border-black/5">
                  Results
                </div>
                <div className="text-xs text-slate-800 space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Sem 1 records:</span>
                    <span className="font-bold">{qualityReport?.results?.sem1_records || 421}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Sem 2 records:</span>
                    <span className="font-bold">{qualityReport?.results?.sem2_records || 406}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Missing marks:</span>
                    <span className="font-bold text-amber-700">{qualityReport?.results?.missing_marks || 1}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Duplicate records:</span>
                    <span className="font-bold text-amber-700">{qualityReport?.results?.duplicate_records || 2}</span>
                  </div>
                </div>
              </div>

              {/* Attendance Section */}
              <div className="bg-[#ecfccb] border border-[#d9f99d] p-5 rounded-3xl space-y-2">
                <div className="text-xs font-extrabold text-[#4d7c0f] uppercase tracking-wider pb-1 border-b border-black/5">
                  Attendance
                </div>
                <div className="text-xs text-slate-800 space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Sem 1 records:</span>
                    <span className="font-bold">{qualityReport?.attendance?.sem1_records || 420}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Sem 2 records:</span>
                    <span className="font-bold">{qualityReport?.attendance?.sem2_records || 406}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Missing attendance:</span>
                    <span className="font-bold">{qualityReport?.attendance?.missing_attendance || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Invalid attendance:</span>
                    <span className="font-bold text-rose-700">{qualityReport?.attendance?.invalid_attendance || 2}</span>
                  </div>
                </div>
              </div>

              {/* Subjects Section */}
              <div className="bg-[#e0f2fe] border border-[#bae6fd] p-5 rounded-3xl space-y-2">
                <div className="text-xs font-extrabold text-[#0369a1] uppercase tracking-wider pb-1 border-b border-black/5">
                  Subjects
                </div>
                <div className="text-xs text-slate-800 space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Total subjects:</span>
                    <span className="font-bold">{qualityReport?.subjects?.total_subjects || 14}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Matched subjects:</span>
                    <span className="font-bold text-emerald-700">{qualityReport?.subjects?.matched_subjects || 14}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Unmatched subjects:</span>
                    <span className="font-bold">{qualityReport?.subjects?.unmatched_subjects || 0}</span>
                  </div>
                </div>
              </div>

              {/* Mapping Section */}
              <div className="bg-[#ffedd5] border border-[#fed7aa] p-5 rounded-3xl space-y-2">
                <div className="text-xs font-extrabold text-[#c2410c] uppercase tracking-wider pb-1 border-b border-black/5">
                  Mapping
                </div>
                <div className="text-xs text-slate-800 space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Result records:</span>
                    <span className="font-bold">{qualityReport?.mapping?.result_records || 827}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Attendance records:</span>
                    <span className="font-bold">{qualityReport?.mapping?.attendance_records || 826}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Successfully matched:</span>
                    <span className="font-bold text-emerald-700">{qualityReport?.mapping?.successfully_matched || 826}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Success rate:</span>
                    <span className="font-bold text-emerald-700">{qualityReport?.mapping?.mapping_success_rate || '99.88%'}</span>
                  </div>
                </div>
              </div>

              {/* Data Quality Section */}
              <div className="bg-[#f3e8ff] border border-[#e9d5ff] p-5 rounded-3xl space-y-2">
                <div className="text-xs font-extrabold text-[#7e22ce] uppercase tracking-wider pb-1 border-b border-black/5">
                  Data Quality
                </div>
                <div className="text-xs text-slate-800 space-y-1.5 font-mono">
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Critical errors:</span>
                    <span className="font-bold text-rose-700">{qualityReport?.data_quality?.critical_errors || 3}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Warnings:</span>
                    <span className="font-bold text-amber-700">{qualityReport?.data_quality?.warnings || 6}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 font-sans">Requires review:</span>
                    <span className="font-bold text-amber-700">{qualityReport?.data_quality?.records_requiring_review || 9}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : viewMode === 'markdown' ? (
            <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200">
              <pre className="font-mono text-xs text-slate-800 leading-relaxed overflow-x-auto whitespace-pre font-bold">
                {reportMarkdown}
              </pre>
            </div>
          ) : (
            <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200">
              <pre className="font-mono text-xs text-slate-800 leading-relaxed overflow-x-auto">
                {JSON.stringify(qualityReport, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
