import { useState, useEffect, useMemo, useCallback } from 'react';
import { endpoints } from '../api';

function calculateStats(candidates = []) {
  if (!Array.isArray(candidates)) candidates = [];
  return {
    total: candidates.length,
    elite: candidates.filter(c => (c.match_score || 0) >= 85).length,
    avgScore: candidates.length 
      ? Math.round(candidates.reduce((acc, c) => acc + (c.match_score || 0), 0) / candidates.length) 
      : 0,
    reviewed: candidates.filter(c => c.status === 'ai_reviewed').length,
  };
}

function buildScoreDistribution(candidates = []) {
  if (!Array.isArray(candidates)) candidates = [];
  const buckets = [
    { name: '0-20', count: 0, fill: '#ef4444', percentage: 0 },      // Red
    { name: '21-40', count: 0, fill: '#f97316', percentage: 0 },     // Orange
    { name: '41-60', count: 0, fill: '#eab308', percentage: 0 },     // Yellow
    { name: '61-80', count: 0, fill: '#22d3ee', percentage: 0 },     // Cyan
    { name: '81-100', count: 0, fill: '#10b981', percentage: 0 }     // Green
  ];

  candidates.forEach((c) => {
    const score = c.match_score || 0;
    if (score <= 20) buckets[0].count++;
    else if (score <= 40) buckets[1].count++;
    else if (score <= 60) buckets[2].count++;
    else if (score <= 80) buckets[3].count++;
    else buckets[4].count++;
  });

  // Calculate percentages
  const total = candidates.length || 1;
  return buckets.map(b => ({
    ...b,
    percentage: Math.round((b.count / total) * 100)
  }));
}

function getTopTalent(candidates = [], limit = 3) {
  if (!Array.isArray(candidates)) candidates = [];
  return [...candidates]
    .sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
    .slice(0, limit)
    .map(c => ({
      id: c.candidate_id || c._id,  // Support both new and legacy API formats
      name: c.name || 'Unknown',     // New format has name at top level
      score: c.match_score || 0,
      skills: (c.skills || []).slice(0, 3),  // New format has skills at top level
    }));
}

function getRecentActivity(candidates = [], limit = 5) {
  if (!Array.isArray(candidates)) candidates = [];
  return [...candidates]
    .sort((a, b) => new Date(b.created_at || b._id) - new Date(a.created_at || a._id))
    .slice(0, limit)
    .map(c => ({
      id: c.candidate_id || c._id,  // Support both new and legacy API formats
      name: c.name || 'Unknown',     // New format has name at top level
      status: c.status || 'pending',
      timestamp: new Date(c.created_at || c._id),
    }));
}

function calculateTrends(candidates = [], previousCandidates = []) {
  if (!Array.isArray(candidates)) candidates = [];
  if (!Array.isArray(previousCandidates)) previousCandidates = [];
  const current = candidates.length;
  const previous = previousCandidates.length;
  const change = current - previous;
  const percentChange = previous > 0 ? Math.round((change / previous) * 100) : 0;

  return {
    totalGrowth: change,
    growthPercent: percentChange,
    isPositive: change >= 0,
  };
}

// ─────────────────────────────────────────────────────────────────────
// HOOK
// ─────────────────────────────────────────────────────────────────────

export function useDashboard() {
  const [candidates, setCandidates] = useState([]);
  const [previousCandidates, setPreviousCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // ─────────────────────────────────────────────────────────────────────
  // FETCH DATA
  // ─────────────────────────────────────────────────────────────────────

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(endpoints.candidates);
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      
      // Note: Save current candidates before updating for trend calculation
      setCandidates((prevCandidates) => {
        setPreviousCandidates(prevCandidates);
        return prevCandidates;
      });
      
      const data = await res.json();
      
      let candidatesArray = [];
      if (Array.isArray(data)) {
        candidatesArray = data;
      } else if (data && typeof data === 'object') {
        candidatesArray = data.items || data.candidates || data.data || [];
      }
      
      setCandidates(candidatesArray);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, []); // ← FIX: Empty dependency array - function doesn't depend on state

  // Initial fetch - runs only once on mount
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]); // ← FIX: Empty dependency array - fetch only once on mount

  // ─────────────────────────────────────────────────────────────────────
  // COMPUTED VALUES (Memoized)
  // ─────────────────────────────────────────────────────────────────────

  const stats = useMemo(() => calculateStats(candidates), [candidates]);
  const scoreDistribution = useMemo(() => buildScoreDistribution(candidates), [candidates]);
  const topTalent = useMemo(() => getTopTalent(candidates), [candidates]);
  const recentActivity = useMemo(() => getRecentActivity(candidates), [candidates]);
  const trends = useMemo(() => calculateTrends(candidates, previousCandidates), [candidates, previousCandidates]);



  const statusBreakdown = useMemo(() => {
    const breakdown = {
      'Under Review': 0,
      'Shortlisted': 0,
      'Rejected': 0,
    };
    
    const candidatesArray = Array.isArray(candidates) ? candidates : [];
    candidatesArray.forEach((c) => {
      const status = c.status || 'Under Review';
      if (Object.prototype.hasOwnProperty.call(breakdown, status)) {
        breakdown[status]++;
      } else {
        breakdown['Under Review']++;
      }
    });

    return breakdown;
  }, [candidates]);


  return {
    // State
    loading,
    error,
    candidates,
    lastUpdated,

    // Analytics
    stats,
    scoreDistribution,
    topTalent,
    recentActivity,
    trends,
    statusBreakdown,

    // Actions
    refetch: fetchDashboardData,

    // Helpers
    hasData: candidates.length > 0,
    isEmpty: candidates.length === 0,
  };
}
