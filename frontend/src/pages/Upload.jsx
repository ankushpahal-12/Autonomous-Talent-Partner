import { useState, useRef, useEffect } from 'react';
import { useUpload } from '../hooks/useUpload';
import {
  Upload as UploadIcon, Plus, Trash2, CheckCircle, Clock, AlertCircle,
  ChevronDown, Search, Filter, RefreshCw
} from 'lucide-react';

export default function Upload() {
  const [activeTab, setActiveTab] = useState('candidates'); // 'candidates' or 'jobs'
  
  // ───────────────────────────────────────────────────────────────────────
  // CANDIDATE UPLOAD
  // ───────────────────────────────────────────────────────────────────────
  const {
    // Candidate Upload
    candidateName, setCandidateName,
    candidateCV, setCandidateCV,
    candidateDragActive, setCandidateDragActive,
    candidateLoading, setCandidateLoading,
    candidateError, setCandidateError,
    candidateSuccess, setCandidateSuccess,
    candidateUploadProgress, setCandidateUploadProgress,
    analyzingCandidate, setAnalyzingCandidate,
    allCandidates, setAllCandidates,
    uploadCandidate,
    analyzeCandidate,
    
    // Job Management
    jobTitle, setJobTitle,
    jobText, setJobText,
    aiPrompt, setAiPrompt,
    jobFile, setJobFile,
    mode, setMode,
    job, setJob,
    step, setStep,
    loading, setLoading,
    error, setError,
    success, setSuccess,
    editingDescription, setEditingDescription,
    editedDescription, setEditedDescription,
    suggestionPreview, setSuggestionPreview,
    previewingMerge, setPreviewingMerge,
    showPublishConfirm, setShowPublishConfirm,
    dragActive, setDragActive,
    allJobs, setAllJobs,
    jobsLoading, setJobsLoading,
    jobsError, setJobsError,
    jobsFilterStatus, setJobsFilterStatus,
    jobsDisplayCount, setJobsDisplayCount,
    deletingJobId, setDeletingJobId,
    showDeleteConfirm, setShowDeleteConfirm,
    processingJobId, setProcessingJobId,
    
    // Job Actions
    createJob,
    getSuggestions,
    applySuggestion,
    saveJobEdit,
    publishJob,
    fetchAllJobs,
    deleteJob,
    publishJobFromList,
    startEditing,
    cancelEditing,
    previewSuggestionMerge,
    cancelPreview,
  } = useUpload();

  const candidateInputRef = useRef(null);
  const jobFileInputRef = useRef(null);

  // ───────────────────────────────────────────────────────────────────────
  // FETCH JOBS ON MOUNT AND FILTER CHANGE
  // ───────────────────────────────────────────────────────────────────────
  useEffect(() => {
    fetchAllJobs();
  }, [jobsFilterStatus, fetchAllJobs]);

  // ───────────────────────────────────────────────────────────────────────
  // CANDIDATE DRAG & DROP
  // ───────────────────────────────────────────────────────────────────────
  const handleCandidateDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setCandidateDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleCandidateDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setCandidateDragActive(false);
    
    if (e.dataTransfer.files?.[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf' || file.type.startsWith('text/') || file.name.endsWith('.docx')) {
        setCandidateCV(file);
      } else {
        setCandidateError('Please upload a PDF, DOC, or TXT file');
      }
    }
  };

  // ───────────────────────────────────────────────────────────────────────
  // JOB FILE HANDLING
  // ───────────────────────────────────────────────────────────────────────
  const handleJobFileDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files?.[0]) {
      setJobFile(e.dataTransfer.files[0]);
    }
  };

  const handleJobFileDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  return (
    <div style={{ minHeight: '100vh', padding: '40px 20px', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* Header */}
        <div style={{ marginBottom: '40px' }}>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '8px', background: 'linear-gradient(90deg, #fff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Talent Hub
          </h1>
          <p style={{ fontSize: '1rem', color: '#64748b' }}>Manage job openings and upload candidate resumes</p>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '30px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '16px' }}>
          <button
            onClick={() => setActiveTab('candidates')}
            style={{
              padding: '12px 24px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === 'candidates' ? 'rgba(34, 211, 238, 0.2)' : 'transparent',
              color: activeTab === 'candidates' ? '#22d3ee' : '#94a3b8',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <UploadIcon style={{ display: 'inline', marginRight: '8px', width: '18px', height: '18px' }} />
            Upload Candidates
          </button>
          <button
            onClick={() => { setActiveTab('jobs'); fetchAllJobs(); }}
            style={{
              padding: '12px 24px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === 'jobs' ? 'rgba(34, 211, 238, 0.2)' : 'transparent',
              color: activeTab === 'jobs' ? '#22d3ee' : '#94a3b8',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <Plus style={{ display: 'inline', marginRight: '8px', width: '18px', height: '18px' }} />
            Manage Jobs
          </button>
        </div>

        {/* ─────────────────────────────────────────────────────────────────────────────── */}
        {/* CANDIDATES TAB */}
        {/* ─────────────────────────────────────────────────────────────────────────────── */}
        {activeTab === 'candidates' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '24px' }}>
            {/* Upload Form */}
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '24px' }}>
              <h2 style={{ marginBottom: '20px', color: '#fff', fontSize: '1.25rem' }}>Upload Candidate CV</h2>
              
              {candidateError && (
                <div style={{ padding: '12px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#ef4444', marginBottom: '16px', fontSize: '0.9rem' }}>
                  {candidateError}
                </div>
              )}
              
              {candidateSuccess && (
                <div style={{ padding: '12px', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '8px', color: '#10b981', marginBottom: '16px', fontSize: '0.9rem' }}>
                  {candidateSuccess}
                </div>
              )}

              {/* Name Input */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', color: '#cbd5e1', fontSize: '0.9rem', fontWeight: 600 }}>
                  Candidate Name *
                </label>
                <input
                  type="text"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  placeholder="e.g., John Doe"
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: 'rgba(15,23,42,0.8)',
                    color: '#fff',
                    fontSize: '0.95rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              {/* File Drop */}
              <div
                onDragEnter={handleCandidateDrag}
                onDragLeave={handleCandidateDrag}
                onDragOver={handleCandidateDrag}
                onDrop={handleCandidateDrop}
                onClick={() => candidateInputRef.current?.click()}
                style={{
                  padding: '40px 24px',
                  borderRadius: '8px',
                  border: `2px dashed ${candidateDragActive ? '#22d3ee' : 'rgba(255,255,255,0.2)'}`,
                  background: candidateDragActive ? 'rgba(34,211,238,0.05)' : 'rgba(255,255,255,0.02)',
                  cursor: 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.2s',
                  marginBottom: '16px'
                }}
              >
                <UploadIcon style={{ width: '32px', height: '32px', margin: '0 auto 12px', color: '#64748b' }} />
                <p style={{ color: '#94a3b8', marginBottom: '4px' }}>Drag and drop CV here</p>
                <p style={{ color: '#64748b', fontSize: '0.85rem' }}>or click to browse</p>
              </div>

              {candidateCV && (
                <div style={{ padding: '12px', background: 'rgba(34,211,238,0.1)', borderRadius: '8px', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#22d3ee', fontSize: '0.9rem' }}>✓ {candidateCV.name}</span>
                  {!candidateLoading && <button onClick={() => setCandidateCV(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '1.2rem' }}>×</button>}
                </div>
              )}

              {candidateUploadProgress > 0 && candidateUploadProgress < 100 && (
                <div style={{ marginBottom: '16px', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: `${candidateUploadProgress}%`, height: '100%', background: '#22d3ee', transition: 'width 0.3s' }} />
                </div>
              )}

              <button
                onClick={uploadCandidate}
                disabled={!candidateName.trim() || !candidateCV || candidateLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  border: 'none',
                  background: !candidateName.trim() || !candidateCV || candidateLoading ? '#475569' : '#22d3ee',
                  color: !candidateName.trim() || !candidateCV || candidateLoading ? '#94a3b8' : '#0f172a',
                  fontWeight: 600,
                  cursor: !candidateName.trim() || !candidateCV || candidateLoading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {candidateLoading ? '⏳ Uploading...' : '📤 Upload Candidate'}
              </button>
            </div>

            {/* Uploaded Candidates List */}
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '24px' }}>
              <h2 style={{ marginBottom: '20px', color: '#fff', fontSize: '1.25rem' }}>Recent Uploads</h2>
              
              {allCandidates.length === 0 ? (
                <p style={{ color: '#64748b', textAlign: 'center', paddingTop: '20px' }}>No candidates uploaded yet</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '500px', overflowY: 'auto' }}>
                  {allCandidates.slice(-10).map((candidate, i) => (
                    <div key={i} style={{ padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <p style={{ color: '#fff', margin: '0 0 4px 0', fontWeight: 500 }}>{candidate.name || candidate.candidate_id}</p>
                        <p style={{ color: '#64748b', margin: 0, fontSize: '0.8rem' }}>ID: {candidate.candidate_id?.substring(0, 12)}...</p>
                      </div>
                      <button
                        onClick={() => analyzeCandidate(candidate.candidate_id)}
                        disabled={analyzingCandidate === candidate.candidate_id}
                        style={{
                          padding: '6px 12px',
                          borderRadius: '6px',
                          border: 'none',
                          background: analyzingCandidate === candidate.candidate_id ? '#475569' : 'rgba(34,211,238,0.2)',
                          color: '#22d3ee',
                          fontSize: '0.85rem',
                          fontWeight: '600',
                          cursor: 'pointer'
                        }}
                      >
                        {analyzingCandidate === candidate.candidate_id ? '⏳ Analyzing' : '🔍 Analyze'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────────────────────── */}
        {/* JOBS TAB */}
        {/* ─────────────────────────────────────────────────────────────────────────────── */}
        {activeTab === 'jobs' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '24px' }}>
            {/* Create New Job */}
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '24px' }}>
              <h2 style={{ marginBottom: '20px', color: '#fff', fontSize: '1.25rem' }}>Create New Job</h2>
              
              {error && <div style={{ padding: '12px', background: 'rgba(239,68,68,0.1)', borderRadius: '8px', color: '#ef4444', marginBottom: '16px', fontSize: '0.9rem' }}>{error}</div>}
              {success && <div style={{ padding: '12px', background: 'rgba(16,185,129,0.1)', borderRadius: '8px', color: '#10b981', marginBottom: '16px', fontSize: '0.9rem' }}>{success}</div>}

              {/* Job Title */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', color: '#cbd5e1', fontSize: '0.9rem', fontWeight: 600 }}>Job Title *</label>
                <input
                  type="text"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="e.g., Senior React Developer"
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: 'rgba(15,23,42,0.8)',
                    color: '#fff',
                    fontSize: '0.95rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              {/* Mode Selection */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', color: '#cbd5e1', fontSize: '0.9rem', fontWeight: 600 }}>Description Source</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {['upload', 'write', 'ai'].map((m) => (
                    <button
                      key={m}
                      onClick={() => setMode(m)}
                      style={{
                        flex: 1,
                        padding: '10px',
                        borderRadius: '6px',
                        border: 'none',
                        background: mode === m ? 'rgba(34,211,238,0.2)' : 'rgba(255,255,255,0.05)',
                        color: mode === m ? '#22d3ee' : '#94a3b8',
                        fontWeight: 600,
                        fontSize: '0.9rem',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      {m === 'upload' && '📄 Upload'}
                      {m === 'write' && '✍️ Write'}
                      {m === 'ai' && '🤖 AI Generate'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Mode-specific input */}
              {mode === 'upload' && (
                <div style={{ marginBottom: '16px' }}>
                  <div
                    onDragEnter={handleJobFileDrag}
                    onDragLeave={handleJobFileDrag}
                    onDragOver={handleJobFileDrag}
                    onDrop={handleJobFileDrop}
                    onClick={() => jobFileInputRef.current?.click()}
                    style={{
                      padding: '30px',
                      borderRadius: '8px',
                      border: `2px dashed ${dragActive ? '#22d3ee' : 'rgba(255,255,255,0.2)'}`,
                      background: dragActive ? 'rgba(34,211,238,0.05)' : 'rgba(255,255,255,0.02)',
                      cursor: 'pointer',
                      textAlign: 'center'
                    }}
                  >
                    <p style={{ color: '#94a3b8' }}>Drag JD file here or click</p>
                    {jobFile && <p style={{ color: '#22d3ee', fontSize: '0.9rem', marginTop: '8px' }}>✓ {jobFile.name}</p>}
                  </div>
                  <input ref={jobFileInputRef} type="file" hidden onChange={(e) => setJobFile(e.target.files?.[0])} />
                </div>
              )}

              {mode === 'write' && (
                <div style={{ marginBottom: '16px' }}>
                  <textarea
                    value={jobText}
                    onChange={(e) => setJobText(e.target.value)}
                    placeholder="Paste job description here..."
                    style={{
                      width: '100%',
                      padding: '12px',
                      borderRadius: '8px',
                      border: '1px solid rgba(255,255,255,0.1)',
                      background: 'rgba(15,23,42,0.8)',
                      color: '#fff',
                      fontSize: '0.95rem',
                      minHeight: '120px',
                      fontFamily: 'monospace',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              )}

              {mode === 'ai' && (
                <div style={{ marginBottom: '16px' }}>
                  <textarea
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    placeholder="Describe the role and requirements..."
                    style={{
                      width: '100%',
                      padding: '12px',
                      borderRadius: '8px',
                      border: '1px solid rgba(255,255,255,0.1)',
                      background: 'rgba(15,23,42,0.8)',
                      color: '#fff',
                      fontSize: '0.95rem',
                      minHeight: '120px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              )}

              <button
                onClick={() => createJob()}
                disabled={loading || !jobTitle.trim()}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  border: 'none',
                  background: loading || !jobTitle.trim() ? '#475569' : '#22d3ee',
                  color: loading || !jobTitle.trim() ? '#94a3b8' : '#0f172a',
                  fontWeight: 600,
                  cursor: loading || !jobTitle.trim() ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? '⏳ Creating...' : '✨ Create Job'}
              </button>
            </div>

            {/* All Jobs List */}
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', padding: '24px' }}>
              <h2 style={{ marginBottom: '20px', color: '#fff', fontSize: '1.25rem' }}>Published Jobs</h2>
              
              {/* Filter Buttons */}
              <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => {
                    setJobsFilterStatus('all');
                    setJobsDisplayCount(5);
                  }}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    background: jobsFilterStatus === 'all' ? '#22d3ee' : 'rgba(255,255,255,0.1)',
                    color: jobsFilterStatus === 'all' ? '#0f172a' : '#e2e8f0',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  📋 All
                </button>
                <button
                  onClick={() => {
                    setJobsFilterStatus('published');
                    setJobsDisplayCount(5);
                  }}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    background: jobsFilterStatus === 'published' ? '#10b981' : 'rgba(255,255,255,0.1)',
                    color: jobsFilterStatus === 'published' ? '#0f172a' : '#e2e8f0',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  ✅ Published
                </button>
                <button
                  onClick={() => {
                    setJobsFilterStatus('draft');
                    setJobsDisplayCount(5);
                  }}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    background: jobsFilterStatus === 'draft' ? '#f59e0b' : 'rgba(255,255,255,0.1)',
                    color: jobsFilterStatus === 'draft' ? '#0f172a' : '#e2e8f0',
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                  }}
                >
                  📝 Draft
                </button>
              </div>
              
              {jobsLoading ? (
                <p style={{ color: '#64748b', textAlign: 'center' }}>Loading jobs...</p>
              ) : allJobs.length === 0 ? (
                <p style={{ color: '#64748b', textAlign: 'center' }}>No jobs created yet</p>
              ) : (
                <>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '500px', overflowY: 'auto' }}>
                    {allJobs.slice(0, jobsDisplayCount).map((j) => (
                      <div key={j.job_id} style={{ padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <p style={{ color: '#fff', margin: '0 0 4px 0', fontWeight: 500 }}>{j.title}</p>
                          <p style={{ color: '#64748b', margin: 0, fontSize: '0.8rem' }}>Status: {j.status || 'Draft'}</p>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          {j.status !== 'published' && (
                            <button
                              onClick={() => publishJobFromList(j.job_id, j.title)}
                              disabled={processingJobId === j.job_id}
                              style={{
                                padding: '6px 12px',
                                borderRadius: '6px',
                                border: 'none',
                                background: processingJobId === j.job_id ? '#475569' : 'rgba(16,185,129,0.2)',
                                color: processingJobId === j.job_id ? '#94a3b8' : '#10b981',
                                fontSize: '0.85rem',
                                fontWeight: 600,
                                cursor: 'pointer'
                              }}
                            >
                              {processingJobId === j.job_id ? '⏳' : '📤 Publish'}
                            </button>
                          )}
                          <button
                            onClick={() => setShowDeleteConfirm(j.job_id)}
                            style={{
                              padding: '6px 12px',
                              borderRadius: '6px',
                              border: 'none',
                              background: 'rgba(239,68,68,0.2)',
                              color: '#ef4444',
                              fontSize: '0.85rem',
                              fontWeight: 600,
                              cursor: 'pointer'
                            }}
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Show More Button */}
                  {jobsDisplayCount < allJobs.length && (
                    <button
                      onClick={() => setJobsDisplayCount(prev => Math.min(prev + 5, allJobs.length))}
                      style={{
                        width: '100%',
                        marginTop: '16px',
                        padding: '12px',
                        borderRadius: '8px',
                        border: 'none',
                        background: 'rgba(34,211,238,0.2)',
                        color: '#22d3ee',
                        fontWeight: 600,
                        cursor: 'pointer',
                        fontSize: '0.95rem'
                      }}
                    >
                      📂 Show More ({jobsDisplayCount} of {allJobs.length})
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
