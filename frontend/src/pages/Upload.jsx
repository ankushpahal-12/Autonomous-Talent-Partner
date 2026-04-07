import { useState, useRef } from 'react';
import { endpoints } from '../api';

export default function Upload() {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');
  
  const inputRef = useRef(null);

  // Handle Drag Events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  // Handle File Drop
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  // Handle Input Change
  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  // Validate and set file
  const handleFile = (uploadedFile) => {
    setError('');
    setResponse(null);
    
    if (uploadedFile.type !== 'application/pdf') {
      setError('Please upload a valid PDF document.');
      return;
    }
    setFile(uploadedFile);
  };

  // Trigger file input
  const onButtonClick = () => {
    inputRef.current.click();
  };

  // Format file size
  const formatBytes = (bytes, decimals = 2) => {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
  };

  // Submit to Backend
  const handleSubmit = async () => {
    if (!file) return;
    
    setLoading(true);
    setError('');
    setResponse(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Assuming FastAPI runs on 8000
      const res = await fetch(endpoints.uploadResume, {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed');
      }
      
      setResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel">
      <h1>Autonomous Hub</h1>
      <p className="subtitle">Upload a candidate resume to begin agentic screening.</p>
      
      <form onDragEnter={handleDrag} onSubmit={(e) => e.preventDefault()}>
        <input 
          ref={inputRef} 
          type="file" 
          className="file-input" 
          accept="application/pdf"
          onChange={handleChange} 
        />
        
        <div 
          className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={onButtonClick}
        >
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p>Drag and drop your PDF here, or <span className="browse-text">browse files</span></p>
        </div>
      </form>

      {file && (
        <div className="file-preview">
          <div className="file-info">
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{color: '#10b981'}}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <div className="file-name">{file.name}</div>
              <div className="file-size">{formatBytes(file.size)}</div>
            </div>
          </div>
          {!loading && (
            <svg onClick={() => setFile(null)} style={{cursor: 'pointer', color: 'var(--text-muted)'}} width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          )}
        </div>
      )}

      {error && (
        <div className="response-area" style={{ borderColor: 'var(--error)' }}>
          <div className="response-status status-error">
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Error Processing Resume
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{error}</p>
        </div>
      )}

      {response && (
        <div className="response-area" style={{ borderColor: 'var(--success)' }}>
          <div className="response-status status-success">
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Pipeline Complete!
          </div>
          <div className="code-block">
            {typeof response.data === 'string' ? response.data : JSON.stringify(response.data, null, 2)}
          </div>
        </div>
      )}

      <button 
        className="btn-primary" 
        onClick={handleSubmit} 
        disabled={!file || loading}
      >
        {loading ? (
          <><span className="loader"></span> Autonomous Parsing...</>
        ) : (
          'Analyze Candidate'
        )}
      </button>
    </div>
  );
}
