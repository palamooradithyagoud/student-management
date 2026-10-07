'use client';

import React, { useState, useEffect, useRef } from 'react';
import AppShell from '@/components/AppShell';
import api from '@/lib/api';
import { 
  CheckCircle2, 
  Play, 
  RefreshCw, 
  Layers, 
  Upload,
  FileSpreadsheet,
  AlertCircle,
  Plus,
  X,
  FileText,
  Calendar,
  Check,
  ChevronRight,
  Database,
  ArrowUpRight,
  Trash2,
  AlertTriangle
} from 'lucide-react';

interface BatchItem {
  id: number;
  name: string;
  department: string;
  regulation?: string;
  start_year?: number;
  end_year?: number;
  is_active: boolean;
}

interface SectionAttendance {
  section: string;
  filename: string;
  row_count: number;
  uploaded_at: string;
}

interface SemesterStatus {
  semester: number;
  result_uploaded: boolean;
  result_filename?: string;
  result_row_count?: number;
  result_uploaded_at?: string;
  attendance_sections: SectionAttendance[];
}

export default function DataPage() {
  // Batch State
  const [batches, setBatches] = useState<BatchItem[]>([]);
  const [selectedBatch, setSelectedBatch] = useState<string>('2024-2028');
  const [showBatchModal, setShowBatchModal] = useState<boolean>(false);
  const [newBatchName, setNewBatchName] = useState<string>('');
  const [newRegulation, setNewRegulation] = useState<string>('R22');
  const [newStartYear, setNewStartYear] = useState<string>('2025');
  const [newEndYear, setNewEndYear] = useState<string>('2029');
  const [creatingBatch, setCreatingBatch] = useState<boolean>(false);

  // Clear / Purge Database Modal State
  const [showClearModal, setShowClearModal] = useState<boolean>(false);
  const [purgeUploadFiles, setPurgeUploadFiles] = useState<boolean>(false);
  const [clearingDatabase, setClearingDatabase] = useState<boolean>(false);

  // Semester State (1 to 8)
  const [selectedSemester, setSelectedSemester] = useState<number>(1);
  const [batchStatus, setBatchStatus] = useState<SemesterStatus[]>([]);

  // Section Attendance Upload State
  const [attendanceSection, setAttendanceSection] = useState<string>('A');
  const [attendanceFile, setAttendanceFile] = useState<File | null>(null);
  const [uploadingAttendance, setUploadingAttendance] = useState<boolean>(false);
  const attendanceInputRef = useRef<HTMLInputElement>(null);

  // Overall Result Upload State
  const [resultFile, setResultFile] = useState<File | null>(null);
  const [uploadingResult, setUploadingResult] = useState<boolean>(false);
  const resultInputRef = useRef<HTMLInputElement>(null);

  // Pipeline Execution State
  const [processing, setProcessing] = useState<boolean>(false);
  const [processResult, setProcessResult] = useState<any>(null);

  // Logs & History State
  const [cleaningLogs, setCleaningLogs] = useState<any[]>([]);
  const [mappingRecords, setMappingRecords] = useState<any[]>([]);
  const [uploadLogs, setUploadLogs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'status' | 'logs' | 'mapping' | 'uploads'>('status');

  // Load Batches & Batch Status
  const fetchBatches = async () => {
    try {
      const res = await api.get('/api/data/batches');
      setBatches(res.data);
      if (res.data.length > 0 && !res.data.some((b: BatchItem) => b.name === selectedBatch)) {
        setSelectedBatch(res.data[0].name);
      }
    } catch (err) {
      console.error('Failed to load batches:', err);
    }
  };

  const fetchBatchStatus = async (batchName: string) => {
    try {
      const res = await api.get(`/api/data/batch-status?batch_name=${encodeURIComponent(batchName)}`);
      setBatchStatus(res.data.semesters || []);
    } catch (err) {
      console.error('Failed to load batch status:', err);
    }
  };

  const fetchLogsAndHistory = async () => {
    try {
      const [logsRes, mapRes, uploadsRes] = await Promise.all([
        api.get('/api/data/cleaning-logs?limit=50'),
        api.get('/api/data/mapping-report?limit=50'),
        api.get('/api/data/uploads'),
      ]);
      setCleaningLogs(logsRes.data);
      setMappingRecords(mapRes.data);
      setUploadLogs(uploadsRes.data);
    } catch (err) {
      console.error('Failed to load logs:', err);
    }
  };

  useEffect(() => {
    fetchBatches();
    fetchLogsAndHistory();
  }, []);

  useEffect(() => {
    if (selectedBatch) {
      fetchBatchStatus(selectedBatch);
    }
  }, [selectedBatch]);

  // Handle Create New Batch
  const handleCreateBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBatchName.trim()) return;

    setCreatingBatch(true);
    try {
      const res = await api.post('/api/data/batches', {
        name: newBatchName.trim(),
        regulation: newRegulation.trim() || 'R22',
        start_year: parseInt(newStartYear) || undefined,
        end_year: parseInt(newEndYear) || undefined,
      });
      await fetchBatches();
      setSelectedBatch(res.data.name);
      setShowBatchModal(false);
      setNewBatchName('');
    } catch (err: any) {
      alert('Error creating batch: ' + (err.response?.data?.detail || err.message));
    } finally {
      setCreatingBatch(false);
    }
  };

  // Handle Attendance Upload
  const handleUploadAttendance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!attendanceFile) {
      alert('Please select an attendance Excel/CSV file.');
      return;
    }

    setUploadingAttendance(true);
    const formData = new FormData();
    formData.append('file', attendanceFile);
    formData.append('batch_name', selectedBatch);
    formData.append('semester', selectedSemester.toString());
    formData.append('section', attendanceSection.toUpperCase());

    try {
      await api.post('/api/data/upload/attendance', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAttendanceFile(null);
      if (attendanceInputRef.current) attendanceInputRef.current.value = '';
      await fetchBatchStatus(selectedBatch);
      await fetchLogsAndHistory();
      alert(`Attendance for Semester ${selectedSemester} - Section ${attendanceSection} uploaded successfully!`);
    } catch (err: any) {
      alert('Error uploading attendance: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploadingAttendance(false);
    }
  };

  // Handle Overall Result Upload
  const handleUploadResult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resultFile) {
      alert('Please select an overall result Excel/CSV file.');
      return;
    }

    setUploadingResult(true);
    const formData = new FormData();
    formData.append('file', resultFile);
    formData.append('batch_name', selectedBatch);
    formData.append('semester', selectedSemester.toString());

    try {
      await api.post('/api/data/upload/results', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResultFile(null);
      if (resultInputRef.current) resultInputRef.current.value = '';
      await fetchBatchStatus(selectedBatch);
      await fetchLogsAndHistory();
      alert(`Overall Results for Semester ${selectedSemester} uploaded successfully!`);
    } catch (err: any) {
      alert('Error uploading results: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploadingResult(false);
    }
  };

  // Handle Delete Section Attendance
  const handleDeleteSectionAttendance = async (section: string) => {
    if (!confirm(`Are you sure you want to delete Attendance for Semester ${selectedSemester} - Section ${section}?`)) {
      return;
    }

    try {
      await api.delete(
        `/api/data/section-attendance?batch_name=${encodeURIComponent(selectedBatch)}&semester=${selectedSemester}&section=${encodeURIComponent(section)}`
      );
      await fetchBatchStatus(selectedBatch);
      await fetchLogsAndHistory();
      alert(`Attendance for Section ${section} deleted.`);
    } catch (err: any) {
      alert('Error deleting section attendance: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Handle Delete Overall Result
  const handleDeleteResult = async () => {
    if (!confirm(`Are you sure you want to delete the overall results for Semester ${selectedSemester}?`)) {
      return;
    }

    try {
      await api.delete(
        `/api/data/semester-result?batch_name=${encodeURIComponent(selectedBatch)}&semester=${selectedSemester}`
      );
      await fetchBatchStatus(selectedBatch);
      await fetchLogsAndHistory();
      alert(`Overall results for Semester ${selectedSemester} deleted.`);
    } catch (err: any) {
      alert('Error deleting semester result: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Handle Delete Upload Record
  const handleDeleteUploadRecord = async (uploadId: number, filename: string) => {
    if (!confirm(`Delete upload record #${uploadId} (${filename})?`)) {
      return;
    }

    try {
      await api.delete(`/api/data/uploads/${uploadId}`);
      await fetchBatchStatus(selectedBatch);
      await fetchLogsAndHistory();
    } catch (err: any) {
      alert('Error deleting upload record: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Handle Clear / Purge Database
  const handleClearDatabase = async () => {
    setClearingDatabase(true);
    try {
      const res = await api.delete(`/api/data/clear-database?purge_uploads=${purgeUploadFiles}`);
      alert(res.data.message || 'Database records cleared successfully.');
      setShowClearModal(false);
      setProcessResult(null);
      await fetchBatchStatus(selectedBatch);
      await fetchLogsAndHistory();
    } catch (err: any) {
      alert('Error clearing database: ' + (err.response?.data?.detail || err.message));
    } finally {
      setClearingDatabase(false);
    }
  };

  // Run Master Pipeline
  const handleRunPipeline = async () => {
    setProcessing(true);
    const formData = new FormData();
    formData.append('batch_name', selectedBatch);

    try {
      const res = await api.post('/api/data/process', formData, { timeout: 300000 });
      setProcessResult(res.data);
      await fetchBatchStatus(selectedBatch);
      await fetchLogsAndHistory();
      alert(`Data pipeline executed successfully! Processed ${res.data.total_students || 0} students across ${res.data.total_results || 0} result records and ${res.data.total_attendance || 0} attendance records.`);
    } catch (err: any) {
      alert('Error executing data pipeline: ' + (err.response?.data?.detail || err.message));
    } finally {
      setProcessing(false);
    }
  };

  const currentSemStatus = batchStatus.find((s) => s.semester === selectedSemester);

  return (
    <AppShell>
      <div className="space-y-7 animate-fade-in pb-12">
        {/* Top Header & Batch Controls */}
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div>
            <div className="flex items-center space-x-2">
              <span className="bg-slate-900 text-[#d9f99d] text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-full">
                CSM Department
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-xs font-semibold text-slate-500">
                Batch & Semester Pipeline
              </span>
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight mt-1.5">
              Academic Data Ingestion
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Select or create an academic batch, manage Sem 1 to Sem 8, upload section attendance, overall results, or reset data.
            </p>
          </div>

          {/* Batch Selector & Actions */}
          <div className="flex items-center flex-wrap gap-2.5 self-start md:self-auto">
            <div className="flex items-center bg-slate-50 border border-slate-200 rounded-2xl px-3 py-1.5">
              <Calendar className="w-4 h-4 text-slate-400 mr-2" />
              <label htmlFor="batch-select" className="text-xs font-semibold text-slate-500 mr-2">Batch:</label>
              <select
                id="batch-select"
                aria-label="Select Academic Batch"
                value={selectedBatch}
                onChange={(e) => setSelectedBatch(e.target.value)}
                className="bg-transparent text-xs font-bold text-slate-900 outline-none cursor-pointer pr-2"
              >
                {batches.map((b) => (
                  <option key={b.id} value={b.name}>
                    {b.name} {b.regulation ? `(${b.regulation})` : ''}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setShowBatchModal(true)}
              className="flex items-center space-x-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold px-3.5 py-2.5 rounded-2xl transition-all cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Batch</span>
            </button>

            <button
              onClick={handleRunPipeline}
              disabled={processing}
              className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white font-bold px-4 py-2.5 rounded-2xl text-xs transition-all shadow-sm hover:shadow-md disabled:opacity-50 cursor-pointer"
            >
              <Play className={`w-3.5 h-3.5 text-[#d9f99d] ${processing ? 'animate-spin' : ''}`} />
              <span>{processing ? 'Processing...' : 'Run & Sync Database'}</span>
            </button>

            {/* Clear / Reset Database Data Button */}
            <button
              onClick={() => setShowClearModal(true)}
              title="Clear all ingested student and academic records from database"
              className="flex items-center space-x-1.5 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-bold px-3.5 py-2.5 rounded-2xl transition-all cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-600" />
              <span>Clear Data</span>
            </button>
          </div>
        </div>

        {/* Semester Navigator Tabs (Sem 1 to Sem 8) */}
        <div className="bg-white border border-slate-200/80 rounded-3xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-extrabold uppercase tracking-wider text-slate-700">
                Semesters (Batch: {selectedBatch})
              </span>
            </div>
            <span className="text-[11px] text-slate-400 font-medium">
              Click a semester to upload section attendance or overall results
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => {
              const status = batchStatus.find((s) => s.semester === sem);
              const hasResult = status?.result_uploaded;
              const secCount = status?.attendance_sections?.length || 0;
              const isSelected = selectedSemester === sem;

              let badgeText = 'Pending';
              let badgeColor = 'bg-slate-100 text-slate-500 border-slate-200';

              if (hasResult && secCount > 0) {
                badgeText = `Res + ${secCount} Sec`;
                badgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
              } else if (hasResult) {
                badgeText = 'Result only';
                badgeColor = 'bg-blue-50 text-blue-700 border-blue-200';
              } else if (secCount > 0) {
                badgeText = `${secCount} Sec Att`;
                badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
              }

              return (
                <button
                  key={sem}
                  onClick={() => setSelectedSemester(sem)}
                  className={`flex flex-col items-center justify-between p-3 rounded-2xl border transition-all text-center cursor-pointer ${
                    isSelected
                      ? 'bg-slate-900 border-slate-900 text-white shadow-md'
                      : 'bg-slate-50/70 border-slate-200/70 text-slate-800 hover:bg-slate-100'
                  }`}
                >
                  <span className={`text-xs font-black ${isSelected ? 'text-white' : 'text-slate-800'}`}>
                    Sem {sem}
                  </span>
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border mt-2 truncate max-w-full ${
                      isSelected ? 'bg-slate-800 text-[#d9f99d] border-slate-700' : badgeColor
                    }`}
                  >
                    {badgeText}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Upload Workspace for Active Semester */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card 1: Section-wise Attendance Upload */}
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-sm space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    Upload Section Attendance
                  </h2>
                  <p className="text-[11px] text-slate-400">
                    Semester {selectedSemester} • Batch {selectedBatch}
                  </p>
                </div>
              </div>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full">
                By Section
              </span>
            </div>

            <form onSubmit={handleUploadAttendance} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1.5">
                  Choose Section:
                </label>
                <div className="flex items-center flex-wrap gap-2">
                  {['A', 'B', 'C', 'D'].map((sec) => (
                    <button
                      type="button"
                      key={sec}
                      onClick={() => setAttendanceSection(sec)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                        attendanceSection === sec
                          ? 'bg-slate-900 border-slate-900 text-white'
                          : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      Section {sec}
                    </button>
                  ))}
                  <input
                    type="text"
                    placeholder="Custom"
                    value={!['A', 'B', 'C', 'D'].includes(attendanceSection) ? attendanceSection : ''}
                    onChange={(e) => setAttendanceSection(e.target.value.toUpperCase())}
                    className="w-20 px-2.5 py-1.5 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 outline-none uppercase"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1.5">
                  Attendance Excel/CSV File:
                </label>
                <div className="border-2 border-dashed border-slate-200 hover:border-emerald-400 rounded-2xl p-5 text-center transition-all bg-slate-50/50">
                  <input
                    type="file"
                    ref={attendanceInputRef}
                    accept=".xlsx,.xls,.csv"
                    onChange={(e) => setAttendanceFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="attendance-file-input"
                  />
                  <label
                    htmlFor="attendance-file-input"
                    className="cursor-pointer flex flex-col items-center space-y-2"
                  >
                    <Upload className="w-6 h-6 text-slate-400" />
                    <span className="text-xs font-bold text-slate-700">
                      {attendanceFile ? attendanceFile.name : `Select Section ${attendanceSection} Attendance File`}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Supports .xlsx, .xls, .csv (e.g. Conducted & Attended counts)
                    </span>
                  </label>
                </div>
              </div>

              <button
                type="submit"
                disabled={uploadingAttendance || !attendanceFile}
                className="w-full flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 px-4 rounded-xl text-xs transition-all shadow-sm disabled:opacity-50 cursor-pointer"
              >
                <Upload className={`w-3.5 h-3.5 ${uploadingAttendance ? 'animate-spin' : ''}`} />
                <span>
                  {uploadingAttendance
                    ? `Uploading Section ${attendanceSection}...`
                    : `Upload Section ${attendanceSection} Attendance`}
                </span>
              </button>
            </form>

            {/* Currently Uploaded Sections for this semester */}
            <div className="pt-2">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                Uploaded Sections for Sem {selectedSemester}:
              </span>
              {currentSemStatus?.attendance_sections && currentSemStatus.attendance_sections.length > 0 ? (
                <div className="space-y-1.5">
                  {currentSemStatus.attendance_sections.map((sec, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-lg text-[10px]">
                          Section {sec.section}
                        </span>
                        <span className="text-slate-700 font-mono text-[11px] truncate max-w-[140px] sm:max-w-[200px]">
                          {sec.filename}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[11px] font-bold text-slate-500">
                          {sec.row_count} rows
                        </span>
                        <button
                          onClick={() => handleDeleteSectionAttendance(sec.section)}
                          title={`Delete Section ${sec.section} Attendance`}
                          className="p-1 rounded-lg text-rose-500 hover:text-rose-700 hover:bg-rose-100 transition-all cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-center text-[11px] text-slate-400">
                  No section attendance files uploaded yet for Semester {selectedSemester}.
                </div>
              )}
            </div>
          </div>

          {/* Card 2: Overall Semester Result Upload */}
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-sm space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    Upload Overall Results
                  </h2>
                  <p className="text-[11px] text-slate-400">
                    Semester {selectedSemester} • Batch {selectedBatch}
                  </p>
                </div>
              </div>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full border border-blue-200">
                All Sections Combined
              </span>
            </div>

            <form onSubmit={handleUploadResult} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1.5">
                  Semester Result Excel/CSV File:
                </label>
                <div className="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-2xl p-5 text-center transition-all bg-slate-50/50">
                  <input
                    type="file"
                    ref={resultInputRef}
                    accept=".xlsx,.xls,.csv"
                    onChange={(e) => setResultFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="result-file-input"
                  />
                  <label
                    htmlFor="result-file-input"
                    className="cursor-pointer flex flex-col items-center space-y-2"
                  >
                    <Upload className="w-6 h-6 text-slate-400" />
                    <span className="text-xs font-bold text-slate-700">
                      {resultFile ? resultFile.name : `Select Semester ${selectedSemester} Overall Results File`}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Matrix grades & marks for all students in Semester {selectedSemester}
                    </span>
                  </label>
                </div>
              </div>

              <button
                type="submit"
                disabled={uploadingResult || !resultFile}
                className="w-full flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded-xl text-xs transition-all shadow-sm disabled:opacity-50 cursor-pointer"
              >
                <Upload className={`w-3.5 h-3.5 ${uploadingResult ? 'animate-spin' : ''}`} />
                <span>
                  {uploadingResult
                    ? `Uploading Sem ${selectedSemester} Results...`
                    : `Upload Sem ${selectedSemester} Overall Results`}
                </span>
              </button>
            </form>

            {/* Currently Uploaded Result Status */}
            <div className="pt-2">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-2">
                Overall Result Status for Sem {selectedSemester}:
              </span>
              {currentSemStatus?.result_uploaded ? (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <div>
                      <span className="font-bold text-slate-900 block font-mono text-[11px] truncate max-w-[180px] sm:max-w-[240px]">
                        {currentSemStatus.result_filename || `Semester ${selectedSemester} Result File`}
                      </span>
                      <span className="text-[10px] text-emerald-700 font-semibold">
                        Ready for synthesis • {currentSemStatus.result_row_count || 0} rows parsed
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="bg-emerald-200/60 text-emerald-900 font-bold px-2 py-0.5 rounded-lg text-[10px]">
                      Uploaded
                    </span>
                    <button
                      onClick={handleDeleteResult}
                      title="Delete overall results for this semester"
                      className="p-1 rounded-lg text-rose-500 hover:text-rose-700 hover:bg-rose-100 transition-all cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-center text-[11px] text-slate-400">
                  No overall result file uploaded yet for Semester {selectedSemester}.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Pipeline Execution Banner */}
        {processResult && (
          <div className="p-6 bg-white border border-emerald-200 rounded-3xl shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2 font-bold text-sm text-slate-900">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span>
                  Pipeline Complete for Batch {selectedBatch} in {processResult.execution_time_seconds}s
                </span>
              </div>
              <span className="bg-[#d9f99d] text-slate-900 px-3 py-1 rounded-full text-xs font-bold">
                Mapping Success: {processResult.mapping_success_rate}%
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-center">
              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Students</span>
                <span className="text-xl font-bold text-slate-900 block mt-0.5">
                  {processResult.total_students}
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Results</span>
                <span className="text-xl font-bold text-slate-900 block mt-0.5">
                  {processResult.total_results}
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Attendance</span>
                <span className="text-xl font-bold text-slate-900 block mt-0.5">
                  {processResult.total_attendance}
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Matched Pairs</span>
                <span className="text-xl font-bold text-emerald-600 block mt-0.5">
                  {processResult.matched_records}
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Warnings</span>
                <span className="text-xl font-bold text-amber-600 block mt-0.5">
                  {processResult.warnings}
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-100 p-3 rounded-2xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Artifacts</span>
                <span className="text-xl font-bold text-blue-600 block mt-0.5">
                  {processResult.generated_files?.length || 0}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Audit, Mapping & Uploads History */}
        <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex space-x-3 text-xs font-bold overflow-x-auto">
              <button
                onClick={() => setActiveTab('status')}
                className={`pb-1.5 border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'status'
                    ? 'border-slate-900 text-slate-900'
                    : 'border-transparent text-slate-400 hover:text-slate-700'
                }`}
              >
                Batch Overview (Sem 1 - Sem 8)
              </button>
              <button
                onClick={() => setActiveTab('uploads')}
                className={`pb-1.5 border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'uploads'
                    ? 'border-slate-900 text-slate-900'
                    : 'border-transparent text-slate-400 hover:text-slate-700'
                }`}
              >
                Uploaded Files History ({uploadLogs.length})
              </button>
              <button
                onClick={() => setActiveTab('logs')}
                className={`pb-1.5 border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'logs'
                    ? 'border-slate-900 text-slate-900'
                    : 'border-transparent text-slate-400 hover:text-slate-700'
                }`}
              >
                Data Cleaning Audit ({cleaningLogs.length})
              </button>
              <button
                onClick={() => setActiveTab('mapping')}
                className={`pb-1.5 border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                  activeTab === 'mapping'
                    ? 'border-slate-900 text-slate-900'
                    : 'border-transparent text-slate-400 hover:text-slate-700'
                }`}
              >
                Mapping Report ({mappingRecords.length})
              </button>
            </div>

            <button
              onClick={() => {
                fetchBatchStatus(selectedBatch);
                fetchLogsAndHistory();
              }}
              className="flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-900 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto max-h-96">
            {activeTab === 'status' && (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 sticky top-0 font-bold">
                  <tr>
                    <th className="py-2.5 px-3">Semester</th>
                    <th className="py-2.5 px-3">Overall Results</th>
                    <th className="py-2.5 px-3">Section Attendance Uploaded</th>
                    <th className="py-2.5 px-3">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-[11px]">
                  {batchStatus.map((s) => (
                    <tr key={s.semester} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3 font-bold text-slate-900">
                        Semester {s.semester}
                      </td>
                      <td className="py-2.5 px-3">
                        {s.result_uploaded ? (
                          <div className="flex items-center space-x-1.5">
                            <span className="inline-flex items-center space-x-1 text-emerald-700 font-semibold">
                              <Check className="w-3.5 h-3.5 text-emerald-600" />
                              <span>{s.result_filename} ({s.result_row_count} rows)</span>
                            </span>
                            <button
                              type="button"
                              onClick={async (e) => {
                                e.stopPropagation();
                                if (confirm(`Delete overall result for Semester ${s.semester}?`)) {
                                  try {
                                    await api.delete(`/api/data/semester-result?batch_name=${encodeURIComponent(selectedBatch)}&semester=${s.semester}`);
                                    await fetchBatchStatus(selectedBatch);
                                    await fetchLogsAndHistory();
                                  } catch (err: any) {
                                    alert('Error deleting: ' + (err.response?.data?.detail || err.message));
                                  }
                                }
                              }}
                              title="Delete result file"
                              className="p-1 rounded text-rose-400 hover:text-rose-700 hover:bg-rose-50 transition-colors cursor-pointer"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        ) : (
                          <span className="text-slate-400">Not uploaded</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        {s.attendance_sections.length > 0 ? (
                          <div className="flex flex-wrap gap-1.5 items-center">
                            {s.attendance_sections.map((sec, i) => (
                              <span
                                key={i}
                                className="inline-flex items-center space-x-1 bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-md font-bold text-[10px]"
                              >
                                <span>Sec {sec.section}: {sec.row_count} rows</span>
                                <button
                                  type="button"
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    if (confirm(`Delete Attendance for Semester ${s.semester} Section ${sec.section}?`)) {
                                      try {
                                        await api.delete(`/api/data/section-attendance?batch_name=${encodeURIComponent(selectedBatch)}&semester=${s.semester}&section=${encodeURIComponent(sec.section)}`);
                                        await fetchBatchStatus(selectedBatch);
                                        await fetchLogsAndHistory();
                                      } catch (err: any) {
                                        alert('Error deleting: ' + (err.response?.data?.detail || err.message));
                                      }
                                    }
                                  }}
                                  title={`Delete Section ${sec.section} Attendance`}
                                  className="text-rose-400 hover:text-rose-700 ml-0.5 cursor-pointer"
                                >
                                  <X className="w-2.5 h-2.5" />
                                </button>
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-400">No sections uploaded</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <button
                          onClick={() => setSelectedSemester(s.semester)}
                          className="text-xs font-bold text-blue-600 hover:text-blue-800 cursor-pointer"
                        >
                          Manage →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {activeTab === 'uploads' && (
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 sticky top-0 font-bold">
                  <tr>
                    <th className="py-2.5 px-3">Filename</th>
                    <th className="py-2.5 px-3">Batch</th>
                    <th className="py-2.5 px-3">Semester</th>
                    <th className="py-2.5 px-3">Section</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Rows</th>
                    <th className="py-2.5 px-3">Uploaded At</th>
                    <th className="py-2.5 px-3 text-right">Delete</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  {uploadLogs.length > 0 ? (
                    uploadLogs.map((u, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="py-2 px-3 text-slate-900 font-bold">{u.filename}</td>
                        <td className="py-2 px-3 text-slate-600">{u.batch_name || selectedBatch}</td>
                        <td className="py-2 px-3 text-slate-700">Sem {u.semester}</td>
                        <td className="py-2 px-3 text-emerald-700 font-bold">{u.section || 'N/A'}</td>
                        <td className="py-2 px-3 text-slate-500 font-sans">{u.dataset_type}</td>
                        <td className="py-2 px-3 text-slate-700">{u.row_count}</td>
                        <td className="py-2 px-3 text-slate-400 font-sans text-[10px]">
                          {new Date(u.uploaded_at).toLocaleString()}
                        </td>
                        <td className="py-2 px-3 text-right font-sans">
                          <button
                            onClick={() => handleDeleteUploadRecord(u.id, u.filename)}
                            title="Delete this upload file"
                            className="p-1 rounded-lg text-rose-500 hover:text-rose-700 hover:bg-rose-100 transition-all cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="py-6 text-center text-slate-400">
                        No uploads recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}

            {activeTab === 'logs' && (
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
            )}

            {activeTab === 'mapping' && (
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
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                              m.mapping_status === 'MATCHED'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-amber-50 text-amber-700 border border-amber-200'
                            }`}
                          >
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

      {/* Modal: Create New Batch */}
      {showBatchModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-100 space-y-4 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Calendar className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">Create Academic Batch</h3>
              </div>
              <button
                onClick={() => setShowBatchModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateBatch} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Batch Name (e.g. 2025-2029) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="2025-2029"
                  value={newBatchName}
                  onChange={(e) => setNewBatchName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-900 outline-none focus:border-slate-900"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Regulation</label>
                  <input
                    type="text"
                    value={newRegulation}
                    onChange={(e) => setNewRegulation(e.target.value)}
                    placeholder="R22"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-900 outline-none focus:border-slate-900"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">Start Year</label>
                  <input
                    type="number"
                    value={newStartYear}
                    onChange={(e) => setNewStartYear(e.target.value)}
                    placeholder="2025"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-900 outline-none focus:border-slate-900"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 block mb-1">End Year</label>
                  <input
                    type="number"
                    value={newEndYear}
                    onChange={(e) => setNewEndYear(e.target.value)}
                    placeholder="2029"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-900 outline-none focus:border-slate-900"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowBatchModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingBatch || !newBatchName.trim()}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 cursor-pointer"
                >
                  {creatingBatch ? 'Creating...' : 'Create Batch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Reset / Clear Database Academic Data */}
      {showClearModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl border border-slate-100 space-y-4 animate-scale-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2 text-rose-600">
                <AlertTriangle className="w-5 h-5" />
                <h3 className="text-base font-bold text-slate-900">Reset / Clear Academic Data</h3>
              </div>
              <button
                onClick={() => setShowClearModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              This action will <strong>permanently purge all ingested student records, subjects, results, attendance, and summaries</strong> from the database.
            </p>

            <div className="bg-rose-50 border border-rose-200/80 rounded-2xl p-3.5 text-[11px] text-rose-900 font-semibold space-y-1.5">
              <div className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
                <span>Students, Results, Attendance, and Summaries will be emptied.</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
                <span>Your HOD credentials and Batch configurations will remain preserved.</span>
              </div>
            </div>

            <div className="flex items-center space-x-2.5 pt-1">
              <input
                type="checkbox"
                id="purge-uploads-chk"
                checked={purgeUploadFiles}
                onChange={(e) => setPurgeUploadFiles(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-rose-600 focus:ring-rose-500 cursor-pointer"
              />
              <label htmlFor="purge-uploads-chk" className="text-xs font-semibold text-slate-700 cursor-pointer">
                Also purge uploaded raw files and upload history
              </label>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowClearModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleClearDatabase}
                disabled={clearingDatabase}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white disabled:opacity-50 cursor-pointer flex items-center space-x-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{clearingDatabase ? 'Clearing Data...' : 'Confirm Purge Data'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
