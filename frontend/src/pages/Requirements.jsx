import { useState, useEffect, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Trash2, Clock, Search, User, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { endpoints, API_BASE } from '../api';

export default function Requirements() {
  const navigate = useNavigate();
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [requirements, setRequirements] = useState([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedReq, setSelectedReq] = useState(null);
  const [matches, setMatches] = useState([]);
  const [matching, setMatching] = useState(false);
  
  const inputRef = useRef(null);

  useEffect(() => {
    fetchRequirements();
  }, []);

  const fetchRequirements = async () => {
    try {
      const res = await fetch(endpoints.requirements);
      const data = await res.json();
      setRequirements(data || []);
    } catch (err) {
      console.error('Failed to fetch requirements:', err);
    } finally {
      setFetching(false);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (uploadedFile) => {
    setError('');
    setSuccess('');
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ];
    // Check type or extension for txt
    if (!allowedTypes.includes(uploadedFile.type) && !uploadedFile.name.toLowerCase().endsWith('.txt')) {
      setError('Please upload a PDF, DOCX, or TXT file.');
      return;
    }
    setFile(uploadedFile);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(endpoints.uploadRequirement, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setSuccess('Job requirement uploaded and indexed successfully!');
      setFile(null);
      fetchRequirements();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const findMatches = async (req) => {
    setSelectedReq(req);
    setMatching(true);
    setMatches([]);
    try {
      const res = await fetch(`${API_BASE}/api/requirements/${req._id}/matches`);
      const data = await res.json();
      setMatches(data || []);
    } catch (err) {
      console.error('Failed to find matches:', err);
    } finally {
      setMatching(false);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this job requirement? This will permanently remove its indexing.')) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/requirements/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete requirement');
      setSuccess('Requirement deleted successfully');
      fetchRequirements();
      if (selectedReq?._id === id) setSelectedReq(null);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <header style={{ marginBottom: '40px' }}>
        <h1 style={{ textAlign: 'left', background: 'none', WebkitTextFillColor: 'inherit' }}>Job Requirements</h1>
        <p className="subtitle" style={{ textAlign: 'left', marginBottom: 0 }}>
          Upload and manage job descriptions for AI-powered candidate matching.
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) minmax(300px, 1fr)', gap: '32px' }}>
        {/* Upload Section */}
        <div className="glass-panel" style={{ height: 'fit-content', padding: '32px' }}>
          <h3 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Upload size={22} className="text-accent" /> Upload Requirement
          </h3>
          
          <div 
            className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => inputRef.current.click()}
            style={{ borderRadius: '20px', padding: '40px 20px' }}
          >
            <input 
              ref={inputRef} 
              type="file" 
              className="file-input" 
              onChange={handleChange} 
              accept=".pdf,.docx,.txt" 
            />
            <FileText size={48} style={{ color: 'var(--accent)', marginBottom: '16px' }} />
            <p style={{ fontWeight: 600, color: 'var(--text-main)' }}>PDF, DOCX, or TXT</p>
            <p className="subtitle" style={{ fontSize: '0.85rem', marginTop: '8px' }}>
              Drag & drop or Click to browse
            </p>
          </div>

          {file && (
            <div className="file-preview" style={{ marginTop: '24px', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.1)' }}>
              <div className="file-info" style={{ overflow: 'hidden' }}>
                <FileText size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                <span className="file-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {file.name}
                </span>
              </div>
              <Trash2 
                size={18} 
                style={{ cursor: 'pointer', color: 'var(--text-muted)', flexShrink: 0 }} 
                onClick={(e) => { e.stopPropagation(); setFile(null); }} 
              />
            </div>
          )}

          {error && (
            <div className="status-error" style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' }}>
              <AlertCircle size={18} /> {error}
            </div>
          )}
          
          {success && (
            <div className="status-success" style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' }}>
              <CheckCircle size={18} /> {success}
            </div>
          )}

          <button 
            className="btn-primary" 
            onClick={(e) => { e.stopPropagation(); handleSubmit(); }} 
            disabled={!file || loading} 
            style={{ marginTop: '24px' }}
          >
            {loading ? <><span className="loader"></span> Indexing...</> : 'Process & Upload'}
          </button>
        </div>

        {/* List Section */}
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h3 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Clock size={22} className="text-muted" /> Active Requirements
          </h3>

          {fetching ? (
            <div style={{ textAlign: 'center', padding: '60px' }}>
              <span className="loader" style={{ width: '30px', height: '30px' }}></span>
            </div>
          ) : requirements.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.02)', borderRadius: '20px' }}>
              <FileText size={40} style={{ opacity: 0.2, marginBottom: '16px' }} />
              <p>No job requirements uploaded yet.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {requirements.map((req) => (
                <div 
                  key={req._id} 
                  style={{ 
                    padding: '20px', 
                    background: 'rgba(255,255,255,0.03)', 
                    borderRadius: '16px', 
                    border: '1px solid var(--glass-border)', 
                    display: 'flex', 
                    gap: '12px',
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                  onClick={() => findMatches(req)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateX(4px)';
                    e.currentTarget.style.borderColor = 'var(--accent)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateX(0)';
                    e.currentTarget.style.borderColor = 'var(--glass-border)';
                  }}
                >
                  <div style={{ overflow: 'hidden', flex: 1 }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>{req.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <FileText size={12} /> {req.filename}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <button 
                      className="btn-pill" 
                      style={{ fontSize: '0.75rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
                    >
                      <Search size={14} /> Find Matches
                    </button>
                    <button 
                      onClick={(e) => handleDelete(e, req._id)}
                      style={{ 
                        background: 'rgba(239, 68, 68, 0.1)', 
                        border: 'none', 
                        color: 'var(--error)', 
                        padding: '8px', 
                        borderRadius: '10px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center'
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {selectedReq && (
        <div className="glass-panel" style={{ marginTop: '32px', padding: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Search size={22} className="text-accent" /> Top Talent Matches for: {selectedReq.title}
            </h3>
            <button className="btn-pill" onClick={() => setSelectedReq(null)}>Close Results</button>
          </div>

          {matching ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <span className="loader"></span> Identifying Semantic Matches...
            </div>
          ) : matches.length === 0 ? (
            <p className="subtitle">No candidates found matching this role's profile yet.</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
              {matches.map((match) => (
                <div key={match.id} className="glass-panel" style={{ padding: '20px', background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <User size={18} className="text-accent" />
                      <span style={{ fontWeight: 600 }}>{match.name}</span>
                    </div>
                    <span className={`badge badge-${match.status}`} style={{ fontSize: '0.7rem' }}>{match.status}</span>
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '4px' }}>
                    {match.match_percentage}% Match
                  </div>
                  <div className="subtitle" style={{ fontSize: '0.8rem', marginBottom: '16px' }}>
                    {match.final_decision === 'selected' ? 'Previously Selected' : 'Available in Talent Pool'}
                  </div>
                  <button 
                    className="btn-primary" 
                    style={{ width: '100%', padding: '8px', fontSize: '0.9rem' }}
                    onClick={() => navigate(`/candidates/${match.id}`)}
                  >
                    <ExternalLink size={14} style={{ marginRight: '6px' }} /> View Profile
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
