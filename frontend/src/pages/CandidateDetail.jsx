import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { User, Mail, Briefcase, Award, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';

export default function CandidateDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);

  useEffect(() => {
    async function fetchCandidate() {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/candidates/${id}`);
        const data = await res.json();
        setCandidate(data);
      } catch (err) {
        console.error('Failed to fetch candidate details:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchCandidate();
  }, [id]);

  const handleDecision = async (decision) => {
    setReviewing(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/candidates/${id}/decision`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reason: 'Manual HR Review' })
      });
      if (res.ok) {
        const updated = await res.json();
        alert(`Candidate ${decision} successfully!`);
        navigate('/'); // Go back to dashboard
      }
    } catch (err) {
      console.error('Decision update failed:', err);
    } finally {
      setReviewing(false);
    }
  };

  if (loading) return <div className="loader"></div>;
  if (!candidate) return <div>Candidate not found</div>;

  const data = candidate.parsed_data || {};

  return (
    <div>
      <div className="detail-header">
        <button onClick={() => navigate(-1)} className="nav-item" style={{ border: 'none', background: 'none', cursor: 'pointer' }}>
          <ArrowLeft size={20} />
          Back to Dashboard
        </button>

        <div className="action-buttons">
          <button 
            className="btn-pill btn-reject" 
            onClick={() => handleDecision('rejected')} 
            disabled={reviewing}
          >
            {reviewing ? 'Processing...' : 'Reject Application'}
          </button>
          <button 
            className="btn-pill btn-approve" 
            onClick={() => handleDecision('selected')} 
            disabled={reviewing}
          >
            {reviewing ? 'Processing...' : 'Approve Candidate'}
          </button>
        </div>
      </div>

      <div className="detail-grid">
        <section className="glass-panel" style={{ width: '100%', maxWidth: 'none' }}>
          <div className="info-section">
            <h2 style={{ fontSize: '2rem', marginBottom: '8px' }}>{data.name}</h2>
            <div style={{ display: 'flex', gap: '20px', color: 'var(--text-muted)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Mail size={16} /> {data.email}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Briefcase size={16} /> {candidate.status}
              </span>
            </div>
          </div>

          <div className="info-section" style={{ marginTop: '40px' }}>
            <h3 className="section-title"><Award size={18} /> Professional Skills</h3>
            <div className="skills-tags">
              {(data.skills || []).map((skill, i) => (
                <span key={i} className="skill-tag">{skill}</span>
              ))}
            </div>
          </div>

          <div className="info-section">
            <h3 className="section-title"><Briefcase size={18} /> Project Experience</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {(data.projects || []).map((project, i) => (
                <div key={i} className="glass-panel" style={{ padding: '16px', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)' }}>
                  {project}
                </div>
              ))}
            </div>
          </div>
        </section>

        <aside className="glass-panel" style={{ height: 'fit-content' }}>
          <h3 className="section-title"><Zap size={18} /> AI Evaluation</h3>
          
          <div style={{ textAlign: 'center', margin: '32px 0' }}>
            <div className="score-circle" style={{ width: '80px', height: '80px', fontSize: '1.5rem', margin: '0 auto 16px', borderColor: 'var(--accent)' }}>
              {candidate.match_score || 0}
            </div>
            <p style={{ fontWeight: 600 }}>Overall Match Score</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Technical Depth</span>
              <span style={{ color: 'var(--success)' }}>High</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Skill Overlap</span>
              <span style={{ color: 'var(--accent-hover)' }}>85%</span>
            </div>
          </div>

          <div style={{ marginTop: '24px', padding: '16px', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.1)' }}>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px' }}>AI RECOMMENDATION</p>
            <p style={{ fontSize: '0.9rem', lineHeight: '1.5' }}>
              Candidate shows strong proficiency in core tech stack. Recommendation: <strong>Proceed to Interview</strong>.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

// Helper icons imported from lucide-react above
const Zap = ({ size, ...props }) => <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" /></svg>;
