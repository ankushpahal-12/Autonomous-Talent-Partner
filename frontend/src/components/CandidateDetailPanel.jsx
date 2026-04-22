import { memo, useState } from 'react';
import {
  User, Mail, Sparkles, CheckCircle, XCircle, Brain,
  TrendingUp, Code2, FlaskConical, Dna, ChevronRight,
  Award, Zap, Star, Target, Download, Share2,
} from 'lucide-react';
import ScoreBreakdown from './ScoreBreakdown';
import Neo4jInsights from './Neo4jInsights';
import RiskAssessmentChart from './RiskAssessmentChart';

// ── Helpers ───────────────────────────────────────────────────────────────────
function ScoreBar({ label, value, color, icon: Icon }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div 
      style={{ marginBottom: '16px' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', marginBottom: '8px',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '7px',
          fontSize: '0.82rem', fontWeight: 600,
          transition: 'color 0.2s ease',
          color: hovered ? color : 'var(--text-muted)',
        }}>
          {Icon && <Icon size={13} style={{ color, transition: 'transform 0.2s ease', transform: hovered ? 'scale(1.2) rotate(10deg)' : 'scale(1)' }} />}
          {label}
        </div>
        <span style={{
          fontSize: '0.88rem', fontWeight: 700,
          color, textShadow: `0 0 8px ${color}66`,
          transform: hovered ? 'scale(1.15)' : 'scale(1)',
          transition: 'transform 0.2s ease',
        }}>
          {value}%
        </span>
      </div>
      <div style={{
        width: '100%', height: '7px',
        background: 'rgba(255,255,255,0.05)',
        borderRadius: '6px', overflow: 'hidden',
        boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.4)',
        transition: 'all 0.3s ease',
        opacity: hovered ? 1 : 0.8,
      }}>
        <div style={{
          height: '100%',
          width: `${value}%`,
          background: `linear-gradient(90deg, ${color}99, ${color})`,
          borderRadius: '6px',
          boxShadow: `0 0 10px ${color}55`,
          transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
          filter: hovered ? `drop-shadow(0 0 8px ${color})` : 'none',
        }} />
      </div>
    </div>
  );
}

function SkillTag({ skill, variant = 'default', idx = 0 }) {
  const [hovered, setHovered] = useState(false);
  
  const styles = {
    default: {
      background: 'rgba(255,255,255,0.04)',
      border: '1px solid rgba(255,255,255,0.1)',
      color: 'var(--text-muted)',
    },
    accent: {
      background: 'rgba(34,211,238,0.08)',
      border: '1px solid rgba(34,211,238,0.2)',
      color: 'var(--neon-cyan)',
    },
  };
  
  return (
    <span 
      style={{
        ...styles[variant],
        padding: '6px 14px',
        borderRadius: '8px',
        fontSize: '0.76rem',
        fontWeight: 600,
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
        transform: hovered ? 'translateY(-3px) scale(1.05)' : 'translateY(0)',
        boxShadow: hovered ? `0 8px 16px ${variant === 'accent' ? 'rgba(34,211,238,0.2)' : 'rgba(0,0,0,0.2)'}` : 'none',
        opacity: hovered ? 1 : 0.9,
        animation: `slideUp 0.4s ease-out ${idx * 0.05}s backwards`,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {hovered && <span style={{ marginRight: '6px' }}>✓</span>}
      {skill}
    </span>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
const CandidateDetailPanel = memo(({
  candidate,
  actionLoading,
  actionFeedback,
  onShortlist,
  onReject,
}) => {
  const [showInsights, setShowInsights] = useState(false);

  if (!candidate) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        gap: '20px',
        color: 'var(--text-muted)',
      }}>
        {/* Animated orb */}
        <div style={{
          width: '100px', height: '100px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(34,211,238,0.12) 0%, transparent 70%)',
          border: '1px solid rgba(34,211,238,0.15)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        }}>
          <User size={40} style={{ color: 'rgba(34,211,238,0.4)', animation: 'float 3s ease-in-out infinite' }} />
        </div>
        <div style={{ textAlign: 'center', animation: 'fadeIn 0.6s ease-out' }}>
          <p style={{
            fontSize: '1.15rem', fontWeight: 600,
            color: 'rgba(255,255,255,0.4)', marginBottom: '8px',
          }}>
            Select a candidate to view details
          </p>
          <p style={{ fontSize: '0.82rem', color: 'rgba(148,163,184,0.45)' }}>
            Click any card on the left to inspect full AI evaluation
          </p>
        </div>
        <ChevronRight
          size={20}
          style={{
            color: 'rgba(34,211,238,0.2)',
            transform: 'rotate(180deg)',
            animation: 'bounce 2s ease-in-out infinite',
          }}
        />
      </div>
    );
  }

  const { name, email, role, status, aiScore, skills, breakdown, aiSummary } = candidate;
  const isShortlisted = status === 'Shortlisted';
  const isRejected = status === 'Rejected';

  // Score colour helpers
  const scoreColor = s => s >= 80 ? 'var(--neon-cyan)' : s >= 60 ? 'var(--neon-amber)' : '#f43f5e';

  return (
    <div
      key={candidate.id}
      style={{
        height: '100%',
        overflowY: 'auto',
        padding: typeof window !== 'undefined' && window.innerWidth <= 640 ? '16px' : typeof window !== 'undefined' && window.innerWidth <= 768 ? '20px' : '32px 36px',
        animation: 'slideInRight 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        scrollbarWidth: 'thin',
        scrollbarColor: 'rgba(255,255,255,0.08) transparent',
      }}
    >
      {/* ── Header ─────────────────────────────────────────── */}
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'flex-start', marginBottom: '32px',
        flexWrap: 'wrap', gap: '16px',
        animation: 'slideDown 0.4s ease-out',
      }}>
        {/* Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '18px', flex: 1, minWidth: '200px', animation: 'slideInLeft 0.5s ease-out' }}>
          {/* Avatar */}
          <div style={{
            width: typeof window !== 'undefined' && window.innerWidth <= 640 ? '50px' : '62px',
            height: typeof window !== 'undefined' && window.innerWidth <= 640 ? '50px' : '62px',
            borderRadius: '18px', flexShrink: 0,
            background: 'linear-gradient(135deg, rgba(34,211,238,0.2), rgba(217,70,239,0.2))',
            border: '2px solid rgba(34,211,238,0.25)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 800, 
            fontSize: typeof window !== 'undefined' && window.innerWidth <= 640 ? '1rem' : '1.25rem',
            color: 'var(--neon-cyan)',
            boxShadow: '0 0 20px rgba(34,211,238,0.12)',
            transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
            animation: 'scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
            cursor: 'pointer',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = 'scale(1.1) rotate(5deg)';
            e.currentTarget.style.boxShadow = '0 0 30px rgba(34,211,238,0.3)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'scale(1) rotate(0deg)';
            e.currentTarget.style.boxShadow = '0 0 20px rgba(34,211,238,0.12)';
          }}
          >
            {name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{
              fontSize: typeof window !== 'undefined' && window.innerWidth <= 640 ? '1.1rem' : '1.4rem',
              fontWeight: 800,
              background: 'linear-gradient(to right, #fff, #a5b4fc)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              backgroundClip: 'text', margin: 0, marginBottom: '4px',
              letterSpacing: '-0.03em',
              animation: 'slideInLeft 0.5s ease-out 0.1s backwards',
            }}>
              {name}
            </h2>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              color: 'var(--text-muted)', fontSize: '0.82rem',
              animation: 'slideInLeft 0.5s ease-out 0.2s backwards',
            }}>
              <Mail size={13} />
              {email}
            </div>
            {role && (
              <div style={{
                marginTop: '4px', fontSize: '0.75rem',
                color: 'rgba(165,180,252,0.7)', fontWeight: 600,
                animation: 'slideInLeft 0.5s ease-out 0.3s backwards',
              }}>
                <Award size={11} style={{ display: 'inline-block', marginRight: '6px' }} />
                {role}
              </div>
            )}
          </div>
        </div>

        {/* AI Score Ring */}
        <div style={{
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', gap: '6px',
          animation: 'slideInRight 0.5s ease-out',
        }}>
          <div style={{
            width: typeof window !== 'undefined' && window.innerWidth <= 640 ? '60px' : '76px',
            height: typeof window !== 'undefined' && window.innerWidth <= 640 ? '60px' : '76px',
            borderRadius: '50%',
            background: `conic-gradient(${scoreColor(aiScore)} ${aiScore * 3.6}deg, rgba(255,255,255,0.05) 0deg)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            position: 'relative',
            boxShadow: `0 0 24px ${scoreColor(aiScore)}33`,
            transition: 'all 0.3s ease',
            animation: 'rotateIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
            cursor: 'pointer',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.boxShadow = `0 0 40px ${scoreColor(aiScore)}66`;
            e.currentTarget.style.transform = 'scale(1.08)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.boxShadow = `0 0 24px ${scoreColor(aiScore)}33`;
            e.currentTarget.style.transform = 'scale(1)';
          }}
          >
            <div style={{
              position: 'absolute', inset: '8px',
              borderRadius: '50%', background: '#0B0E14',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column',
            }}>
              <span style={{
                fontSize: typeof window !== 'undefined' && window.innerWidth <= 640 ? '1rem' : '1.3rem',
                fontWeight: 800,
                color: scoreColor(aiScore),
                textShadow: `0 0 12px ${scoreColor(aiScore)}`,
              }}>
                {aiScore}
              </span>
            </div>
          </div>
          <div style={{
            fontSize: '0.65rem', fontWeight: 700,
            textTransform: 'uppercase', letterSpacing: '0.5px',
            color: 'var(--text-muted)', display: 'flex',
            alignItems: 'center', gap: '4px',
            animation: 'slideInRight 0.5s ease-out 0.1s backwards',
          }}>
            <Star size={9} style={{ color: 'var(--neon-cyan)' }} />
            AI Score
          </div>
        </div>
      </div>

      {/* ── Action Feedback Banner ──────────────────────────── */}
      {actionFeedback && (
        <div style={{
          padding: '12px 18px', borderRadius: '12px', marginBottom: '20px',
          background: actionFeedback.type === 'success'
            ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
          border: `1px solid ${actionFeedback.type === 'success' ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
          color: actionFeedback.type === 'success' ? '#10b981' : '#ef4444',
          fontSize: '0.85rem', fontWeight: 600,
          animation: 'slideUp 0.3s ease',
        }}>
          {actionFeedback.msg}
        </div>
      )}

      {/* ── AI Summary ─────────────────────────────────────── */}
      <div style={{
        background: 'rgba(34,211,238,0.04)',
        border: '1px solid rgba(34,211,238,0.12)',
        borderRadius: '16px', padding: '20px',
        marginBottom: '24px',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          marginBottom: '12px',
          fontSize: '0.75rem', fontWeight: 700,
          textTransform: 'uppercase', letterSpacing: '0.8px',
          color: 'var(--neon-cyan)',
        }}>
          <Brain size={14} />
          AI Summary
        </div>
        <p style={{
          fontSize: '0.88rem', lineHeight: 1.7,
          color: 'rgba(248,250,252,0.75)',
          margin: 0,
        }}>
          {aiSummary}
        </p>
      </div>

      {/* ── Score Breakdown ─────────────────────────────────── */}
      <div style={{
        background: 'rgba(15,21,34,0.5)',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '16px', padding: '22px',
        marginBottom: '24px',
      }}>
        <div style={{
          fontSize: '0.75rem', fontWeight: 700,
          textTransform: 'uppercase', letterSpacing: '0.8px',
          color: 'var(--text-muted)', marginBottom: '18px',
          display: 'flex', alignItems: 'center', gap: '7px',
        }}>
          <TrendingUp size={13} />
          Score Breakdown
        </div>

        <ScoreBar
          label="Skills Match"
          value={breakdown.skills}
          color="var(--neon-cyan)"
          icon={Code2}
        />
        <ScoreBar
          label="Projects"
          value={breakdown.projects}
          color="var(--neon-magenta)"
          icon={FlaskConical}
        />
        <ScoreBar
          label="Aptitude"
          value={breakdown.aptitude}
          color="var(--neon-amber)"
          icon={Brain}
        />
        <ScoreBar
          label="Growth Potential"
          value={breakdown.growthPotential}
          color="#a78bfa"
          icon={Dna}
        />
      </div>

      {/* ── Skills ─────────────────────────────────────────── */}
      {skills.length > 0 && (
        <div style={{
          background: 'rgba(15,21,34,0.5)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '16px', padding: '22px',
          marginBottom: '24px',
        }}>
          <div style={{
            fontSize: '0.75rem', fontWeight: 700,
            textTransform: 'uppercase', letterSpacing: '0.8px',
            color: 'var(--text-muted)', marginBottom: '14px',
            display: 'flex', alignItems: 'center', gap: '7px',
          }}>
            <Code2 size={13} />
            Skills &amp; Technologies
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {skills.map((skill, i) => (
              <SkillTag
                key={skill}
                skill={skill}
                variant={i < 3 ? 'accent' : 'default'}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Comprehensive Scoring Visualization ─────────────────────── */}
      {candidate.raw?.comprehensive_analysis && (
        <div style={{ marginBottom: '24px' }}>
          <ScoreBreakdown 
            comprehensiveAnalysis={candidate.raw.comprehensive_analysis}
            enhancedDecision={candidate.raw.enhanced_decision}
          />
        </div>
      )}

      {/* ── Neo4j Insights Visualization ─────────────────────– */}
      {candidate.raw?.comprehensive_analysis?.neo4j_insights && (
        <div style={{ marginBottom: '24px' }}>
          <Neo4jInsights 
            neo4jInsights={candidate.raw.comprehensive_analysis.neo4j_insights}
          />
        </div>
      )}

      {/* ── Risk Assessment Visualization ─────────────────────– */}
      {candidate.raw?.comprehensive_analysis?.risk_assessment && (
        <div style={{ marginBottom: '24px' }}>
          <RiskAssessmentChart 
            riskData={candidate.raw.comprehensive_analysis.risk_assessment}
          />
        </div>
      )}

      {/* ── Insights (extra raw data) ───────────────────────── */}
      {candidate.raw?.ai_report?.rag_reasoning && (
        <div style={{ marginBottom: '24px' }}>
          <button
            onClick={() => setShowInsights(p => !p)}
            style={{
              width: '100%',
              background: showInsights ? 'rgba(139,92,246,0.12)' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${showInsights ? 'rgba(139,92,246,0.3)' : 'rgba(255,255,255,0.08)'}`,
              borderRadius: '12px', padding: '14px 18px',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              cursor: 'pointer', color: showInsights ? '#a78bfa' : 'var(--text-muted)',
              fontSize: '0.83rem', fontWeight: 700,
              textTransform: 'uppercase', letterSpacing: '0.5px',
              transition: 'all 0.25s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={13} />
              RAG Insights
            </div>
            <ChevronRight
              size={16}
              style={{
                transform: showInsights ? 'rotate(90deg)' : 'rotate(0deg)',
                transition: 'transform 0.3s ease',
              }}
            />
          </button>

          {showInsights && (
            <div style={{
              marginTop: '8px', padding: '18px',
              background: 'rgba(139,92,246,0.06)',
              border: '1px solid rgba(139,92,246,0.15)',
              borderRadius: '12px',
              fontSize: '0.83rem', lineHeight: 1.7,
              color: 'rgba(248,250,252,0.65)',
              animation: 'slideUp 0.3s ease',
            }}>
              {candidate.raw.ai_report.rag_reasoning}
            </div>
          )}
        </div>
      )}

      {/* ── Action Buttons ──────────────────────────────────── */}
      <div style={{
        display: 'flex', gap: '12px', flexWrap: 'wrap',
        position: 'sticky', bottom: 0, paddingTop: '16px',
        background: 'linear-gradient(to top, #0B0E14 60%, transparent)',
        paddingBottom: '4px',
      }}>
        {/* Shortlist */}
        <button
          disabled={actionLoading || isShortlisted || isRejected}
          onClick={() => onShortlist(candidate.id)}
          style={{
            flex: 1, minWidth: '130px',
            padding: '14px 20px',
            borderRadius: '14px', border: 'none',
            cursor: actionLoading || isShortlisted || isRejected ? 'not-allowed' : 'pointer',
            background: isShortlisted
              ? 'rgba(16,185,129,0.15)'
              : isRejected ? 'rgba(107,114,128,0.1)' : 'linear-gradient(135deg, #059669, #10b981)',
            color: isShortlisted ? '#10b981' : isRejected ? 'rgba(148,163,184,0.5)' : 'white',
            fontWeight: 700, fontSize: '0.88rem',
            display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: '8px',
            boxShadow: isShortlisted ? 'none' : isRejected ? 'none' : '0 4px 16px rgba(16,185,129,0.3)',
            transition: 'all 0.25s ease',
            opacity: actionLoading ? 0.6 : isRejected ? 0.5 : 1,
            letterSpacing: '0.3px',
          }}
        >
          <CheckCircle size={16} />
          {isShortlisted ? 'Shortlisted' : 'Approve Candidate'}
        </button>

        {/* Reject */}
        <button
          disabled={actionLoading || isRejected || isShortlisted}
          onClick={() => onReject(candidate.id)}
          style={{
            flex: 1, minWidth: '130px',
            padding: '14px 20px',
            borderRadius: '14px', border: 'none',
            cursor: actionLoading || isRejected || isShortlisted ? 'not-allowed' : 'pointer',
            background: isRejected
              ? 'rgba(239,68,68,0.15)'
              : isShortlisted ? 'rgba(107,114,128,0.1)' : 'linear-gradient(135deg, #dc2626, #ef4444)',
            color: isRejected ? '#ef4444' : isShortlisted ? 'rgba(148,163,184,0.5)' : 'white',
            fontWeight: 700, fontSize: '0.88rem',
            display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: '8px',
            boxShadow: isRejected ? 'none' : isShortlisted ? 'none' : '0 4px 16px rgba(239,68,68,0.3)',
            transition: 'all 0.25s ease',
            opacity: actionLoading ? 0.6 : isShortlisted ? 0.5 : 1,
            letterSpacing: '0.3px',
          }}
        >
          <XCircle size={16} />
          {isRejected ? 'Rejected' : 'Reject Application'}
        </button>

        {/* AI Insights deep-link */}
        <a
          href={`/candidates/${candidate.id}`}
          style={{
            flexShrink: 0,
            padding: '14px 18px',
            borderRadius: '14px',
            border: '1px solid rgba(139,92,246,0.3)',
            background: 'rgba(139,92,246,0.1)',
            color: '#a78bfa',
            fontWeight: 700, fontSize: '0.88rem',
            display: 'flex', alignItems: 'center', gap: '8px',
            textDecoration: 'none',
            transition: 'all 0.25s ease',
            boxShadow: '0 4px 16px rgba(139,92,246,0.15)',
            letterSpacing: '0.3px',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(139,92,246,0.2)';
            e.currentTarget.style.borderColor = 'rgba(139,92,246,0.5)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(139,92,246,0.1)';
            e.currentTarget.style.borderColor = 'rgba(139,92,246,0.3)';
          }}
        >
          <Sparkles size={16} />
          Full Report
        </a>
      </div>
    </div>
  );
});

CandidateDetailPanel.displayName = 'CandidateDetailPanel';
export default CandidateDetailPanel;
