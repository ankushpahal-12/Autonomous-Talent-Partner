import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, RefreshCw, Search, ArrowRight, Zap, Code2, Briefcase, ExternalLink } from 'lucide-react';

const API = 'http://127.0.0.1:8000';

const styles = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  .spin {
    animation: spin 1s linear infinite;
  }
`;

export default function EnhanceCandidates() {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [enrichmentComplete, setEnrichmentComplete] = useState({});
  const [error, setError] = useState('');

  // Fetch all candidates
  const fetchCandidates = async () => {
    try {
      setLoading(true);
      setError('');
      const res = await fetch(`${API}/api/v1/candidates?page=1&page_size=100`);
      if (!res.ok) {
        throw new Error(`Failed to fetch candidates: ${res.status} ${res.statusText}`);
      }
      const data = await res.json();
      console.log('Fetched candidates:', data);
      
      if (data.status !== 'success') {
        throw new Error('Invalid response format from API');
      }
      
      const items = data.items || [];
      console.log(`Loaded ${items.length} candidates`);
      setCandidates(items);
      
      if (items.length === 0) {
        setError('No candidates found. Please upload candidate resumes first.');
      }
    } catch (err) {
      console.error('Error fetching candidates:', err);
      setError(`Failed to load candidates: ${err.message}`);
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, []);

  // Handle enrichment
  const handleEnrich = async (candidateId, candidateName) => {
    setEnriching(prev => ({ ...prev, [candidateId]: true }));
    setError('');
    
    try {
      const res = await fetch(`${API}/api/v1/candidates/${candidateId}/enrich`, {
        method: 'POST'
      });
      
      if (!res.ok) {
        throw new Error('Enrichment failed');
      }

      const result = await res.json();
      
      // Log enrichment result for debugging
      console.log(`Enrichment successful for ${candidateName}:`, result);
      
      // Mark as enriched and show success
      setEnrichmentComplete(prev => ({ ...prev, [candidateId]: true }));
      
      // Reset after 3 seconds
      setTimeout(() => {
        setEnriching(prev => {
          const newState = { ...prev };
          delete newState[candidateId];
          return newState;
        });
      }, 2000);

    } catch (err) {
      console.error('Enrichment error:', err);
      setError(`Failed to enrich ${candidateName}: ${err.message}`);
      setEnriching(prev => {
        const newState = { ...prev };
        delete newState[candidateId];
        return newState;
      });
    }
  };

  // Filter candidates based on search
  const filteredCandidates = candidates.filter(c =>
    (c.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.email || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ minHeight: '100vh', padding: '40px 20px', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}>
      <style>{styles}</style>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '40px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Sparkles size={32} style={{ color: '#22d3ee' }} />
              <h1 style={{ fontSize: '2.5rem', fontWeight: 700, margin: 0, background: 'linear-gradient(90deg, #fff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Enhance Candidates
              </h1>
            </div>
            <button
              onClick={fetchCandidates}
              disabled={loading}
              style={{
                padding: '10px 16px',
                borderRadius: '8px',
                border: 'none',
                background: 'rgba(34,211,238,0.2)',
                color: '#22d3ee',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                opacity: loading ? 0.6 : 1
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.background = 'rgba(34,211,238,0.3)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(34,211,238,0.2)';
              }}
            >
              <RefreshCw size={16} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              Refresh
            </button>
          </div>
          <p style={{ fontSize: '1rem', color: '#64748b', margin: '0 0 20px 0' }}>
            Enrich candidate profiles with external data from GitHub, LinkedIn, and web sources. Get deeper insights into candidate backgrounds and expertise.
          </p>
        </div>

        {/* Info Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px', marginBottom: '40px' }}>
          <div style={{ background: 'rgba(34,211,238,0.1)', border: '1px solid rgba(34,211,238,0.3)', borderRadius: '12px', padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <Code2 size={20} style={{ color: '#22d3ee' }} />
              <span style={{ fontWeight: 600, color: '#22d3ee' }}>GitHub Data</span>
            </div>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>Pull repositories, contributions, and technical expertise</p>
          </div>
          
          <div style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '12px', padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <Briefcase size={20} style={{ color: '#6366f1' }} />
              <span style={{ fontWeight: 600, color: '#6366f1' }}>LinkedIn Profile</span>
            </div>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>Verify experience, skills, and career history</p>
          </div>
          
          <div style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '12px', padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <ExternalLink size={20} style={{ color: '#10b981' }} />
              <span style={{ fontWeight: 600, color: '#10b981' }}>Web Research</span>
            </div>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>Deep web search for public profiles and mentions</p>
          </div>
        </div>

        {/* Search Bar */}
        <div style={{ marginBottom: '30px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={20} style={{ position: 'absolute', left: '12px', top: '12px', color: '#64748b' }} />
            <input
              type="text"
              placeholder="Search candidates by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                paddingLeft: '40px',
                padding: '12px 16px',
                borderRadius: '8px',
                border: '1px solid rgba(255,255,255,0.1)',
                background: 'rgba(15,23,42,0.8)',
                color: '#fff',
                fontSize: '0.95rem',
                boxSizing: 'border-box'
              }}
            />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div style={{ padding: '16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', color: '#ef4444', marginBottom: '20px' }}>
            {error}
          </div>
        )}

        {/* Candidates Grid */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <RefreshCw size={48} style={{ margin: '0 auto 20px', color: '#22d3ee', animation: 'spin 1s linear infinite' }} />
            <p style={{ color: '#64748b', fontSize: '1.1rem' }}>Loading candidates...</p>
          </div>
        ) : filteredCandidates.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <Sparkles size={48} style={{ margin: '0 auto 20px', color: '#64748b' }} />
            <p style={{ color: '#cbd5e1', fontSize: '1.1rem', marginBottom: '12px' }}>
              {searchQuery 
                ? '❌ No candidates match your search' 
                : candidates.length === 0
                ? '📋 No candidates available'
                : '✅ All candidates have been enriched'}
            </p>
            {searchQuery && (
              <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
                Try adjusting your search query or{' '}
                <button
                  onClick={() => setSearchQuery('')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#22d3ee',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    font: 'inherit',
                    fontSize: 'inherit'
                  }}
                >
                  clear the search
                </button>
              </p>
            )}
            {candidates.length === 0 && (
              <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '12px' }}>
                👉 Please upload candidate resumes on the <button
                  onClick={() => navigate('/dashboard')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#22d3ee',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    font: 'inherit',
                    fontSize: 'inherit'
                  }}
                >
                  Dashboard
                </button> page first
              </p>
            )}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {filteredCandidates.map((candidate, index) => (
              <div
                key={candidate.candidate_id || `candidate-${index}`}
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  padding: '20px',
                  transition: 'all 0.3s',
                  hover: { background: 'rgba(255,255,255,0.04)' }
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
                  e.currentTarget.style.borderColor = 'rgba(34,211,238,0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.02)';
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                }}
              >
                {/* Candidate Header */}
                <div style={{ marginBottom: '16px' }}>
                  <h3 style={{ margin: '0 0 4px 0', color: '#fff', fontSize: '1.1rem' }}>
                    {candidate.name || 'Unknown'}
                  </h3>
                  <p style={{ margin: '0 0 8px 0', color: '#64748b', fontSize: '0.9rem' }}>
                    {candidate.email || 'N/A'}
                  </p>
                </div>

                {/* Candidate Info */}
                <div style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                  {candidate.location && (
                    <p style={{ margin: '4px 0', color: '#cbd5e1', fontSize: '0.85rem' }}>
                      📍 {candidate.location}
                    </p>
                  )}
                  {candidate.phone && (
                    <p style={{ margin: '4px 0', color: '#cbd5e1', fontSize: '0.85rem' }}>
                      📞 {candidate.phone}
                    </p>
                  )}
                </div>

                {/* Score Display */}
                {candidate.aiScore !== undefined && (
                  <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(34,211,238,0.1)', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.85rem', color: '#64748b' }}>AI Score</span>
                      <span style={{ fontSize: '1.2rem', fontWeight: 700, color: '#22d3ee' }}>
                        {(candidate.aiScore || 0).toFixed(1)}/100
                      </span>
                    </div>
                    <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          background: 'linear-gradient(90deg, #22d3ee, #06b6d4)',
                          width: `${(candidate.aiScore || 0)}%`,
                          transition: 'width 0.3s'
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => handleEnrich(candidate.candidate_id, candidate.name)}
                    disabled={enriching[candidate.candidate_id] || enrichmentComplete[candidate.candidate_id]}
                    style={{
                      flex: 1,
                      padding: '10px 16px',
                      borderRadius: '8px',
                      border: 'none',
                      background: enrichmentComplete[candidate.candidate_id] ? 'rgba(16,185,129,0.2)' : (enriching[candidate.candidate_id] ? '#475569' : 'rgba(34,211,238,0.2)'),
                      color: enrichmentComplete[candidate.candidate_id] ? '#10b981' : (enriching[candidate.candidate_id] ? '#94a3b8' : '#22d3ee'),
                      fontWeight: 600,
                      fontSize: '0.9rem',
                      cursor: enriching[candidate.candidate_id] || enrichmentComplete[candidate.candidate_id] ? 'not-allowed' : 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px'
                    }}
                  >
                    {enrichmentComplete[candidate.candidate_id] ? (
                      <>✓ Enriched</>
                    ) : enriching[candidate.candidate_id] ? (
                      <>⏳ Enriching...</>
                    ) : (
                      <>
                        <Sparkles size={16} />
                        Enrich
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => navigate(`/candidates/${candidate.candidate_id}`)}
                    style={{
                      padding: '10px 16px',
                      borderRadius: '8px',
                      border: 'none',
                      background: 'rgba(255,255,255,0.05)',
                      color: '#cbd5e1',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                      e.currentTarget.style.color = '#fff';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                      e.currentTarget.style.color = '#cbd5e1';
                    }}
                  >
                    <ArrowRight size={16} />
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Stats Footer */}
        <div style={{ marginTop: '40px', padding: '20px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}>
          <p style={{ margin: '0', color: '#64748b', fontSize: '0.9rem' }}>
            Total candidates: <span style={{ fontWeight: 700, color: '#22d3ee' }}>{filteredCandidates.length}</span> |
            Showing: <span style={{ fontWeight: 700, color: '#22d3ee' }}>{filteredCandidates.filter(c => !enrichmentComplete[c.candidate_id]).length}</span> available for enrichment
          </p>
        </div>
      </div>
    </div>
  );
}
