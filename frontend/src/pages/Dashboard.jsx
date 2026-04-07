import { useState, useEffect } from 'react';
import { User, Mail, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { endpoints } from '../api';

export default function Dashboard() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div className="loader" style={{ width: '40px', height: '40px' }}></div>
      </div>
    );
  }

  return (
    <div>
      <header style={{ marginBottom: '48px' }}>
        <h1 style={{ textAlign: 'left', background: 'none', WebkitTextFillColor: 'inherit' }}>
          Talent Dashboard
        </h1>
        <p className="subtitle" style={{ textAlign: 'left', marginBottom: 0 }}>
          Manage and review all AI-extracted candidate profiles.
        </p>
      </header>
      
      <div className="dashboard-grid">
        {candidates.map((candidate) => (
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
                <span style={{ fontSize: '0.8rem' }}>{candidate.parsed_data?.email || 'N/A'}</span>
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
      
      {candidates.length === 0 && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px' }}>
          <User size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
          <h3>No candidates found</h3>
          <p className="subtitle">Upload a resume to start building your talent pool.</p>
          <Link to="/upload" className="btn-primary" style={{ display: 'inline-block', maxWidth: '200px', textDecoration: 'none' }}>
            Upload Now
          </Link>
        </div>
      )}
    </div>
  );
}
