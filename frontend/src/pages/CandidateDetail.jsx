import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { User, Mail, Phone, Briefcase, Award, ArrowLeft } from 'lucide-react';

const API = 'http://127.0.0.1:8000';

// Zap icon inline
const Zap = ({ size, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

/** Extracts the key fields from the report regardless of old vs new schema */
function parseReport(agentReports) {
  if (!agentReports) return null;

  // --- New schema (post LangChain upgrade) ---
  const fd = agentReports.final_decision;
  if (fd) {
    return {
      score: fd.final_score ?? 0,
      decision: fd.decision ?? 'N/A',
      explanation: fd.explanation ?? '',
      techFit: agentReports.tech?.tech_stack_match?.toUpperCase() ?? 'N/A',
      cultureFit: agentReports.culture?.culture_fit_score ?? 'N/A',
      rejectionFeedback: agentReports.rejection_feedback ?? null,
    };
  }

  // --- Old schema (pre LangChain upgrade, graceful fallback) ---
  const lead = agentReports.lead;
  if (lead) {
    return {
      score: lead.overall_match_score ?? 0,
      decision: lead.recommendation ?? 'N/A',
      explanation: lead.final_summary ?? '',
      techFit: agentReports.tech?.tech_stack_match?.toUpperCase() ?? 'N/A',
      cultureFit: agentReports.culture?.culture_fit_score ?? 'N/A',
      rejectionFeedback: null,
    };
  }

  return null;
}

export default function CandidateDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const [generatingAI, setGeneratingAI] = useState(false);
  const [actionError, setActionError] = useState('');
  const [activeTab, setActiveTab] = useState('tech');

  useEffect(() => {
    async function fetchCandidate() {
      try {
        const res = await fetch(`${API}/api/candidates/${id}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
    setActionError('');
    try {
      const res = await fetch(`${API}/api/candidates/${id}/decision`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reason: 'Manual HR Review' })
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'Decision update failed');
      setCandidate(prev => ({ ...prev, final_decision: decision, status: 'decided' }));
    } catch (err) {
      setActionError(err.message);
      console.error('Decision update failed:', err);
    } finally {
      setReviewing(false);
    }
  };

  const runAIReview = async () => {
    setGeneratingAI(true);
    setActionError('');
    try {
      const res = await fetch(`${API}/api/candidates/${id}/review`, { method: 'POST' });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'AI Review failed');
      setCandidate(prev => ({
        ...prev,
        agent_reports: result.report,
        match_score: result.report?.final_decision?.final_score ?? result.report?.lead?.overall_match_score ?? 0,
        status: 'ai_reviewed'
      }));
    } catch (err) {
      setActionError(err.message);
      console.error('AI Review failed:', err);
    } finally {
      setGeneratingAI(false);
    }
  };

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <div className="loader" style={{ width: '40px', height: '40px' }}></div>
    </div>
  );
  if (!candidate) return <div className="glass-panel" style={{ textAlign: 'center', padding: '60px' }}><p>Candidate not found.</p></div>;

  const data = candidate.parsed_data || {};
  const parsedReport = parseReport(candidate.agent_reports);
  const displayScore = parsedReport?.score ?? candidate.match_score ?? 0;

  return (
    <div>
      <div className="detail-header">
        <button onClick={() => navigate(-1)} className="nav-item" style={{ border: 'none', background: 'none', cursor: 'pointer' }}>
          <ArrowLeft size={20} />
          Back
        </button>

        <div className="action-buttons">
          <button
            className="btn-pill btn-reject"
            onClick={() => handleDecision('rejected')}
            disabled={reviewing || generatingAI || !parsedReport || displayScore < 60}
            title={!parsedReport ? "AI score required before decision" : displayScore < 60 ? "Auto-rejected by AI due to low score" : ""}
          >
            {reviewing ? 'Processing...' : 'Reject Application'}
          </button>
          <button
            className="btn-pill btn-approve"
            onClick={() => handleDecision('selected')}
            disabled={reviewing || generatingAI || !parsedReport || displayScore < 60}
            title={!parsedReport ? "AI score required before decision" : displayScore < 60 ? "Auto-rejected by AI due to low score" : ""}
          >
            {reviewing ? 'Processing...' : 'Approve Candidate'}
          </button>
        </div>
      </div>

      {actionError && (
        <div className="glass-panel" style={{ borderColor: 'var(--error)', marginBottom: '16px', padding: '12px 20px' }}>
          <p style={{ color: 'var(--error)', margin: 0, fontSize: '0.9rem' }}>⚠ {actionError}</p>
        </div>
      )}

      <div className="detail-grid">
        {/* Left: Candidate Profile */}
        <section className="glass-panel" style={{ width: '100%', maxWidth: 'none' }}>
          <div className="info-section">
            <h2 style={{ fontSize: '2rem', marginBottom: '8px' }}>{data.name || 'Unknown Candidate'}</h2>
            <div style={{ display: 'flex', gap: '20px', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
              {data.email && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Mail size={16} /> {data.email}
                </span>
              )}
              {data.phone && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Phone size={16} /> {data.phone}
                </span>
              )}
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
              {(!data.skills || data.skills.length === 0) && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No skills extracted.</p>
              )}
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
              {(!data.projects || data.projects.length === 0) && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No projects extracted.</p>
              )}
            </div>
          </div>
        </section>

        {/* Right: AI Evaluation */}
        {/* Right: AI Evaluation Overview */}
        <aside className="glass-panel" style={{ height: 'fit-content', padding: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h3 className="section-title" style={{ margin: 0 }}><Zap size={18} /> AI Overview</h3>
            {!parsedReport && (
              <button
                onClick={runAIReview}
                disabled={generatingAI}
                className="nav-item"
                style={{ fontSize: '0.75rem', padding: '4px 8px', background: 'rgba(59, 130, 246, 0.1)', cursor: 'pointer' }}
              >
                {generatingAI ? 'Analysing...' : 'Run Analysis'}
              </button>
            )}
          </div>

          <div style={{ textAlign: 'center', margin: '32px 0' }}>
            <div className="circular-progress" style={{ '--progress': `${displayScore * 3.6}deg` }}>
              <span className="circular-value">{displayScore}</span>
            </div>
            <p style={{ fontWeight: 600, marginTop: '16px' }}>Overall Match Score</p>
          </div>

          {parsedReport ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>TECH FIT</span>
                <span style={{ color: 'var(--success)' }}>{parsedReport.techFit}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>CULTURE</span>
                <span style={{ color: 'var(--accent-hover)' }}>{parsedReport.cultureFit}/10</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>DECISION</span>
                <span style={{ color: parsedReport.decision === 'hire' || parsedReport.decision === 'Hire' || parsedReport.decision === 'selected' ? 'var(--success)' : 'var(--error)', fontWeight: 600 }}>
                  {parsedReport.decision?.toUpperCase()}
                </span>
              </div>
              <div style={{ marginTop: '16px', padding: '12px', borderRadius: '12px', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.1)' }}>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '4px' }}>AI REASONING</p>
                <p style={{ fontSize: '0.85rem', lineHeight: '1.4' }}>{parsedReport.explanation}</p>
              </div>

              {parsedReport.rejectionFeedback && (
                <div style={{ marginTop: '12px', padding: '12px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                  <p style={{ fontSize: '0.7rem', color: 'var(--error)', marginBottom: '8px', fontWeight: 600 }}>REJECTION FEEDBACK</p>
                  {parsedReport.rejectionFeedback.missing_skills?.length > 0 && (
                    <p style={{ fontSize: '0.8rem', marginBottom: '4px' }}>
                      <strong>Missing Skills:</strong> {parsedReport.rejectionFeedback.missing_skills.join(', ')}
                    </p>
                  )}
                  {parsedReport.rejectionFeedback.suggestions && (
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      <strong>Suggestions:</strong> {parsedReport.rejectionFeedback.suggestions}
                    </p>
                  )}
                </div>
              )}

              <button
                onClick={runAIReview}
                disabled={generatingAI}
                className="nav-item"
                style={{ marginTop: '8px', fontSize: '0.75rem', padding: '6px 12px', background: 'rgba(59, 130, 246, 0.1)', cursor: 'pointer', textAlign: 'center', display: 'block', width: '100%' }}
              >
                {generatingAI ? 'Re-analysing...' : '↺ Re-run Analysis'}
              </button>
            </div>
          ) : (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center' }}>
              {generatingAI ? 'Running AI analysis...' : 'No AI analysis yet. Click the button above to start.'}
            </p>
          )}
        </aside>
      </div>

      {candidate?.agent_reports && (
        <div className="glass-panel" style={{ marginTop: '32px', maxWidth: 'none', padding: 0, overflow: 'hidden' }}>
          <div className="tabs-header">
            <button className={`tab-btn ${activeTab === 'tech' ? 'active' : ''}`} onClick={() => setActiveTab('tech')}>Technical Analytics</button>
            <button className={`tab-btn ${activeTab === 'culture' ? 'active' : ''}`} onClick={() => setActiveTab('culture')}>Cultural Assessment</button>
            <button className={`tab-btn ${activeTab === 'screener' ? 'active' : ''}`} onClick={() => setActiveTab('screener')}>Screener Quality</button>
            {(candidate.agent_reports.rag_reasoning || candidate.agent_reports.lead?.rag_reasoning) && (
                <button className={`tab-btn ${activeTab === 'rag' ? 'active' : ''}`} onClick={() => setActiveTab('rag')}>Graph Context</button>
            )}
          </div>
          
          <div className="tab-content" style={{ minHeight: '300px' }}>
             {activeTab === 'tech' && candidate.agent_reports.tech && (
                 <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                       <div className="stat-box">
                         <span className="stat-label">Stack Match</span>
                         <span className="stat-value" style={{ color: 'var(--success)' }}>{candidate.agent_reports.tech.tech_stack_match?.toUpperCase() || 'N/A'}</span>
                       </div>
                       <div className="stat-box">
                         <span className="stat-label">System Design</span>
                         <span className="stat-value">{candidate.agent_reports.tech.system_design_experience || 'N/A'}</span>
                       </div>
                       <div className="stat-box">
                         <span className="stat-label">Problem Solving</span>
                         <span className="stat-value">{candidate.agent_reports.tech.problem_solving_indicators || 'N/A'}</span>
                       </div>
                    </div>
                    <div>
                       <h4 style={{ marginBottom: '12px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>KEY TECHNOLOGIES FOUND</h4>
                       <div className="skills-tags">
                         {(candidate.agent_reports.tech.key_technologies_found || candidate.agent_reports.tech.key_technologies || []).map((t,i) => <span key={i} className="skill-tag" style={{ border: '1px solid var(--accent)' }}>{t}</span>)}
                       </div>
                    </div>
                    {candidate.agent_reports.tech.technical_red_flags?.length > 0 && (
                       <div style={{ background: 'rgba(239, 68, 68, 0.05)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                          <h4 style={{ color: 'var(--error)', marginBottom: '8px', fontSize: '0.9rem' }}>TECHNICAL RED FLAGS</h4>
                          <ul style={{ paddingLeft: '20px', fontSize: '0.85rem' }}>
                            {candidate.agent_reports.tech.technical_red_flags.map((rf,i) => <li key={i}>{rf}</li>)}
                          </ul>
                       </div>
                    )}
                 </div>
             )}
             
             {activeTab === 'culture' && candidate.agent_reports.culture && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                   <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                      <div className="circular-progress" style={{ '--progress': `${(candidate.agent_reports.culture.culture_fit_score || 0) * 36}deg`, width: '80px', height: '80px' }}>
                        <span className="circular-value" style={{ fontSize: '1.5rem' }}>{candidate.agent_reports.culture.culture_fit_score}/10</span>
                      </div>
                      <div>
                        <h3>Culture Fit Score</h3>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>Evaluated against company values and collaborative indicators.</p>
                      </div>
                   </div>
                   <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                     <div className="stat-box" style={{ borderColor: 'rgba(16, 185, 129, 0.2)', background: 'rgba(16, 185, 129, 0.05)' }}>
                       <span className="stat-label" style={{ color: 'var(--success)' }}>Positive Indicators</span>
                       <ul style={{ paddingLeft: '20px', fontSize: '0.85rem', marginTop: '8px' }}>
                         {(candidate.agent_reports.culture.pros || []).map((p,i) => <li key={i}>{p}</li>)}
                         {(!candidate.agent_reports.culture.pros || candidate.agent_reports.culture.pros.length === 0) && <li>None noted.</li>}
                       </ul>
                     </div>
                     <div className="stat-box" style={{ borderColor: 'rgba(245, 158, 11, 0.2)', background: 'rgba(245, 158, 11, 0.05)' }}>
                       <span className="stat-label" style={{ color: '#f59e0b' }}>Areas of Concern</span>
                       <ul style={{ paddingLeft: '20px', fontSize: '0.85rem', marginTop: '8px' }}>
                         {(candidate.agent_reports.culture.cons || candidate.agent_reports.culture.warning_signs || []).map((c,i) => <li key={i}>{c}</li>)}
                         {(!candidate.agent_reports.culture.cons && !candidate.agent_reports.culture.warning_signs) && <li>None noted.</li>}
                       </ul>
                     </div>
                   </div>
                </div>
             )}

             {activeTab === 'screener' && candidate.agent_reports.screener && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                     <div className="stat-box" style={{ flex: 'unset', width: '200px', alignItems: 'center' }}>
                       <div className="circular-progress" style={{ '--progress': `${(candidate.agent_reports.screener.grammar_and_formatting_score || 0) * 36}deg`, width: '60px', height: '60px' }}>
                          <span className="circular-value" style={{ fontSize: '1rem' }}>{candidate.agent_reports.screener.grammar_and_formatting_score}/10</span>
                       </div>
                       <span className="stat-label" style={{ marginTop: '12px', textAlign: 'center' }}>Grammar Score</span>
                     </div>
                     <div className="stat-box">
                       <span className="stat-label">Flow & Readability</span>
                       <span className="stat-value">{candidate.agent_reports.screener.flow_and_readability || 'N/A'}</span>
                     </div>
                     <div className="stat-box">
                       <span className="stat-label">Action Verbs Usage</span>
                       <span className="stat-value">{candidate.agent_reports.screener.action_verbs_usage || 'N/A'}</span>
                     </div>
                  </div>
                  {candidate.agent_reports.screener.red_flags_or_gaps?.length > 0 && (
                     <div style={{ background: 'rgba(245, 158, 11, 0.05)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                        <h4 style={{ color: '#f59e0b', marginBottom: '8px', fontSize: '0.9rem' }}>RESUME GAPS OR FLAGS</h4>
                        <ul style={{ paddingLeft: '20px', fontSize: '0.85rem' }}>
                          {candidate.agent_reports.screener.red_flags_or_gaps.map((rf,i) => <li key={i}>{rf}</li>)}
                        </ul>
                     </div>
                  )}
                </div>
             )}

             {activeTab === 'rag' && (candidate.agent_reports.rag_reasoning || candidate.agent_reports.lead?.rag_reasoning) && (
                <div style={{ padding: '24px', borderRadius: '12px', background: 'rgba(139, 92, 246, 0.05)', border: '1px solid rgba(139, 92, 246, 0.15)' }}>
                  <p style={{ fontSize: '0.85rem', color: '#a78bfa', marginBottom: '16px', fontWeight: 600, letterSpacing: '1px' }}>📄 RETRIEVED GRAPH & VECTOR KNOWLEDGE</p>
                  <p style={{ fontSize: '1rem', lineHeight: '1.7', color: 'var(--text-main)', whiteSpace: 'pre-wrap' }}>
                    {candidate.agent_reports.rag_reasoning || candidate.agent_reports.lead?.rag_reasoning}
                  </p>
                </div>
             )}
          </div>
        </div>
      )}
    </div>
  );
}
