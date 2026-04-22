import { useState, useRef, useEffect } from 'react';
import {
    Users, Search, X, RefreshCw, SlidersHorizontal,
    Sparkles, ChevronDown,
} from 'lucide-react';

import { useApplicants } from '../hooks/useApplicants';
import { useWebSocket } from '../hooks/useWebSocket';
import ApplicantCard from '../components/ApplicantCard';
import CandidateDetailPanel from '../components/CandidateDetailPanel';
import RealtimeNotifications from '../components/RealtimeNotifications';


const FILTERS = ['All', 'Under Review', 'Shortlisted', 'Rejected'];

function FilterPill({ label, active, count, onClick }) {
    const colors = {
        All: { active: 'rgba(34,211,238,0.15)', border: 'rgba(34,211,238,0.4)', text: 'var(--neon-cyan)' },
        'Under Review': { active: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.35)', text: '#f59e0b' },
        Shortlisted: { active: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.35)', text: '#10b981' },
        Rejected: { active: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.35)', text: '#ef4444' },
    };
    const cfg = colors[label] || colors.All;

    return (
        <button
            onClick={onClick}
            style={{
                padding: '6px 14px',
                borderRadius: '20px',
                border: active ? `1px solid ${cfg.border}` : '1px solid rgba(255,255,255,0.07)',
                background: active ? cfg.active : 'rgba(255,255,255,0.03)',
                color: active ? cfg.text : 'var(--text-muted)',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.25s ease',
                display: 'flex', alignItems: 'center', gap: '6px',
                whiteSpace: 'nowrap',
                boxShadow: active ? `0 0 12px ${cfg.border}55` : 'none',
            }}
        >
            {label}
            {typeof count === 'number' && (
                <span style={{
                    background: active ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.06)',
                    borderRadius: '10px',
                    padding: '1px 6px',
                    fontSize: '0.65rem',
                    fontWeight: 800,
                }}>
                    {count}
                </span>
            )}
        </button>
    );
}

const SORT_OPTIONS = [
    { value: 'score_desc', label: '↓ Highest Score' },
    { value: 'score_asc', label: '↑ Lowest Score' },
    { value: 'name_asc', label: 'A → Z' },
    { value: 'name_desc', label: 'Z → A' },
];

function sortCandidates(list, sort) {
    return [...list].sort((a, b) => {
        switch (sort) {
            case 'score_desc': return (b.aiScore || 0) - (a.aiScore || 0);
            case 'score_asc': return (a.aiScore || 0) - (b.aiScore || 0);
            case 'name_asc': return a.name.localeCompare(b.name);
            case 'name_desc': return b.name.localeCompare(a.name);
            default: return 0;
        }
    });
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Applicants() {
    const {
        candidates,
        allCandidates,
        loading,
        error,
        selectedId,
        selectedCandidate,
        setSelectedId,
        searchQuery,
        setSearchQuery,
        statusFilter,
        setStatusFilter,
        actionLoading,
        actionFeedback,
        makeDecision,
        refetch,
    } = useApplicants();

    const [sort, setSort] = useState('score_desc');
    const [sortOpen, setSortOpen] = useState(false);
    const [searchFocused, setSearchFocused] = useState(false);
    const [sessionId] = useState(() => `applicants-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);
    const searchRef = useRef(null);
    const sortRef = useRef(null);

    const { isConnected, events } = useWebSocket(sessionId);

    // Close sort dropdown on outside click
    useEffect(() => {
        function handle(e) {
            if (sortRef.current && !sortRef.current.contains(e.target)) {
                setSortOpen(false);
            }
        }
        document.addEventListener('mousedown', handle);
        return () => document.removeEventListener('mousedown', handle);
    }, []);

    // Sorted candidates
    const displayList = sortCandidates(candidates, sort);

    // Count per status from all (unfiltered) candidates
    const statusCounts = {
        All: allCandidates.length,
        'Under Review': allCandidates.filter(c => c.status === 'Under Review').length,
        Shortlisted: allCandidates.filter(c => c.status === 'Shortlisted').length,
        Rejected: allCandidates.filter(c => c.status === 'Rejected').length,
    };

    // ── Loading ──────────────────────────────────────────────────────────────
    if (loading) {
        return (
            <div style={{
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
                height: '70vh', gap: '20px',
            }}>
                <div style={{
                    width: '56px', height: '56px', borderRadius: '50%',
                    border: '3px solid rgba(34,211,238,0.15)',
                    borderTop: '3px solid var(--neon-cyan)',
                    animation: 'spin 0.9s linear infinite',
                }} />
                <div style={{ color: 'var(--text-muted)', fontSize: '0.88rem', fontWeight: 500 }}>
                    Loading talent pipeline…
                </div>
            </div>
        );
    }
    if (error) {
        return (
            <div style={{
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
                height: '60vh', gap: '16px', color: '#ef4444',
            }}>
                <div style={{
                    background: 'rgba(239,68,68,0.08)',
                    border: '1px solid rgba(239,68,68,0.2)',
                    borderRadius: '16px', padding: '32px 48px',
                    textAlign: 'center',
                }}>
                    <p style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '8px' }}>
                        ⚠ Failed to fetch candidates
                    </p>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
                        {error}
                    </p>
                    <button onClick={refetch} style={{
                        background: 'rgba(239,68,68,0.15)',
                        border: '1px solid rgba(239,68,68,0.3)',
                        color: '#ef4444', padding: '10px 20px',
                        borderRadius: '10px', cursor: 'pointer',
                        fontWeight: 600, fontSize: '0.85rem',
                        display: 'flex', alignItems: 'center', gap: '8px',
                    }}>
                        <RefreshCw size={14} /> Retry
                    </button>
                </div>
            </div>
        );
    }

    // ── Main Layout ──────────────────────────────────────────────────────────
    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 80px)', minHeight: 0, position: 'relative' }}>

            {/* Fullscreen Modal - appears when candidate is selected */}
            {selectedCandidate && (
                <>
                    {/* Backdrop */}
                    <div
                        onClick={() => setSelectedId(null)}
                        style={{
                            position: 'fixed',
                            inset: 0,
                            background: 'rgba(0,0,0,0.6)',
                            backdropFilter: 'blur(8px)',
                            zIndex: 999,
                            animation: 'fadeIn 0.3s ease',
                        }}
                    />

                    {/* Modal Container */}
                    <div style={{
                        position: 'fixed',
                        inset: 0,
                        zIndex: 1000,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '20px',
                        animation: 'slideUp 0.3s ease',
                    }}>
                        {/* Modal Content */}
                        <div style={{
                            background: 'rgba(15,21,34,0.95)',
                            backdropFilter: 'blur(24px)',
                            WebkitBackdropFilter: 'blur(24px)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '24px',
                            width: '100%',
                            maxWidth: '900px',
                            maxHeight: '90vh',
                            overflow: 'hidden',
                            display: 'flex',
                            flexDirection: 'column',
                            boxShadow: '0 20px 80px rgba(0,0,0,0.6)',
                        }}>
                            {/* Modal Header */}
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '24px 32px',
                                borderBottom: '1px solid rgba(255,255,255,0.07)',
                                flexShrink: 0,
                            }}>
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '12px',
                                }}>
                                    <div style={{
                                        width: '48px',
                                        height: '48px',
                                        borderRadius: '50%',
                                        background: `linear-gradient(135deg, rgba(34,211,238,0.2), rgba(245,158,11,0.2))`,
                                        border: '1px solid rgba(34,211,238,0.3)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '1.4rem',
                                        fontWeight: 700,
                                        color: 'var(--neon-cyan)',
                                    }}>
                                        {selectedCandidate?.name?.charAt(0)?.toUpperCase()}
                                    </div>
                                    <div>
                                        <h2 style={{
                                            fontSize: '1.6rem',
                                            fontWeight: 800,
                                            margin: 0,
                                            color: 'var(--text-main)',
                                        }}>
                                            {selectedCandidate?.name}
                                        </h2>
                                        <p style={{
                                            fontSize: '0.85rem',
                                            color: 'var(--text-muted)',
                                            margin: '4px 0 0 0',
                                        }}>
                                            {selectedCandidate?.email}
                                        </p>
                                    </div>
                                </div>

                                {/* Close Button */}
                                <button
                                    onClick={() => setSelectedId(null)}
                                    style={{
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '12px',
                                        padding: '10px',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        transition: 'all 0.2s ease',
                                        color: 'var(--text-muted)',
                                        flexShrink: 0,
                                    }}
                                    onMouseEnter={e => {
                                        e.currentTarget.style.background = 'rgba(239,68,68,0.15)';
                                        e.currentTarget.style.borderColor = 'rgba(239,68,68,0.3)';
                                        e.currentTarget.style.color = '#ef4444';
                                    }}
                                    onMouseLeave={e => {
                                        e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
                                        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
                                        e.currentTarget.style.color = 'var(--text-muted)';
                                    }}
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Modal Body */}
                            <div style={{
                                flex: 1,
                                overflow: 'auto',
                                scrollbarWidth: 'thin',
                                scrollbarColor: 'rgba(255,255,255,0.1) transparent',
                            }}>
                                <CandidateDetailPanel
                                    candidate={selectedCandidate}
                                    actionLoading={actionLoading}
                                    actionFeedback={actionFeedback}
                                    onShortlist={id => makeDecision(id, 'selected')}
                                    onReject={id => makeDecision(id, 'rejected')}
                                />
                            </div>
                        </div>
                    </div>
                </>
            )}

            {/* ── Page Header ──────────────────────────────────── */}
            <header style={{ marginBottom: '24px', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
                    <div>
                        <h1 style={{
                            textAlign: 'left', fontSize: '2.2rem', fontWeight: 800,
                            marginBottom: '4px', letterSpacing: '-0.04em',
                        }}>
                            Applicants
                        </h1>
                        <p className="subtitle" style={{ textAlign: 'left', margin: 0, fontSize: '0.9rem' }}>
                            AI-powered candidate evaluation pipeline · {allCandidates.length} total
                        </p>
                    </div>

                    {/* Refresh */}
                    <button
                        onClick={refetch}
                        disabled={loading}
                        style={{
                            background: 'rgba(255,255,255,0.04)',
                            border: '1px solid rgba(255,255,255,0.08)',
                            borderRadius: '10px', padding: '10px 16px',
                            cursor: 'pointer', color: 'var(--text-muted)',
                            display: 'flex', alignItems: 'center', gap: '7px',
                            fontSize: '0.8rem', fontWeight: 600,
                            transition: 'all 0.2s ease',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(34,211,238,0.3)'; e.currentTarget.style.color = 'var(--neon-cyan)'; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = 'var(--text-muted)'; }}
                    >
                        <RefreshCw size={13} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
                        Refresh
                    </button>
                </div>

                {/* ── Filter + Search bar row ───────────────────── */}
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    marginTop: '16px', flexWrap: 'wrap',
                }}>
                    {/* Status pills */}
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {FILTERS.map(f => (
                            <FilterPill
                                key={f}
                                label={f}
                                active={statusFilter === f}
                                count={statusCounts[f]}
                                onClick={() => setStatusFilter(f)}
                            />
                        ))}
                    </div>

                    {/* Spacer */}
                    <div style={{ flex: 1 }} />

                    {/* Sort dropdown */}
                    <div ref={sortRef} style={{ position: 'relative' }}>
                        <button
                            onClick={() => setSortOpen(p => !p)}
                            style={{
                                background: 'rgba(255,255,255,0.04)',
                                border: '1px solid rgba(255,255,255,0.08)',
                                borderRadius: '10px', padding: '8px 14px',
                                cursor: 'pointer', color: 'var(--text-muted)',
                                display: 'flex', alignItems: 'center', gap: '6px',
                                fontSize: '0.78rem', fontWeight: 600,
                                transition: 'all 0.2s ease',
                            }}
                        >
                            <SlidersHorizontal size={12} />
                            {SORT_OPTIONS.find(o => o.value === sort)?.label}
                            <ChevronDown size={12} style={{ transform: sortOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s ease' }} />
                        </button>

                        {sortOpen && (
                            <div style={{
                                position: 'absolute', top: 'calc(100% + 8px)', right: 0,
                                background: 'rgba(15,21,34,0.95)',
                                backdropFilter: 'blur(20px)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: '12px', padding: '6px',
                                zIndex: 100, minWidth: '160px',
                                boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
                                animation: 'slideUp 0.2s ease',
                            }}>
                                {SORT_OPTIONS.map(opt => (
                                    <button
                                        key={opt.value}
                                        onClick={() => { setSort(opt.value); setSortOpen(false); }}
                                        style={{
                                            width: '100%', padding: '9px 12px',
                                            borderRadius: '8px', border: 'none',
                                            background: sort === opt.value ? 'rgba(34,211,238,0.1)' : 'transparent',
                                            color: sort === opt.value ? 'var(--neon-cyan)' : 'var(--text-muted)',
                                            fontSize: '0.78rem', fontWeight: 600,
                                            cursor: 'pointer', textAlign: 'left',
                                            transition: 'all 0.15s ease',
                                        }}
                                        onMouseEnter={e => { if (sort !== opt.value) e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; }}
                                        onMouseLeave={e => { if (sort !== opt.value) e.currentTarget.style.background = 'transparent'; }}
                                    >
                                        {opt.label}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Search */}
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: '8px',
                        background: searchFocused ? 'rgba(34,211,238,0.06)' : 'rgba(255,255,255,0.03)',
                        border: `1px solid ${searchFocused ? 'rgba(34,211,238,0.4)' : 'rgba(255,255,255,0.08)'}`,
                        borderRadius: '10px', padding: '8px 12px',
                        transition: 'all 0.25s ease',
                        boxShadow: searchFocused ? '0 0 16px rgba(34,211,238,0.08)' : 'none',
                    }}>
                        <Search size={13} style={{ color: searchFocused ? 'var(--neon-cyan)' : 'var(--text-muted)', flexShrink: 0 }} />
                        <input
                            ref={searchRef}
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            onFocus={() => setSearchFocused(true)}
                            onBlur={() => setSearchFocused(false)}
                            placeholder="Search name, email, skill…"
                            style={{
                                background: 'none', border: 'none', outline: 'none',
                                color: 'var(--text-main)', fontSize: '0.8rem',
                                width: '180px', fontWeight: 500,
                            }}
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                style={{
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    color: 'var(--text-muted)', display: 'flex', padding: 0,
                                }}
                            >
                                <X size={12} />
                            </button>
                        )}
                    </div>
                </div>
            </header>

            {/* ── Split Panel ───────────────────────────────────────────────────── */}
            <div style={{
                display: 'flex',
                gap: '0',
                flex: 1,
                minHeight: 0,
                background: 'rgba(15,21,34,0.45)',
                backdropFilter: 'blur(24px)',
                WebkitBackdropFilter: 'blur(24px)',
                border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: '20px',
                overflow: 'hidden',
                boxShadow: '0 20px 60px rgba(0,0,0,0.35)',
                flexDirection: 'row',
            }}>

                {/* ── Candidate List ──────────────────────── */}
                <div style={{
                    width: '100%',
                    maxWidth: '100%',
                    flexShrink: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                }}>
                    {/* List header */}
                    <div style={{
                        padding: '18px 20px 14px',
                        borderBottom: '1px solid rgba(255,255,255,0.05)',
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        flexShrink: 0,
                    }}>
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '8px',
                            fontSize: '0.75rem', fontWeight: 700,
                            textTransform: 'uppercase', letterSpacing: '0.8px',
                            color: 'var(--text-muted)',
                        }}>
                            <Users size={13} />
                            Candidates
                        </div>
                        <div style={{
                            background: 'rgba(34,211,238,0.1)',
                            border: '1px solid rgba(34,211,238,0.2)',
                            borderRadius: '12px', padding: '2px 10px',
                            fontSize: '0.7rem', fontWeight: 800,
                            color: 'var(--neon-cyan)',
                        }}>
                            {displayList.length}
                        </div>
                    </div>

                    {/* Scrollable card list */}
                    <div style={{
                        flex: 1,
                        overflowY: 'auto',
                        padding: '14px 14px 20px',
                        scrollbarWidth: 'thin',
                        scrollbarColor: 'rgba(255,255,255,0.07) transparent',
                    }}>
                        {displayList.length === 0 && (
                            <div style={{
                                display: 'flex', flexDirection: 'column',
                                alignItems: 'center', justifyContent: 'center',
                                height: '200px', gap: '12px',
                                color: 'var(--text-muted)', textAlign: 'center',
                            }}>
                                <div style={{
                                    width: '48px', height: '48px', borderRadius: '50%',
                                    background: 'rgba(255,255,255,0.03)',
                                    border: '1px solid rgba(255,255,255,0.07)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                }}>
                                    <Sparkles size={20} style={{ color: 'rgba(34,211,238,0.3)' }} />
                                </div>
                                <div>
                                    <p style={{ fontSize: '0.88rem', fontWeight: 600, marginBottom: '4px' }}>
                                        No candidates found
                                    </p>
                                    <p style={{ fontSize: '0.75rem', color: 'rgba(148,163,184,0.5)' }}>
                                        Try adjusting your filters
                                    </p>
                                </div>
                            </div>
                        )}

                        {displayList.map((candidate, idx) => (
                            <ApplicantCard
                                key={candidate.id || `candidate-${idx}`}
                                candidate={candidate}
                                isSelected={selectedId === candidate.id}
                                onClick={() => setSelectedId(candidate.id)}
                            />
                        ))}
                    </div>
                </div>
            </div>

            {/* Real-time Notifications */}
            <RealtimeNotifications events={events} isConnected={isConnected} />
        </div>
    );
}
