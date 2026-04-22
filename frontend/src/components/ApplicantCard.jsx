import { memo } from 'react';
import { Mail, Sparkles } from 'lucide-react';

// ── Helpers ───────────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  'Shortlisted': {
    label: 'Shortlisted',
    bg: 'rgba(16, 185, 129, 0.12)',
    border: 'rgba(16, 185, 129, 0.35)',
    color: '#10b981',
    dot: '#10b981',
  },
  'Rejected': {
    label: 'Rejected',
    bg: 'rgba(239, 68, 68, 0.12)',
    border: 'rgba(239, 68, 68, 0.35)',
    color: '#ef4444',
    dot: '#ef4444',
  },
  'Under Review': {
    label: 'Under Review',
    bg: 'rgba(245, 158, 11, 0.12)',
    border: 'rgba(245, 158, 11, 0.35)',
    color: '#f59e0b',
    dot: '#f59e0b',
  },
};

function scoreColor(score) {
  if (score >= 80) return 'var(--neon-cyan)';
  if (score >= 60) return 'var(--neon-amber)';
  return '#f43f5e';
}

function scoreGlow(score) {
  if (score >= 80) return '0 0 10px rgba(34,211,238,0.4)';
  if (score >= 60) return '0 0 10px rgba(245,158,11,0.4)';
  return '0 0 10px rgba(244,63,94,0.4)';
}

// ── Component ─────────────────────────────────────────────────────────────────
const ApplicantCard = memo(({ candidate, isSelected, onClick }) => {
  const { name, email, status, aiScore, skills, insightText } = candidate;
  const statusCfg = STATUS_CONFIG[status] || STATUS_CONFIG['Under Review'];
  const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  return (
    <div
      className="candidate-card-elite"
      onClick={onClick}
      style={{
        position: 'relative',
        background: isSelected
          ? 'rgba(34, 211, 238, 0.06)'
          : 'rgba(15, 21, 34, 0.55)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: `1px solid ${isSelected ? 'rgba(34,211,238,0.55)' : 'rgba(255,255,255,0.07)'}`,
        borderRadius: '18px',
        padding: '20px',
        cursor: 'pointer',
        marginBottom: '12px',
        boxShadow: isSelected
          ? '0 0 24px rgba(34,211,238,0.18), inset 0 0 0 1px rgba(34,211,238,0.12)'
          : '0 4px 20px rgba(0,0,0,0.25)',
        transition: 'all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
        overflow: 'hidden',
      }}
    >
      {/* Selected indicator strip */}
      {isSelected && (
        <div style={{
          position: 'absolute',
          left: 0, top: 0, bottom: 0,
          width: '3px',
          background: 'linear-gradient(180deg, var(--neon-cyan), var(--neon-magenta))',
          borderRadius: '18px 0 0 18px',
        }} />
      )}

      {/* Row 1 – Avatar + Name + Status */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', marginBottom: '14px' }}>
        {/* Avatar */}
        <div style={{
          width: '44px', height: '44px', borderRadius: '14px', flexShrink: 0,
          background: isSelected
            ? 'linear-gradient(135deg, rgba(34,211,238,0.25), rgba(217,70,239,0.25))'
            : 'rgba(255,255,255,0.06)',
          border: '1px solid rgba(255,255,255,0.1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 800, fontSize: '0.9rem',
          color: isSelected ? 'var(--neon-cyan)' : 'var(--text-muted)',
          letterSpacing: '-0.5px',
        }}>
          {initials}
        </div>

        {/* Name + Email */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            marginBottom: '3px',
          }}>
            {name}
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '5px',
            color: 'var(--text-muted)', fontSize: '0.75rem',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            <Mail size={11} style={{ flexShrink: 0 }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{email}</span>
          </div>
        </div>

        {/* Status badge */}
        <div style={{
          background: statusCfg.bg,
          border: `1px solid ${statusCfg.border}`,
          color: statusCfg.color,
          borderRadius: '20px',
          padding: '3px 10px',
          fontSize: '0.68rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          whiteSpace: 'nowrap',
          display: 'flex', alignItems: 'center', gap: '5px',
          flexShrink: 0,
        }}>
          <div style={{
            width: '5px', height: '5px', borderRadius: '50%',
            background: statusCfg.dot,
            boxShadow: `0 0 4px ${statusCfg.dot}`,
          }} />
          {statusCfg.label}
        </div>
      </div>

      {/* Row 2 – AI Score */}
      <div style={{ marginBottom: '14px' }}>
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', marginBottom: '6px',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '5px',
            fontSize: '0.72rem', fontWeight: 700,
            textTransform: 'uppercase', letterSpacing: '0.5px',
            color: 'var(--text-muted)',
          }}>
            <Sparkles size={11} style={{ color: 'var(--neon-cyan)' }} />
            AI Score
          </div>
          <div style={{
            fontWeight: 800, fontSize: '0.95rem',
            color: scoreColor(aiScore),
            textShadow: scoreGlow(aiScore),
          }}>
            {aiScore}
            <span style={{ fontSize: '0.6rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '1px' }}>/100</span>
          </div>
        </div>
        {/* Progress bar */}
        <div style={{
          width: '100%', height: '5px',
          background: 'rgba(255,255,255,0.05)',
          borderRadius: '4px', overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${aiScore}%`,
            borderRadius: '4px',
            background: aiScore >= 80
              ? 'linear-gradient(90deg, #06b6d4, #22d3ee)'
              : aiScore >= 60
              ? 'linear-gradient(90deg, #d97706, #f59e0b)'
              : 'linear-gradient(90deg, #dc2626, #f43f5e)',
            boxShadow: `0 0 8px ${scoreColor(aiScore)}66`,
            transition: 'width 1s ease-out',
          }} />
        </div>
      </div>

      {/* Row 3 – Skills */}
      {skills.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginBottom: '12px' }}>
          {skills.slice(0, 5).map(skill => (
            <span key={skill} style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '6px',
              padding: '2px 8px',
              fontSize: '0.68rem',
              color: 'var(--text-muted)',
              fontWeight: 500,
            }}>
              {skill}
            </span>
          ))}
          {skills.length > 5 && (
            <span style={{
              background: 'rgba(34,211,238,0.06)',
              border: '1px solid rgba(34,211,238,0.15)',
              borderRadius: '6px',
              padding: '2px 8px',
              fontSize: '0.68rem',
              color: 'var(--neon-cyan)',
              fontWeight: 600,
            }}>
              +{skills.length - 5}
            </span>
          )}
        </div>
      )}

      {/* Row 4 – Insight text */}
      <div style={{
        fontSize: '0.7rem',
        color: 'rgba(148,163,184,0.6)',
        fontStyle: 'italic',
        display: 'flex', alignItems: 'center', gap: '5px',
      }}>
        <Sparkles size={9} style={{ color: 'rgba(34,211,238,0.5)' }} />
        {insightText}
      </div>
    </div>
  );
});

ApplicantCard.displayName = 'ApplicantCard';
export default ApplicantCard;
