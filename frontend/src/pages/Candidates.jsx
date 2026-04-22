import React, { useState, useRef } from 'react';
import { AlertCircle, CheckCircle, Upload } from 'lucide-react';

export default function Candidates() {
  const [candidateName, setCandidateName] = useState('');
  const [candidateCV, setCandidateCV] = useState(null);
  const [candidateDragActive, setCandidateDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analyzingCandidate, setAnalyzingCandidate] = useState(null);
  const [allCandidates, setAllCandidates] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileInputRef = useRef(null);

  // Clear messages after 5 seconds
  React.useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError('');
        setSuccess('');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setCandidateDragActive(true);
    else if (e.type === 'dragleave' || e.type === 'drop') setCandidateDragActive(false);
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(file.type)) {
      setError('❌ Please upload PDF, DOCX, or TXT file');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('❌ File size must be less than 5MB');
      return;
    }
    setCandidateCV(file);
    setSuccess(`✓ ${file.name} selected`);
    setError('');
  };

  const handleUpload = async () => {
    if (!candidateName.trim()) {
      setError('❌ Please enter candidate name');
      return;
    }
    if (!candidateCV) {
      setError('❌ Please select a CV file');
      return;
    }

    setError('');
    setSuccess('');
    
    const formData = new FormData();
    formData.append('file', candidateCV);
    formData.append('candidate_name', candidateName);

    // Simulate progress
    setUploadProgress(20);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/candidates/upload-resume', {
        method: 'POST',
        body: formData
      });

      setUploadProgress(70);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({detail: 'Upload failed'}));
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setUploadProgress(100);
      
      setAllCandidates([...allCandidates, data]);
      setSuccess(`✓ CV uploaded successfully for ${candidateName}!`);
      setCandidateName('');
      setCandidateCV(null);
      
      setTimeout(() => setUploadProgress(0), 1500);
    } catch (err) {
      setUploadProgress(0);
      setError(`❌ ${err.message}`);
    }
  };

  const handleAnalyze = async (candidateId, candidateName) => {
    setAnalyzingCandidate(candidateId);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/candidates/${candidateId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) throw new Error('Analysis failed');
      
      const result = await response.json();
      setSuccess(`✓ Resume analyzed! Score: ${result.overall_score || 'N/A'}`);
      
      // Update candidate in list
      setAllCandidates(prev => prev.map(c => c.candidate_id === candidateId ? {...c, analysis: result} : c));
    } catch (err) {
      setError(`❌ Failed to analyze resume: ${err.message}`);
    } finally {
      setAnalyzingCandidate(null);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%', padding: '20px' }}>
      <header style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '8px', color: 'white' }}>👥 Candidates</h1>
        <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.7)' }}>Upload and analyze candidate CVs</p>
      </header>

      {/* Messages */}
      {error && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '6px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#ef4444',
          marginBottom: '16px',
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          animation: 'slideUp 0.3s ease-out'
        }}>
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {success && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '6px',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#10b981',
          marginBottom: '16px',
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          animation: 'slideUp 0.3s ease-out'
        }}>
          <CheckCircle size={18} />
          {success}
        </div>
      )}

      {/* Upload Card */}
      <div style={{
        background: 'rgba(59, 130, 246, 0.08)',
        padding: '24px',
        borderRadius: '8px',
        border: '1px solid rgba(59, 130, 246, 0.2)',
        marginBottom: '32px'
      }}>
        <h3 style={{ margin: '0 0 16px 0', color: 'white', fontSize: '1.1rem' }}>📄 Add Candidate CV</h3>
        
        {/* Name Input */}
        <input
          type="text"
          placeholder="Candidate Name (e.g., John Smith)"
          value={candidateName}
          onChange={(e) => setCandidateName(e.target.value)}
          style={{
            width: '100%',
            padding: '12px',
            marginBottom: '16px',
            background: 'rgba(0,0,0,0.3)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '6px',
            color: 'white',
            fontSize: '0.95rem',
            outline: 'none',
            boxSizing: 'border-box'
          }}
        />

        {/* Drag & Drop Area */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={(e) => {
            handleDrag(e);
            handleFileSelect(e.dataTransfer.files[0]);
          }}
          onClick={() => fileInputRef.current?.click()}
          style={{
            padding: '32px 24px',
            background: candidateDragActive ? 'rgba(59, 130, 246, 0.2)' : 'rgba(0,0,0,0.2)',
            border: `2px dashed ${candidateDragActive ? 'rgba(59, 130, 246, 0.8)' : 'rgba(59, 130, 246, 0.3)'}`,
            borderRadius: '8px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s',
            marginBottom: '16px'
          }}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>📑</div>
          <p style={{ margin: '0 0 4px 0', color: 'rgba(255,255,255,0.9)', fontSize: '0.95rem', fontWeight: 600 }}>Drag CV here or click to browse</p>
          <p style={{ margin: 0, color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem' }}>{candidateCV ? candidateCV.name : 'PDF, DOCX, or TXT (max 5MB)'}</p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          onChange={(e) => handleFileSelect(e.target.files?.[0])}
          accept=".pdf,.docx,.txt"
          style={{ display: 'none' }}
        />

        {/* Upload Progress */}
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div style={{ marginBottom: '16px', background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem', fontWeight: 600 }}>
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{
                width: `${uploadProgress}%`,
                height: '100%',
                background: 'linear-gradient(90deg, rgba(59, 130, 246, 0.8), rgba(59, 130, 246, 1))',
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!candidateName || !candidateCV}
          style={{
            width: '100%',
            padding: '12px 16px',
            background: !candidateName || !candidateCV ? 'rgba(107, 114, 128, 0.3)' : 'linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(59, 130, 246, 0.2))',
            border: '1px solid ' + (!candidateName || !candidateCV ? 'rgba(107, 114, 128, 0.3)' : 'rgba(59, 130, 246, 0.5)'),
            borderRadius: '6px',
            color: '#3b82f6',
            cursor: !candidateName || !candidateCV ? 'not-allowed' : 'pointer',
            fontSize: '0.95rem',
            fontWeight: 600,
            transition: 'all 0.2s',
            opacity: !candidateName || !candidateCV ? 0.5 : 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px'
          }}
          onMouseEnter={(e) => {
            if (candidateName && candidateCV) {
              e.currentTarget.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.4), rgba(59, 130, 246, 0.3))';
            }
          }}
          onMouseLeave={(e) => {
            if (candidateName && candidateCV) {
              e.currentTarget.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(59, 130, 246, 0.2))';
            }
          }}
        >
          <Upload size={18} /> Upload & Analyze CV
        </button>
      </div>

      {/* Candidates List */}
      {allCandidates.length > 0 && (
        <div>
          <h3 style={{ color: 'white', marginBottom: '16px', fontSize: '1.1rem' }}>📋 Uploaded Candidates ({allCandidates.length})</h3>
          <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
            {allCandidates.map((candidate) => (
              <div
                key={candidate.candidate_id}
                style={{
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(59, 130, 246, 0.06))',
                  padding: '16px',
                  borderRadius: '8px',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 20px rgba(59, 130, 246, 0.15)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0, color: 'white', fontSize: '1rem' }}>{candidate.candidate_name}</h4>
                  {candidate.analysis && (
                    <span style={{
                      background: 'rgba(16, 185, 129, 0.2)',
                      color: '#10b981',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600
                    }}>
                      ✓ Analyzed
                    </span>
                  )}
                </div>
                
                {candidate.analysis ? (
                  <div style={{ fontSize: '0.9rem', color: 'rgba(255,255,255,0.8)', marginBottom: '12px' }}>
                    <p style={{ margin: '4px 0' }}>📊 Score: {candidate.analysis.overall_score || 'N/A'}</p>
                    <p style={{ margin: '4px 0', fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)' }}>Analysis: {candidate.analysis.summary || 'Ready for review'}</p>
                  </div>
                ) : (
                  <button
                    onClick={() => handleAnalyze(candidate.candidate_id, candidate.candidate_name)}
                    disabled={analyzingCandidate === candidate.candidate_id}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: analyzingCandidate === candidate.candidate_id ? 'rgba(59, 130, 246, 0.3)' : 'rgba(59, 130, 246, 0.15)',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      borderRadius: '4px',
                      color: '#3b82f6',
                      cursor: analyzingCandidate === candidate.candidate_id ? 'not-allowed' : 'pointer',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      if (analyzingCandidate !== candidate.candidate_id) {
                        e.currentTarget.style.background = 'rgba(59, 130, 246, 0.25)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(59, 130, 246, 0.15)';
                    }}
                  >
                    {analyzingCandidate === candidate.candidate_id ? '⏳ Analyzing...' : '🔍 Analyze Now'}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {allCandidates.length === 0 && !uploadProgress && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          background: 'rgba(0,0,0,0.2)',
          borderRadius: '8px',
          border: '1px dashed rgba(255,255,255,0.1)'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '12px', opacity: 0.5 }}>👤</div>
          <p style={{ color: 'rgba(255,255,255,0.6)', margin: 0 }}>No candidates yet. Upload a CV to get started!</p>
        </div>
      )}
    </div>
  );
}
