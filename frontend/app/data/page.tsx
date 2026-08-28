'use client';

import React, { useState, useEffect } from 'react';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';
import { 
  CheckCircle2, 
  Play, 
  RefreshCw, 
  Layers, 
  ShieldCheck,
  FileSpreadsheet
} from 'lucide-react';

export default function DataPage() {
  const [processing, setProcessing] = useState(false);
  const [processResult, setProcessResult] = useState<any>(null);
  const [cleaningLogs, setCleaningLogs] = useState<any[]>([]);
  const [mappingRecords, setMappingRecords] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'logs' | 'mapping'>('logs');

  const fetchLogs = async () => {
    try {
      const [logsRes, mapRes] = await Promise.all([
        api.get('/api/data/cleaning-logs?limit=50'),
        api.get('/api/data/mapping-report?limit=50'),
      ]);
      setCleaningLogs(logsRes.data);
      setMappingRecords(mapRes.data);
    } catch (err) {
      console.error('Failed to load logs:', err);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleRunPipeline = async () => {
    setProcessing(true);
    try {
      const res = await api.post('/api/data/process');
      setProcessResult(res.data);
      fetchLogs();
    } catch (err: any) {
      alert('Error executing data pipeline: ' + (err.response?.data?.detail || err.message));
    } finally {
      setProcessing(false);
    }
  };

  return (
    <AppShell>
      <div className="space-y-7 animate-fade-in">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Data Ingestion & Master Pipeline
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              Trigger normalization, subject standardization, result-attendance mapping, and master dataset generation.
            </p>
          </div>

          <button
            onClick={handleRunPipeline}
            disabled={processing}
            className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white font-bold px-5 py-3 rounded-2xl text-xs transition-all shadow-sm hover:shadow-md disabled:opacity-50 cursor-pointer self-start sm:self-auto"
          >
            <Play className={`w-4 h-4 text-[#d9f99d] ${processing ? 'animate-spin' : ''}`} />
            <span>{processing ? 'Running Master Pipeline...' : 'Run Pipeline & Build Master Dataset'}</span>
          </button>
        </div>

        {/* Pipeline Summary Banner */}
        {processResult && (
          <div className="p-6 bg-white border border-emerald-200 rounded-3xl shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2 font-bold text-sm text-slate-900">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span>Pipeline Complete in {processResult.execution_time_seconds}s</span>
              </div>
              <span className="bg-[#d9f99d] text-slate-900 px-3 py-1 rounded-full text-xs font-bold">
                Mapping Success: {processResult.mapping_success_rate}%
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-center">
              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Students</span>
                <span className="text-xl font-bold text-slate-900 block mt-0.5">{processResult.total_students}</span>
              </div>

              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Results</span>
                <span className="text-xl font-bold text-slate-900 block mt-0.5">{processResult.total_results}</span>
              </div>

              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Attendance</span>
                <span className="text-xl font-bold text-slate-900 block mt-0.5">{processResult.total_attendance}</span>
              </div>

              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Matched Pairs</span>
                <span className="text-xl font-bold text-emerald-600 block mt-0.5">{processResult.matched_records}</span>
              </div>

              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Warnings</span>
                <span className="text-xl font-bold text-amber-600 block mt-0.5">{processResult.warnings}</span>
              </div>

              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Artifacts</span>
                <span className="text-xl font-bold text-blue-600 block mt-0.5">{processResult.generated_files.length}</span>
              </div>
            </div>
          </div>
        )}

        {/* Audit Logs Table Card */}
        <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex space-x-3 text-xs font-bold">
              <button
                onClick={() => setActiveTab('logs')}
                className={`pb-1.5 border-b-2 transition-all cursor-pointer ${
                  activeTab === 'logs'
                    ? 'border-slate-900 text-slate-900'
                    : 'border-transparent text-slate-400 hover:text-slate-700'
                }`}
              >
                Data Cleaning Audit Log ({cleaningLogs.length} recent)
              </button>

              <button
                onClick={() => setActiveTab('mapping')}
                className={`pb-1.5 border-b-2 transition-all cursor-pointer ${
                  activeTab === 'mapping'
                    ? 'border-slate-900 text-slate-900'
                    : 'border-transparent text-slate-400 hover:text-slate-700'
                }`}
              >
                Result ↔ Attendance Mapping Log ({mappingRecords.length} recent)
              </button>
            </div>

            <button
              onClick={fetchLogs}
              className="flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-900 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto max-h-96">
            {activeTab === 'logs' ? (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 sticky top-0 font-bold">
                  <tr>
                    <th className="py-2.5 px-3">Source File</th>
                    <th className="py-2.5 px-3">Record ID</th>
                    <th className="py-2.5 px-3">Issue Detected</th>
                    <th className="py-2.5 px-3">Action Taken</th>
                    <th className="py-2.5 px-3">Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {cleaningLogs.length > 0 ? (
                    cleaningLogs.map((l, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="py-2 px-3 text-slate-500">{l.source_file}</td>
                        <td className="py-2 px-3 text-slate-900 font-bold">{l.record_identifier}</td>
                        <td className="py-2 px-3 text-amber-700">{l.issue}</td>
                        <td className="py-2 px-3 text-emerald-700 font-semibold">{l.action_taken}</td>
                        <td className="py-2 px-3 text-slate-500 font-sans">{l.reason}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-slate-400">
                        No cleaning log entries found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            ) : (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 sticky top-0 font-bold">
                  <tr>
                    <th className="py-2.5 px-3">Roll No</th>
                    <th className="py-2.5 px-3">Semester</th>
                    <th className="py-2.5 px-3">Subject Code</th>
                    <th className="py-2.5 px-3">Has Result</th>
                    <th className="py-2.5 px-3">Has Attendance</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-[11px]">
                  {mappingRecords.length > 0 ? (
                    mappingRecords.map((m, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="py-2 px-3 font-mono font-bold text-slate-900">{m.roll_no}</td>
                        <td className="py-2 px-3 text-slate-600">Sem {m.semester}</td>
                        <td className="py-2 px-3 font-mono text-slate-800">{m.subject_code}</td>
                        <td className="py-2 px-3 text-slate-600">{m.has_result ? '✅ Yes' : '❌ No'}</td>
                        <td className="py-2 px-3 text-slate-600">{m.has_attendance ? '✅ Yes' : '❌ No'}</td>
                        <td className="py-2 px-3">
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                            m.mapping_status === 'MATCHED'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-amber-50 text-amber-700 border border-amber-200'
                          }`}>
                            {m.mapping_status}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-slate-400">
                        No mapping records found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
