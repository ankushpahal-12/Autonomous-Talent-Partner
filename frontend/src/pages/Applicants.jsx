import { useState, useEffect, useRef } from 'react';
import { Search, Mail, User, ArrowRight, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { endpoints } from '../api';

export default function Applicants() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    async function fetchCandidates() {
      try {
        const res = await fetch(endpoints.candidates);
        const data = await res.json();
        setCandidates(data);
      } catch (err) {
        console.error('Failed to fetch candidates:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchCandidates();
  }, []);

  useEffect(() => {
    if (isSearchOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isSearchOpen]);

  const filteredCandidates = candidates.filter((candidate) => {
    const name = candidate.parsed_data?.name?.toLowerCase() || '';
    const email = candidate.parsed_data?.email?.toLowerCase() || '';
    // Also search in skills
    const skills = (candidate.parsed_data?.skills || []).join(' ').toLowerCase();
    const query = searchQuery.toLowerCase();
    return name.includes(query) || email.includes(query) || skills.includes(query);
  });

  const toggleSearch = () => {
    setIsSearchOpen(!isSearchOpen);
    if (isSearchOpen) setSearchQuery('');
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div className="loader" style={{ width: '40px', height: '40px' }}></div>
      </div>
    );
  }

  return (
    <div>
      <header style={{ marginBottom: '48px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '20px' }}>
        <div>
          <h1 style={{ textAlign: 'left', background: 'none', WebkitTextFillColor: 'inherit' }}>
            Applicants
          </h1>
          <p className="subtitle" style={{ textAlign: 'left', marginBottom: 0 }}>
            List of all candidates who have applied for positions.
          </p>
        </div>
        
        <div className="search-container">
          <div className={`search-wrapper ${isSearchOpen ? 'open' : ''}`}>
            <button className="search-icon-btn" onClick={toggleSearch} title="Search Applicants">
              {isSearchOpen ? <X size={20} /> : <Search size={20} />}
            </button>
            <input
              ref={inputRef}
              type="text"
              className="search-input"
              placeholder="Search applicants..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </header>

      <div className="dashboard-grid">
        {filteredCandidates.map((candidate) => (
          <div key={candidate._id} className="glass-panel candidate-card">
            <div className="card-header">
              <div className="candidate-name">{candidate.parsed_data?.name || 'Anonymous'}</div>
              <span className={`badge badge-${candidate.status}`}>
                {candidate.status}
              </span>
            </div>

            <div className="card-stats">
              <div className="stat-item">
                <Mail size={14} />
                <span style={{ fontSize: '0.8rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {candidate.parsed_data?.email || 'N/A'}
                </span>
              </div>
            </div>

            <div className="skills-tags">
              {(candidate.parsed_data?.skills || []).slice(0, 3).map((skill, i) => (
                <span key={i} className="skill-tag">{skill}</span>
              ))}
              {(candidate.parsed_data?.skills?.length > 3) && (
                <span className="skill-tag" style={{ border: 'none', background: 'none' }}>+ {candidate.parsed_data.skills.length - 3} more</span>
              )}
            </div>

            <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '16px', borderTop: '1px solid var(--glass-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className="score-circle">
                  {candidate.match_score || 0}
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Match Score</span>
              </div>

              <Link to={`/candidates/${candidate._id}`} className="nav-item" style={{ padding: '8px', color: 'var(--accent-hover)' }}>
                <ArrowRight size={20} />
              </Link>
            </div>
          </div>
        ))}
      </div>

      {filteredCandidates.length === 0 && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px', maxWidth: '100%', marginTop: '32px' }}>
          <User size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
          <h3>{searchQuery ? 'No applicants match your search' : 'No applicants found'}</h3>
          <p className="subtitle">
            {searchQuery ? 'Try adjusting your search query or check for typos.' : 'Upload a resume to start building your applicant list.'}
          </p>
          {!searchQuery && (
            <Link to="/upload" className="btn-primary" style={{ display: 'inline-block', maxWidth: '200px', textDecoration: 'none' }}>
              Upload Now
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
