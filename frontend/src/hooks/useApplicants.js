import { useState, useEffect, useCallback, useMemo } from 'react';
import { endpoints, API_BASE } from '../api';
function deriveStatus(candidate) {
  const hrDec = candidate.hr_decision;
  if (hrDec === 'selected') return 'Shortlisted';
  if (hrDec === 'rejected') return 'Rejected';

  const finalDec = candidate.ai_report?.final_decision;
  if (typeof finalDec === 'string') {
    if (finalDec.toLowerCase().includes('reject')) return 'Rejected';
    if (finalDec.toLowerCase().includes('shortlist') || finalDec.toLowerCase().includes('select')) return 'Shortlisted';
  }

  const s = (candidate.status || '').toLowerCase();
  if (s === 'ai_reviewed') return 'Under Review';
  if (s === 'rejected') return 'Rejected';
  if (s === 'shortlisted' || s === 'selected') return 'Shortlisted';
  return 'Under Review';
}

/**
 * Builds a rich score breakdown from the AI report sub-agents.
 * Normalises all values to 0–100.
 * Supports multiple data formats from different API versions.
 */
function buildScoreBreakdown(candidate) {
  const report = candidate.ai_report || {};
  const tech = report.tech || {};
  const screener = report.screener || {};
  const culture = report.culture || {};

  const normalize = (val, max = 10) => {
    if (typeof val !== 'number') return 0;
    return Math.min(100, Math.round(max === 10 ? val * 10 : val));
  };

  // Try to get scores from various possible locations in the API response
  const skills = 
    candidate.tech_score ?? 
    candidate.skills_score ??
    normalize(tech.technical_score ?? tech.score) ?? 
    0;

  const projects = 
    candidate.project_score ?? 
    normalize(tech.project_score ?? screener.score) ?? 
    0;

  const aptitude = 
    candidate.aptitude_score ?? 
    normalize(screener.aptitude_score ?? screener.score) ?? 
    0;

  const growthPotential = 
    candidate.growth_score ?? 
    candidate.culture_score ??
    normalize(culture.culture_score ?? culture.score) ?? 
    0;

  return {
    skills: typeof skills === 'number' ? Math.min(100, Math.max(0, skills)) : 0,
    projects: typeof projects === 'number' ? Math.min(100, Math.max(0, projects)) : 0,
    aptitude: typeof aptitude === 'number' ? Math.min(100, Math.max(0, aptitude)) : 0,
    growthPotential: typeof growthPotential === 'number' ? Math.min(100, Math.max(0, growthPotential)) : 0,
  };
}

/**
 * Generates an AI summary from available report data
 */
function buildAISummary(candidate) {
  const report = candidate.ai_report || {};
  const ragReasoning = report.rag_reasoning;
  if (ragReasoning && typeof ragReasoning === 'string' && ragReasoning.length > 20) {
    return ragReasoning.slice(0, 280) + (ragReasoning.length > 280 ? '...' : '');
  }
  const finalDec = report.final_decision;
  if (finalDec && typeof finalDec === 'string' && finalDec.length > 20) {
    return finalDec.slice(0, 280) + (finalDec.length > 280 ? '...' : '');
  }
  // Support both flattened (new API) and nested (old API) formats
  const name = candidate.name || candidate.parsed_data?.name || 'This candidate';
  const skills = (candidate.skills || candidate.parsed_data?.skills || []).slice(0, 3).join(', ') || 'various technologies';
  const score = candidate.aiScore || candidate.match_score || 0;
  return `${name} demonstrates proficiency in ${skills}. The AI pipeline scored them ${score}/100 based on technical depth, project portfolio, and cultural alignment with the role requirements.`;
}

/**
 * Maps raw MongoDB candidate document to a clean UI model.
 * Supports both flattened (new API) and nested (old API) response formats.
 */
function normalizeCandidate(raw) {
  // Support both flattened and nested data formats
  const parsed = raw.parsed_data || {};
  const skillsFromFlat = raw.skills || [];
  const skillsFromNested = parsed.skills || [];
  const allSkillsList = skillsFromFlat.length > 0 ? skillsFromFlat : skillsFromNested;
  
  const softSkillsList = parsed.soft_skills || [];
  const allSkills = [...new Set([...allSkillsList, ...softSkillsList])].slice(0, 8);
  const breakdown = buildScoreBreakdown(raw);

  return {
    id: raw.candidate_id || raw._id,
    name: raw.name || parsed.name || 'Unknown Candidate',
    email: raw.email || parsed.email || 'No email on file',
    role: (parsed.roles || [])[0] || 'Software Engineer',
    status: deriveStatus(raw),
    aiScore: raw.aiScore ?? raw.match_score ?? 0,
    skills: allSkills,
    breakdown,
    aiSummary: buildAISummary(raw),
    insightText: raw.ai_report?.rag_reasoning
      ? 'Based on RAG + multi-agent evaluation'
      : 'Based on skills + project gaps',
    raw,
  };
}

export function useApplicants() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState(null); // { type: 'success'|'error', msg }

  // ── Fetch all candidates ──────────────────────────────────────────────
  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(endpoints.candidates);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const rawData = await res.json();
      
      let dataArray = [];
      if (Array.isArray(rawData)) {
        dataArray = rawData;
      } else if (rawData && typeof rawData === 'object') {
        dataArray = rawData.items || rawData.candidates || rawData.data || [];
      }

      const normalized = dataArray.map(normalizeCandidate);
      setCandidates(normalized);
      // Auto-select first if list is non-empty and nothing selected
      setSelectedId(prev => prev ?? (normalized[0]?.id || null));
    } catch (err) {
      setError(err.message || 'Failed to load candidates');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCandidates(); }, [fetchCandidates]);

  // ── Filtered + searched list ──────────────────────────────────────────
  const filteredCandidates = useMemo(() => {
    let list = candidates;
    if (statusFilter !== 'All') {
      list = list.filter(c => c.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        c.skills.some(s => s.toLowerCase().includes(q))
      );
    }
    return list;
  }, [candidates, statusFilter, searchQuery]);

  // ── Selected candidate ────────────────────────────────────────────────
  const selectedCandidate = useMemo(
    () => candidates.find(c => c.id === selectedId) ?? null,
    [candidates, selectedId]
  );

  // ── HR Decision: Shortlist / Reject ───────────────────────────────────
  const makeDecision = useCallback(async (candidateId, decision, reason = '') => {
    setActionLoading(true);
    setActionFeedback(null);
    try {
      const res = await fetch(`${API_BASE}/api/candidates/${candidateId}/decision`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reason }),
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      
      // Map decision to UI status
      const newStatus = decision === 'selected' ? 'Shortlisted' : 'Rejected';
      
      // Optimistically update BOTH all candidates and filtered list
      setCandidates(prev => prev.map(c => {
        if (c.id !== candidateId) return c;
        return {
          ...c,
          status: newStatus,
          raw: { 
            ...c.raw, 
            hr_decision: decision,
            ai_report: {
              ...c.raw?.ai_report,
              final_decision: decision === 'selected' ? 'SHORTLISTED' : 'REJECTED'
            }
          },
        };
      }));

      setActionFeedback({
        type: 'success',
        msg: decision === 'selected' ? '✓ Candidate shortlisted!' : '✓ Candidate rejected.',
      });
      
      // Refetch after delay to ensure database is updated
      setTimeout(() => { fetchCandidates(); }, 500);
    } catch (err) {
      setActionFeedback({ type: 'error', msg: err.message });
      // On error, refetch to sync state
      setTimeout(() => { fetchCandidates(); }, 1000);
    } finally {
      setActionLoading(false);
      setTimeout(() => setActionFeedback(null), 3000);
    }
  }, [fetchCandidates]);

  // ── Delete candidate ──────────────────────────────────────────────────
  const deleteCandidate = useCallback(async (candidateId) => {
    setActionLoading(true);
    try {
      await fetch(`${API_BASE}/api/candidates/${candidateId}`, { method: 'DELETE' });
      setCandidates(prev => prev.filter(c => c.id !== candidateId));
      if (selectedId === candidateId) setSelectedId(null);
      setActionFeedback({ type: 'success', msg: '✓ Candidate removed.' });
    } catch (err) {
      setActionFeedback({ type: 'error', msg: err.message });
    } finally {
      setActionLoading(false);
      setTimeout(() => setActionFeedback(null), 3000);
    }
  }, [selectedId]);

  return {
    candidates: filteredCandidates,
    allCandidates: candidates,
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
    deleteCandidate,
    refetch: fetchCandidates,
  };
}
