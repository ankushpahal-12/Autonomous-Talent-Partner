import { useState, useEffect, useMemo, useCallback } from 'react';
import { endpoints } from '../api';

function normalizeCandidateDetail(raw) {
  const parsed = raw.parsed_data || {};
  const aiReport = raw.ai_report || {};
  
  return {
    // Core Identity
    id: raw._id,
    name: parsed.name || 'Unknown',
    email: parsed.email || '',
    phone: parsed.phone || '',
    role: parsed.current_role || parsed.title || '',
    location: parsed.location || '',

    // Scores & Status
    matchScore: raw.match_score || 0,
    status: raw.status || 'ai_reviewed',
    hrDecision: raw.hr_decision || null,

    // AI Analysis
    aiScore: aiReport.final_score || raw.match_score || 0,
    aiSummary: aiReport.executive_summary || 'No summary available',
    aiRecommendation: aiReport.recommendation || 'Review candidate profile',
    
    // Score Breakdown
    breakdown: {
      skills: aiReport.breakdown?.skills || 0,
      projects: aiReport.breakdown?.projects || 0,
      aptitude: aiReport.breakdown?.aptitude || 0,
      growthPotential: aiReport.breakdown?.growth_potential || 0,
    },

    // Skills & Experience
    skills: parsed.skills || [],
    experience_summary: parsed.experience || [],
    education: parsed.education || [],
    certifications: parsed.certifications || [],
    years_of_experience: parsed.years_of_experience || 0,

    // Enrichment Data
    github_profile: aiReport.github_analysis?.profile_url || null,
    github_languages: aiReport.github_analysis?.languages || [],
    github_repos: aiReport.github_analysis?.top_repos || [],
    
    // Raw Data (for extended inspection)
    raw: raw,
    fullAiReport: aiReport,
  };
}

function extractRagReasoning(candidateDetail) {
  return candidateDetail.raw?.ai_report?.rag_reasoning || null;
}

function getDecisionHistory(candidateDetail) {
  const history = [];
  
  if (candidateDetail.raw.hr_decision) {
    history.push({
      type: 'hr_decision',
      decision: candidateDetail.raw.hr_decision,
      timestamp: candidateDetail.raw.updated_at,
      by: 'HR User',
    });
  }
  
  if (candidateDetail.raw.ai_report?.final_decision) {
    history.push({
      type: 'ai_evaluation',
      decision: candidateDetail.raw.ai_report.final_decision,
      timestamp: candidateDetail.raw.ai_report.created_at,
      by: 'AI System',
    });
  }
  
  return history.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

// ─────────────────────────────────────────────────────────────────────
// HOOK
// ─────────────────────────────────────────────────────────────────────

export function useCandidateDetail(candidateId) {
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(!!candidateId);
  const [error, setError] = useState(null);
  const [enriching, setEnriching] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState(null);

  // ─────────────────────────────────────────────────────────────────────
  // FETCH CANDIDATE
  // ─────────────────────────────────────────────────────────────────────

  const fetchCandidate = useCallback(async (id) => {
    if (!id) {
      setCandidate(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setActionFeedback(null);

    try {
      const res = await fetch(`${endpoints.candidates}/${id}`);
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      
      const raw = await res.json();
      const normalized = normalizeCandidateDetail(raw);
      setCandidate(normalized);
    } catch (err) {
      setError(err.message || 'Failed to fetch candidate details');
      setCandidate(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch when candidateId changes
  useEffect(() => {
    fetchCandidate(candidateId);
  }, [candidateId, fetchCandidate]);

  // ─────────────────────────────────────────────────────────────────────
  // DECISION ACTIONS
  // ─────────────────────────────────────────────────────────────────────

  const makeDecision = useCallback(async (decision) => {
    if (!candidate) return;

    setActionLoading(true);
    setActionFeedback(null);

    try {
      const res = await fetch(
        `${endpoints.candidates}/${candidate.id}/decision`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ decision, candidate_id: candidate.id }),
        }
      );

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || `Error: ${res.status}`);
      }

      setActionFeedback({
        type: 'success',
        msg: `Candidate ${decision === 'selected' ? 'shortlisted' : 'rejected'} successfully!`,
      });

      // Refetch candidate data
      await new Promise(resolve => setTimeout(resolve, 500));
      await fetchCandidate(candidate.id);
    } catch (err) {
      setActionFeedback({
        type: 'error',
        msg: err.message || 'Failed to save decision',
      });
    } finally {
      setActionLoading(false);
    }
  }, [candidate, fetchCandidate]);

  const shortlistCandidate = useCallback(() => {
    return makeDecision('selected');
  }, [makeDecision]);

  const rejectCandidate = useCallback(() => {
    return makeDecision('rejected');
  }, [makeDecision]);

  // ─────────────────────────────────────────────────────────────────────
  // ENRICHMENT
  // ─────────────────────────────────────────────────────────────────────

  const enrichWithGitHub = useCallback(async () => {
    if (!candidate) return;

    setEnriching(true);
    try {
      // This would trigger backend to fetch GitHub stats if email has GH profile
      const res = await fetch(
        `${endpoints.candidates}/${candidate.id}/enrich`,
        { method: 'POST' }
      );

      if (res.ok) {
        await fetchCandidate(candidate.id);
      }
    } catch (err) {
      console.error('Enrichment failed:', err);
    } finally {
      setEnriching(false);
    }
  }, [candidate, fetchCandidate]);

  // ─────────────────────────────────────────────────────────────────────
  // COMPUTED VALUES (Memoized)
  // ─────────────────────────────────────────────────────────────────────

  const enrichmentInfo = useMemo(() => {
    if (!candidate) return null;

    return {
      hasGitHub: !!candidate.github_profile,
      gitHubLanguages: candidate.github_languages,
      gitHubRepos: candidate.github_repos,
      isEnriched: !!candidate.fullAiReport.github_analysis,
    };
  }, [candidate]);

  const decisionHistory = useMemo(() => {
    if (!candidate) return [];
    return getDecisionHistory(candidate);
  }, [candidate]);

  const ragReasoning = useMemo(() => {
    if (!candidate) return null;
    return extractRagReasoning(candidate);
  }, [candidate]);

  const scoreColor = useMemo(() => {
    if (!candidate) return 'rgba(255,255,255,0.5)';
    
    const score = candidate.aiScore;
    if (score >= 80) return 'var(--neon-cyan)';
    if (score >= 60) return 'var(--neon-amber)';
    return '#f43f5e';
  }, [candidate]);

  const isShortlisted = useMemo(() => {
    if (!candidate) return false;
    return candidate.status === 'Shortlisted' || candidate.hrDecision === 'selected';
  }, [candidate]);

  const isRejected = useMemo(() => {
    if (!candidate) return false;
    return candidate.status === 'Rejected' || candidate.hrDecision === 'rejected';
  }, [candidate]);

  const canMakeDecision = useMemo(() => {
    return !isShortlisted && !isRejected;
  }, [isShortlisted, isRejected]);

  // ─────────────────────────────────────────────────────────────────────
  // PUBLIC API
  // ─────────────────────────────────────────────────────────────────────

  return {
    // State
    candidate,
    loading,
    error,
    enriching,
    actionLoading,
    actionFeedback,

    // Enrichment
    enrichmentInfo,
    enrichWithGitHub,

    // History & Analysis
    decisionHistory,
    ragReasoning,

    // Visual Helpers
    scoreColor,

    // Decision Helpers
    isShortlisted,
    isRejected,
    canMakeDecision,

    // Actions
    refetch: () => fetchCandidate(candidateId),
    makeDecision,
    shortlistCandidate,
    rejectCandidate,
    clearFeedback: () => setActionFeedback(null),

    // Helpers
    hasData: !!candidate,
    isEmpty: !candidate,
  };
}
