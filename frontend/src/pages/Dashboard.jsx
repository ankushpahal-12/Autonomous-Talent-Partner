import { useState } from 'react';
import { User, Mail, ArrowRight, Zap, Target, Users, TrendingUp, Sparkles, Clock, BarChart3, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  Cell, AreaChart, Area 
} from 'recharts';
import { useDashboard } from '../hooks/useDashboard';

export default function Dashboard() {
  // State for interactive features
  const [hoveredStat, setHoveredStat] = useState(null);
  
  // ─────────────────────────────────────────────────────────────────────
  // BUSINESS LOGIC (Hook)
  // ─────────────────────────────────────────────────────────────────────
  const {
    loading,
    stats,
    scoreDistribution,
    topTalent,
    recentActivity,
    hasData,
  } = useDashboard();
  // ─────────────────────────────────────────────────────────────────────
  // LOADING STATE
  // ─────────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div style={{ 
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '20px',
        }}>
          <div className="loader" style={{ width: '50px', height: '50px', borderWidth: '4px' }}></div>
          <div style={{ color: 'var(--text-muted)', fontSize: '1rem', fontWeight: 500 }}>
            Loading Intelligence Hub...
          </div>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────
  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }} className="animate-stagger">
      <header style={{ marginBottom: '40px', animation: 'slideInDown 0.6s ease-out' }}>
        <h1 style={{ textAlign: 'left', fontSize: '3rem', fontWeight: 800, marginBottom: '8px', letterSpacing: '-0.04em' }}>
          Intelligence Hub
        </h1>
        <p className="subtitle" style={{ textAlign: 'left', margin: 0, fontSize: '1.2rem', opacity: 0.8 }}>
          Real-time analytics and global talent overview.
        </p>
      </header>

      {hasData ? (
        <>
          {/* Hero Stats Section */}
          <div className="animate-stagger-children" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px', marginBottom: '32px' }}>
            {/* Total Ingested */}
            <div 
              className="glass-card-elite hover-lift" 
              onMouseEnter={() => setHoveredStat('total')}
              onMouseLeave={() => setHoveredStat(null)}
              style={{ 
                padding: '24px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '20px',
                cursor: 'pointer',
                background: hoveredStat === 'total' 
                  ? 'rgba(34,211,238,0.08)' 
                  : 'rgba(15,21,34,0.4)',
                transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                position: 'relative',
                overflow: 'hidden',
              }}>
              <div style={{ 
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(135deg, transparent, rgba(34,211,238,0.1))',
                opacity: hoveredStat === 'total' ? 1 : 0,
                transition: 'opacity 0.3s ease',
              }} />
              <div style={{ background: 'rgba(34, 211, 238, 0.1)', padding: '12px', borderRadius: '16px', position: 'relative', zIndex: 1 }}>
                <Users size={28} style={{ color: 'var(--neon-cyan)' }} />
              </div>
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px' }}>Total Ingested</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, animation: hoveredStat === 'total' ? 'scaled-pop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)' : 'none' }}>
                  {stats.total}
                  {hoveredStat === 'total' && <span style={{ fontSize: '0.8rem', marginLeft: '8px', color: 'var(--neon-cyan)', display: 'inline-block' }}>↑</span>}
                </div>
              </div>
            </div>

            {/* AI Reviewed */}
            <div 
              className="glass-card-elite hover-lift" 
              onMouseEnter={() => setHoveredStat('reviewed')}
              onMouseLeave={() => setHoveredStat(null)}
              style={{ 
                padding: '24px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '20px',
                cursor: 'pointer',
                background: hoveredStat === 'reviewed' 
                  ? 'rgba(245,158,11,0.08)' 
                  : 'rgba(15,21,34,0.4)',
                transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                position: 'relative',
                overflow: 'hidden',
              }}>
              <div style={{ 
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(135deg, transparent, rgba(245,158,11,0.1))',
                opacity: hoveredStat === 'reviewed' ? 1 : 0,
                transition: 'opacity 0.3s ease',
              }} />
              <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '12px', borderRadius: '16px', position: 'relative', zIndex: 1 }}>
                <Zap size={28} style={{ color: 'var(--neon-amber)' }} />
              </div>
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px' }}>AI Reviewed</div>
                <div style={{ fontSize: '2rem', fontWeight: 800 }}>
                  {stats.reviewed}
                  {hoveredStat === 'reviewed' && <span style={{ fontSize: '0.8rem', marginLeft: '8px', color: 'var(--neon-amber)' }}>⚡</span>}
                </div>
              </div>
            </div>

            {/* Elite Talent */}
            <div 
              className="glass-card-elite hover-lift" 
              onMouseEnter={() => setHoveredStat('elite')}
              onMouseLeave={() => setHoveredStat(null)}
              style={{ 
                padding: '24px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '20px',
                cursor: 'pointer',
                background: hoveredStat === 'elite' 
                  ? 'rgba(34,211,238,0.08)' 
                  : 'rgba(15,21,34,0.4)',
                transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                position: 'relative',
                overflow: 'hidden',
              }}>
              <div style={{ 
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(135deg, transparent, rgba(34,211,238,0.1))',
                opacity: hoveredStat === 'elite' ? 1 : 0,
                transition: 'opacity 0.3s ease',
              }} />
              <div style={{ background: 'rgba(34, 211, 238, 0.1)', padding: '12px', borderRadius: '16px', position: 'relative', zIndex: 1 }}>
                <Target size={28} style={{ color: 'var(--neon-cyan)' }} />
              </div>
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px' }}>Elite Talent</div>
                <div style={{ fontSize: '2rem', fontWeight: 800 }}>
                  {stats.elite}
                  {hoveredStat === 'elite' && <span style={{ fontSize: '0.8rem', marginLeft: '8px', color: 'var(--neon-cyan)' }}>⭐</span>}
                </div>
              </div>
            </div>

            {/* Avg Quality */}
            <div 
              className="glass-card-elite hover-lift" 
              onMouseEnter={() => setHoveredStat('score')}
              onMouseLeave={() => setHoveredStat(null)}
              style={{ 
                padding: '24px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '20px',
                cursor: 'pointer',
                background: hoveredStat === 'score' 
                  ? 'rgba(217,70,239,0.08)' 
                  : 'rgba(15,21,34,0.4)',
                transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                position: 'relative',
                overflow: 'hidden',
              }}>
              <div style={{ 
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(135deg, transparent, rgba(217,70,239,0.1))',
                opacity: hoveredStat === 'score' ? 1 : 0,
                transition: 'opacity 0.3s ease',
              }} />
              <div style={{ background: 'rgba(217, 70, 239, 0.1)', padding: '12px', borderRadius: '16px', position: 'relative', zIndex: 1 }}>
                <TrendingUp size={28} style={{ color: 'var(--neon-magenta)' }} />
              </div>
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px' }}>Avg Quality</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {stats.avgScore}%
                  {hoveredStat === 'score' && <ArrowUpRight size={20} style={{ color: 'var(--success)' }} />}
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="bento-grid">
            {/* Score Distribution Chart */}
            <div className="bento-item bento-two-thirds glass-card-elite hover-lift" style={{ height: '400px', opacity: 0, animation: 'slideUp 0.6s ease-out 0.4s forwards' }}>
              <div className="card-title">
                <BarChart3 size={18} style={{ animation: 'float 3s ease-in-out infinite' }} /> Match Score Distribution
              </div>
              <ResponsiveContainer width="100%" height="85%">
                <BarChart data={scoreDistribution}>
                  <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ background: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  />
                  <Bar dataKey="count" radius={[8, 8, 0, 0]} barSize={60}>
                    {scoreDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} fillOpacity={0.8} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Global Pipeline Health */}
            <div className="bento-item bento-third glass-card-elite hover-lift" style={{ height: '400px', opacity: 0, animation: 'slideUp 0.6s ease-out 0.5s forwards' }}>
              <div className="card-title">
                <Sparkles size={18} style={{ animation: 'bounce 2s ease-in-out infinite' }} /> Pipeline Alignment
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                <div className="circular-progress neon-glow-cyan" style={{ width: '160px', height: '160px', background: `conic-gradient(var(--neon-cyan) ${stats.avgScore * 3.6}deg, rgba(255,255,255,0.05) 0deg)`, border: 'none', animation: 'rotateIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)' }}>
                  <div className="circular-value" style={{ fontSize: '3rem' }}>{stats.avgScore}</div>
                </div>
                <div style={{ marginTop: '32px', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>Global Quality Index</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>Real-time verified metric.</div>
                </div>
              </div>
            </div>

            {/* Top Talent Spotlight */}
            <div className="bento-item bento-half glass-card-elite hover-lift" style={{ opacity: 0, animation: 'slideUp 0.6s ease-out 0.6s forwards' }}>
              <div className="card-title" style={{ justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}><Zap size={18} style={{ animation: 'pulse 2s ease-in-out infinite' }} /> Top Talent Spotlight</div>
                <Link to="/applicants" style={{ fontSize: '0.75rem', color: 'var(--accent)', textDecoration: 'none', fontWeight: 600, transition: 'color 0.2s ease' }} onMouseEnter={e => e.target.style.color = 'var(--accent-hover)'} onMouseLeave={e => e.target.style.color = 'var(--accent)'}>View All →</Link>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {topTalent.map((c) => (
                  <Link key={c.id} to={`/candidates/${c.id}`} className="stat-box" style={{ textDecoration: 'none', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'rgba(34, 211, 238, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, color: 'var(--neon-cyan)' }}>
                        {c.name?.charAt(0) || '?'}
                      </div>
                      <div>
                        <div style={{ fontWeight: 600 }}>{c.name || 'Anonymous'}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{c.skills?.[0] || 'No Skills Listed'}</div>
                      </div>
                    </div>
                    <div style={{ color: 'var(--neon-cyan)', fontWeight: 800, fontSize: '1.1rem' }}>{c.score}</div>
                  </Link>
                ))}
                {topTalent.length === 0 && <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>Analyzing talent pool...</div>}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bento-item bento-half glass-card-elite hover-lift" style={{ opacity: 0, animation: 'slideUp 0.6s ease-out 0.7s forwards' }}>
              <div className="card-title">
                <Clock size={18} style={{ animation: 'float 2.5s ease-in-out infinite' }} /> Recent Pipeline Activity
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {recentActivity.map((c, idx) => (
                  <div key={c.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', padding: '12px 4px', borderBottom: '1px solid rgba(255,255,255,0.05)', animation: `slideInLeft 0.5s ease-out ${0.1 + idx * 0.1}s forwards`, opacity: 0 }}>
                    <div style={{ marginTop: '4px' }}>
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: c.status === 'ai_reviewed' ? 'var(--success)' : 'var(--neon-amber)', animation: 'pulse 2s ease-in-out infinite' }}></div>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>Candidate {c.name || 'Processing...'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status changed to <span style={{ color: 'white' }}>{c.status.replace('_', ' ')}</span></div>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Just now</div>
                  </div>
                ))}
                {recentActivity.length === 0 && <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>Generating activity log...</div>}
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="glass-card-elite" style={{ textAlign: 'center', padding: '120px 40px', marginTop: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ width: '100px', height: '100px', background: 'rgba(34, 211, 238, 0.1)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '32px', boxShadow: '0 0 40px rgba(34, 211, 238, 0.1)' }}>
            <Users size={48} style={{ color: 'var(--neon-cyan)' }} />
          </div>
          <h2 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '16px', letterSpacing: '-0.02em' }}>Initialize Command Center</h2>
          <p className="subtitle" style={{ fontSize: '1.2rem', maxWidth: '600px', margin: '0 auto 40px', lineHeight: 1.6 }}>
            Your Intelligence Hub is currently offline. Upload real resumes to activate the Multi-Agent evaluation swarm and populate your global talent analytics.
          </p>
          <Link to="/upload" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '20px 40px', fontSize: '1.2rem', textDecoration: 'none' }}>
            <Sparkles size={20} /> Deploy Swarm via Upload
          </Link>
        </div>
      )}
    </div>
  );
}
