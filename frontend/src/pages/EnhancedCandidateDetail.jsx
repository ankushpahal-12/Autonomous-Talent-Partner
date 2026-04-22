import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
  ComposedChart, ScatterChart, Scatter
} from 'recharts';
import {
  ArrowLeft, Download, Trash2, RefreshCw, Share2, Mail, Phone, Briefcase, Award,
  Code, Users, Target, AlertTriangle, CheckCircle, Clock, TrendingUp, Zap,
  ExternalLink, Copy, FileText, Globe, MapPin
} from 'lucide-react';
import { candidateAPI } from '../api';

// Custom Github icon
const Github = ({ size = 24, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

// Custom Linkedin icon
const Linkedin = ({ size = 24, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect width="4" height="12" x="2" y="9" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

export default function EnhancedCandidateDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [enrichProgress, setEnrichProgress] = useState(0);

  useEffect(() => {
    loadCandidate();
  }, [id]);

  async function loadCandidate() {
    setLoading(true);
    try {
      const data = await candidateAPI.getCandidate(id, { skipCache: true });
      setCandidate(data);
    } catch (err) {
      console.error('Failed to load candidate:', err);
      alert('Failed to load candidate details');
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await candidateAPI.reviewCandidate(id);
      alert('AI review triggered successfully');
      setTimeout(loadCandidate, 2000);
    } catch (err) {
      alert('Failed to trigger review: ' + err.message);
    } finally {
      setRefreshing(false);
    }
  }

  async function handleEnrich() {
    setEnriching(true);
    setEnrichProgress(0);
    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setEnrichProgress(prev => Math.min(prev + Math.random() * 30, 90));
      }, 500);

      // Call enrich API
      await candidateAPI.enrichCandidate(id);
      clearInterval(progressInterval);
      
      // Complete the progress bar
      setEnrichProgress(100);
      
      // Show success and reload
      setTimeout(() => {
        alert('Candidate enriched successfully with GitHub & LinkedIn data');
        loadCandidate();
      }, 300);
    } catch (err) {
      alert('Failed to enrich candidate: ' + err.message);
    } finally {
      setTimeout(() => {
        setEnriching(false);
        setEnrichProgress(0);
      }, 1500);
    }
  }

  async function handleDecision(decision) {
    setDecisionLoading(true);
    try {
      await candidateAPI.recordDecision(id, decision, 'HR Review Decision');
      // Reload candidate data immediately after decision
      await new Promise(resolve => setTimeout(resolve, 500));
      await loadCandidate();
      alert(`Candidate marked as ${decision}`);
    } catch (err) {
      alert('Failed to record decision: ' + err.message);
    } finally {
      setDecisionLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <div className="w-10 h-10 border-4 border-slate-700 border-t-cyan-500 rounded-full animate-spin"></div>
        <p className="text-slate-400 text-sm">Loading candidate profile...</p>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4 text-center">
        <AlertTriangle size={48} className="text-red-500" />
        <h2 className="text-white text-lg">Candidate Not Found</h2>
        <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 font-medium hover:bg-slate-700 hover:border-slate-600 transition">
          <ArrowLeft size={18} /> Back to Dashboard
        </button>
      </div>
    );
  }

  const parsed = candidate.parsed_data || {};
  const scoring = candidate.final_score_data || {};
  const comprehensive = candidate.comprehensive_scoring || {};
  const riskData = candidate.risk_assessment || {};
  const neoData = candidate.neo4j_analysis || {};

  // Prepare radar chart data
  const radarData = [
    { category: 'Technical', value: comprehensive.data_aggregation?.technical_depth || 0, fullMark: 100 },
    { category: 'Culture', value: comprehensive.data_aggregation?.culture_alignment || 0, fullMark: 100 },
    { category: 'Experience', value: comprehensive.data_aggregation?.role_fit || 0, fullMark: 100 },
    { category: 'Code Quality', value: comprehensive.data_aggregation?.code_quality || 0, fullMark: 100 },
    { category: 'Consistency', value: (100 - (comprehensive.consistency_analysis?.red_flags?.length || 0) * 10), fullMark: 100 },
  ];

  // Risk breakdown
  const riskBreakdown = [
    { name: 'Skill Gap', value: riskData.skill_gap_risk * 100 || 0, color: '#ef4444' },
    { name: 'Experience', value: riskData.experience_risk * 100 || 0, color: '#f59e0b' },
    { name: 'Consistency', value: riskData.consistency_risk * 100 || 0, color: '#3b82f6' },
  ];

  // Timeline data from feedback
  const feedbackHist = candidate.scores_history || [];
  const timelineData = feedbackHist.slice(-10).map((s, i) => ({
    day: `Day ${i + 1}`,
    score: s.final_score || 0,
    confidence: (Math.random() * 0.3 + 0.6) * 100,
  }));

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-6 md:p-8">
      {/* Header */}
      <div className="flex items-center gap-6 mb-8 flex-wrap">
        <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 font-medium hover:bg-slate-700 hover:border-slate-600 transition">
          <ArrowLeft size={20} /> Back
        </button>
        <div className="flex-1">
          <h1 className="text-4xl font-bold text-slate-50 m-0">{parsed.name || 'Unknown Candidate'}</h1>
          <p className="text-slate-400 text-sm mt-2 m-0">Comprehensive v2.0 Analysis Report</p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleRefresh} className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 font-medium hover:bg-slate-700 disabled:opacity-50 transition" disabled={refreshing}>
            <RefreshCw size={18} /> {refreshing ? 'Analyzing...' : 'Refresh'}
          </button>
          <button onClick={handleEnrich} className="flex items-center gap-2 px-4 py-2 bg-cyan-600 border border-cyan-500 rounded-lg text-cyan-100 font-medium hover:bg-cyan-700 hover:border-cyan-400 disabled:opacity-50 transition" disabled={enriching}>
            <Zap size={18} /> {enriching ? 'Enriching...' : 'Enrich'}
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 font-medium hover:bg-slate-700 transition">
            <Share2 size={18} /> Share
          </button>
        </div>
      </div>

      {/* Enrichment Progress Bar */}
      {enriching && (
        <div className="mb-8">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Zap size={18} className="text-cyan-400 animate-pulse" />
                <span className="text-slate-200 font-medium">Enriching candidate profile...</span>
              </div>
              <span className="text-slate-400 text-sm font-medium">{Math.round(enrichProgress)}%</span>
            </div>
            <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-cyan-500 via-cyan-400 to-blue-500 rounded-full transition-all duration-300 ease-out shadow-lg shadow-cyan-500/50"
                style={{ width: `${enrichProgress}%` }}
              />
            </div>
            <p className="text-slate-400 text-xs mt-2">Fetching GitHub & LinkedIn data...</p>
          </div>
        </div>
      )}

      {/* Score Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-gradient-to-br from-slate-950 to-slate-900 border-2 border-cyan-500 rounded-xl p-6">
          <div className={`text-5xl font-bold font-mono mb-3 ${
            scoring.final_score >= 80 ? 'text-green-500' : scoring.final_score >= 60 ? 'text-amber-500' : 'text-red-500'
          }`}>
            {scoring.final_score || 0}
          </div>
          <div className="text-slate-400 text-xs uppercase tracking-widest mb-2">Final Score</div>
          <div className="text-sm text-slate-300">
            <span className="text-slate-400">Confidence:</span> <strong className="text-cyan-500">{(scoring.confidence_score * 100).toFixed(0)}%</strong>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-900 to-slate-950 border-2 border-slate-700 rounded-xl p-6 hover:border-cyan-500 hover:shadow-lg hover:shadow-cyan-500/10 transition">
          <div className="w-14 h-14 rounded-xl bg-green-500/10 flex items-center justify-center mx-auto mb-3">
            <CheckCircle size={28} className="text-green-500" />
          </div>
          <div className="text-slate-400 text-xs uppercase tracking-widest mb-2 text-center">Decision</div>
          <div className={`text-base font-semibold text-center uppercase tracking-wide ${
            scoring.decision === 'hire' ? 'text-green-500' : scoring.decision === 'reject' ? 'text-red-500' : 'text-blue-500'
          }`}>
            {scoring.decision?.toUpperCase() || 'PENDING'}
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-900 to-slate-950 border-2 border-slate-700 rounded-xl p-6 hover:border-cyan-500 hover:shadow-lg hover:shadow-cyan-500/10 transition">
          <div className="w-14 h-14 rounded-xl bg-red-500/10 flex items-center justify-center mx-auto mb-3">
            <AlertTriangle size={28} className="text-red-500" />
          </div>
          <div className="text-slate-400 text-xs uppercase tracking-widest mb-2 text-center">Risk Level</div>
          <div className={`text-base font-semibold text-center ${
            riskData.overall_risk_score < 0.3 ? 'text-green-500' : riskData.overall_risk_score < 0.6 ? 'text-amber-500' : 'text-red-500'
          }`}>
            {(riskData.overall_risk_score * 100).toFixed(0)}%
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-900 to-slate-950 border-2 border-slate-700 rounded-xl p-6 hover:border-cyan-500 hover:shadow-lg hover:shadow-cyan-500/10 transition">
          <div className="w-14 h-14 rounded-xl bg-cyan-500/10 flex items-center justify-center mx-auto mb-3">
            <TrendingUp size={28} className="text-cyan-500" />
          </div>
          <div className="text-slate-400 text-xs uppercase tracking-widest mb-2 text-center">Learning Curve</div>
          <div className="text-base font-medium text-center text-slate-300">
            {neoData.learning_curve || 'Medium'}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-slate-700 mb-8 flex-wrap">
        <button
          className={`px-5 py-3 font-medium text-sm transition border-b-2 ${activeTab === 'overview' ? 'text-cyan-500 border-cyan-500' : 'text-slate-400 border-transparent hover:text-slate-300'}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`px-5 py-3 font-medium text-sm transition border-b-2 ${activeTab === 'analysis' ? 'text-cyan-500 border-cyan-500' : 'text-slate-400 border-transparent hover:text-slate-300'}`}
          onClick={() => setActiveTab('analysis')}
        >
          Detailed Analysis
        </button>
        <button
          className={`px-5 py-3 font-medium text-sm transition border-b-2 ${activeTab === 'risk' ? 'text-cyan-500 border-cyan-500' : 'text-slate-400 border-transparent hover:text-slate-300'}`}
          onClick={() => setActiveTab('risk')}
        >
          Risk Assessment
        </button>
        <button
          className={`px-5 py-3 font-medium text-sm transition border-b-2 ${activeTab === 'profile' ? 'text-cyan-500 border-cyan-500' : 'text-slate-400 border-transparent hover:text-slate-300'}`}
          onClick={() => setActiveTab('profile')}
        >
          Profile
        </button>
        <button
          className={`px-5 py-3 font-medium text-sm transition border-b-2 ${activeTab === 'external' ? 'text-cyan-500 border-cyan-500' : 'text-slate-400 border-transparent hover:text-slate-300'}`}
          onClick={() => setActiveTab('external')}
        >
          GitHub & LinkedIn
        </button>
      </div>

      {/* Tab Content */}
      <div className="animate-fadeIn">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Radar Chart */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Competency Overview</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="category" stroke="#94a3b8" />
                    <PolarRadiusAxis stroke="#334155" />
                    <Radar
                      name="Score"
                      dataKey="value"
                      stroke="#0ea5e9"
                      fill="#0ea5e9"
                      fillOpacity={0.3}
                    />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Timeline Chart */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Score Timeline</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={timelineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="day" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                    <Area type="monotone" dataKey="score" fill="#0ea5e9" stroke="#0289d8" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Explanation */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">AI Analysis Summary</h3>
              <p className="text-slate-300 leading-relaxed m-0">{scoring.explanation || 'No explanation available'}</p>
            </div>

            {/* ELO Ranking Section */}
            {candidate?.agent_reports?.final_decision?.elo_statement && (
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mt-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0 flex items-center gap-2">
                  <Award size={20} className="text-cyan-500" /> Percentile Ranking
                </h3>
                <div className="bg-slate-700/50 border-l-4 border-cyan-500 p-4 rounded mb-4">
                  <p className="text-slate-300 leading-relaxed m-0">{candidate.agent_reports.final_decision.elo_statement}</p>
                </div>
                {candidate?.agent_reports?.elo_ranking && (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                      <div className="text-slate-400 text-xs uppercase tracking-widest font-medium mb-2">Percentile</div>
                      <div className="text-cyan-500 text-2xl font-bold">{candidate.agent_reports.elo_ranking.percentile?.toFixed(1)}%</div>
                    </div>
                    <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                      <div className="text-slate-400 text-xs uppercase tracking-widest font-medium mb-2">Pool Avg</div>
                      <div className="text-cyan-500 text-2xl font-bold">{candidate.agent_reports.elo_ranking.pool_avg_score?.toFixed(1)}</div>
                    </div>
                    <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                      <div className="text-slate-400 text-xs uppercase tracking-widest font-medium mb-2">Rank</div>
                      <div className="text-cyan-500 text-2xl font-bold">#{candidate.agent_reports.elo_ranking.rank_in_pool}/{candidate.agent_reports.elo_ranking.pool_size}</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Analysis Tab */}
        {activeTab === 'analysis' && (
          <div className="animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Data Aggregation */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h4 className="text-slate-50 text-sm uppercase tracking-widest font-semibold mb-4 m-0">Data Aggregation</h4>
                <div className="flex flex-col gap-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-slate-300">Technical Depth</span>
                      <span className="text-cyan-500 font-semibold text-sm">{comprehensive.data_aggregation?.technical_depth || 0}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400" style={{ width: `${comprehensive.data_aggregation?.technical_depth || 0}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-slate-300">Role Fit</span>
                      <span className="text-cyan-500 font-semibold text-sm">{comprehensive.data_aggregation?.role_fit || 0}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400" style={{ width: `${comprehensive.data_aggregation?.role_fit || 0}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-slate-300">Culture Alignment</span>
                      <span className="text-cyan-500 font-semibold text-sm">{comprehensive.data_aggregation?.culture_alignment || 0}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400" style={{ width: `${comprehensive.data_aggregation?.culture_alignment || 0}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Consistency Analysis */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h4 className="text-slate-50 text-sm uppercase tracking-widest font-semibold mb-4 m-0">Consistency Analysis</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-2 bg-slate-700/50 rounded">
                    <span className="text-slate-300">Timeline Consistent</span>
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-md text-xs font-semibold ${comprehensive.consistency_analysis?.timeline_consistent ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                      {comprehensive.consistency_analysis?.timeline_consistent ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-slate-700/50 rounded">
                    <span className="text-slate-300">Red Flags</span>
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-md text-xs font-semibold ${(comprehensive.consistency_analysis?.red_flags?.length || 0) === 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                      {comprehensive.consistency_analysis?.red_flags?.length || 0}
                    </span>
                  </div>
                  {comprehensive.consistency_analysis?.red_flags?.map((flag, i) => (
                    <div key={i} className="flex items-start gap-2 p-2 bg-red-500/10 rounded border border-red-500/30">
                      <AlertTriangle size={16} className="text-red-500 mt-0.5 flex-shrink-0" />
                      <span className="text-xs text-red-300">{flag}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Neo4j Insights */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h4 className="text-slate-50 text-sm uppercase tracking-widest font-semibold mb-4 m-0">Neo4j Insights</h4>
                <div className="space-y-4">
                  <div>
                    <span className="text-slate-400 text-xs font-medium">Skill Gaps</span>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {neoData.skill_gaps?.slice(0, 3).map((gap, i) => (
                        <span key={i} className="px-2 py-1 bg-slate-700 text-slate-200 rounded-md text-xs">{gap}</span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-xs font-medium">Transferable Skills</span>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {neoData.transferable_skills?.slice(0, 3).map((skill, i) => (
                        <span key={i} className="px-2 py-1 bg-green-500/20 text-green-300 rounded-md text-xs">{skill}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Comparative Analysis */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h4 className="text-slate-50 text-sm uppercase tracking-widest font-semibold mb-4 m-0">Comparative Analysis</h4>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-slate-300">Must-Have Skills</span>
                      <span className="text-cyan-500 font-semibold text-sm">{comprehensive.comparative_analysis?.must_have_coverage_percent || 0}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400" style={{ width: `${comprehensive.comparative_analysis?.must_have_coverage_percent || 0}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-slate-300">Nice-to-Have Skills</span>
                      <span className="text-cyan-500 font-semibold text-sm">{comprehensive.comparative_analysis?.nice_to_have_coverage_percent || 0}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400" style={{ width: `${comprehensive.comparative_analysis?.nice_to_have_coverage_percent || 0}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Risk Tab */}
        {activeTab === 'risk' && (
          <div className="animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Risk Chart */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Risk Breakdown</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={riskBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                    <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]}>
                      {riskBreakdown.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Risk Details */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Risk Assessment Details</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-slate-300">Overall Risk Score</span>
                      <span className="text-sm font-semibold text-slate-400">{(riskData.overall_risk_score * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full" style={{
                        width: `${riskData.overall_risk_score * 100}%`,
                        backgroundColor: riskData.overall_risk_score < 0.3 ? '#10b981' : riskData.overall_risk_score < 0.6 ? '#f59e0b' : '#ef4444'
                      }}></div>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-700/30 border border-slate-700 rounded-lg">
                    <div className="text-sm text-slate-300"><span className="text-slate-400">Confidence Adjustment:</span> 
                      <span className={`ml-2 font-semibold ${riskData.confidence_adjustment > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {riskData.confidence_adjustment > 0 ? '+' : ''}{(riskData.confidence_adjustment * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-slate-300 text-sm font-semibold mb-2 m-0">Red Flags ({riskData.red_flags?.length || 0})</h4>
                    <div className="space-y-2">
                      {riskData.red_flags?.map((flag, i) => (
                        <div key={i} className="flex items-start gap-2 p-2 bg-red-500/10 rounded border border-red-500/30">
                          <AlertTriangle size={16} className="text-red-500 mt-0.5 flex-shrink-0" />
                          <span className="text-xs text-red-300">{flag}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Personal Info */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Personal Information</h3>
                <div className="space-y-3">
                  <div className="pb-3 border-b border-slate-700">
                    <div className="text-xs uppercase text-slate-400 tracking-wide font-medium">Name</div>
                    <div className="text-slate-200 mt-1">{parsed.name || '-'}</div>
                  </div>
                  <div className="pb-3 border-b border-slate-700 flex items-center gap-2">
                    <Mail size={16} className="text-slate-400" />
                    <div>
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium">Email</div>
                      <div className="text-slate-200">{parsed.email || '-'}</div>
                    </div>
                  </div>
                  <div className="pb-3 border-b border-slate-700 flex items-center gap-2">
                    <Phone size={16} className="text-slate-400" />
                    <div>
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium">Phone</div>
                      <div className="text-slate-200">{parsed.phone || 'Not provided'}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin size={16} className="text-slate-400" />
                    <div>
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium">Location</div>
                      <div className="text-slate-200">{parsed.location || 'Not provided'}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Professional Info */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Professional Background</h3>
                <div className="space-y-3">
                  <div className="pb-3 border-b border-slate-700 flex items-center gap-2">
                    <Briefcase size={16} className="text-slate-400" />
                    <div>
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium">Company</div>
                      <div className="text-slate-200">{parsed.current_company || 'Not specified'}</div>
                    </div>
                  </div>
                  <div className="pb-3 border-b border-slate-700 flex items-center gap-2">
                    <Award size={16} className="text-slate-400" />
                    <div>
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium">Role</div>
                      <div className="text-slate-200">{parsed.current_role || 'Not specified'}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <TrendingUp size={16} className="text-slate-400" />
                    <div>
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium">Experience</div>
                      <div className="text-slate-200">{parsed.experience_years || 0} years</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Education */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Education</h3>
                <div className="space-y-3">
                  {parsed.education?.map((edu, i) => (
                    <div key={i} className="pb-3 border-b border-slate-700 last:border-0">
                      <div className="font-semibold text-slate-200 text-sm">{edu.degree}</div>
                      <div className="text-slate-400 text-xs mt-1">{edu.university}</div>
                      <div className="text-slate-500 text-xs mt-1">{edu.graduation_year}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Skills */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Technical Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {parsed.skills?.map((skill, i) => (
                    <span key={i} className="px-3 py-1 bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 rounded-lg text-xs font-medium">{skill}</span>
                  ))}
                </div>
              </div>

              {/* Social Links */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 md:col-span-2">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Social Profiles</h3>
                <div className="flex flex-wrap gap-3">
                  {parsed.github_username && (
                    <a href={`https://github.com/${parsed.github_username}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-lg text-cyan-400 text-sm font-medium transition">
                      <Github size={16} /> GitHub
                    </a>
                  )}
                  {parsed.linkedin_url && (
                    <a href={parsed.linkedin_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-lg text-cyan-400 text-sm font-medium transition">
                      <Linkedin size={16} /> LinkedIn
                    </a>
                  )}
                  {parsed.portfolio_url && (
                    <a href={parsed.portfolio_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-lg text-cyan-400 text-sm font-medium transition">
                      <Globe size={16} /> Portfolio
                    </a>
                  )}
                </div>
              </div>
            </div>

            {/* Projects */}
            {parsed.projects?.length > 0 && (
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <h3 className="text-slate-50 text-base font-semibold mb-4 m-0">Notable Projects</h3>
                <div className="space-y-4">
                  {parsed.projects?.slice(0, 5).map((proj, i) => (
                    <div key={i} className="p-4 bg-slate-700/30 border-l-4 border-cyan-500 rounded">
                      <div className="font-semibold text-slate-200 mb-1">{proj.name}</div>
                      <div className="text-xs text-slate-400 mb-2">{proj.description}</div>
                      <div className="flex flex-wrap gap-1">
                        {proj.technologies?.map((tech, j) => (
                          <span key={j} className="px-2 py-0.5 bg-slate-600/50 text-slate-300 rounded text-xs">{tech}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* External Intelligence Tab */}
        {activeTab === 'external' && (
          <div className="animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* GitHub Intelligence */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Github size={24} className="text-slate-400" />
                  <h3 className="text-slate-50 text-base font-semibold m-0">GitHub Profile</h3>
                </div>
                {candidate?.external_intel?.github ? (
                  <div className="space-y-4">
                    {candidate.external_intel.github.profile_url && (
                      <div className="pb-3 border-b border-slate-700">
                        <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-1">Profile</div>
                        <a href={candidate.external_intel.github.profile_url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 text-sm hover:underline flex items-center gap-2">
                          <ExternalLink size={14} /> Visit Profile
                        </a>
                      </div>
                    )}
                    
                    <div className="pb-3 border-b border-slate-700">
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Repositories</div>
                      <div className="text-slate-200 font-semibold text-lg">{candidate.external_intel.github.repo_count || 0}</div>
                      <div className="text-xs text-slate-400">Total repositories</div>
                    </div>

                    <div className="pb-3 border-b border-slate-700">
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Stars</div>
                      <div className="text-slate-200 font-semibold text-lg">{candidate.external_intel.github.star_count || 0}</div>
                      <div className="text-xs text-slate-400">Total stars received</div>
                    </div>

                    <div className="pb-3 border-b border-slate-700">
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Followers</div>
                      <div className="text-slate-200 font-semibold text-lg">{candidate.external_intel.github.followers || 0}</div>
                      <div className="text-xs text-slate-400">Community followers</div>
                    </div>

                    <div className="pb-3 border-b border-slate-700">
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Languages</div>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {candidate.external_intel.github.languages?.slice(0, 5).map((lang, i) => (
                          <span key={i} className="px-2 py-1 bg-slate-700 text-slate-200 rounded text-xs">{lang}</span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Contribution Score</div>
                      <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-cyan-500 to-cyan-400" style={{ width: `${Math.min((candidate.external_intel.github.star_count || 0) / 10, 100)}%` }}></div>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">{Math.min((candidate.external_intel.github.star_count || 0) / 10, 100).toFixed(0)}% contribution influence</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    <p>No GitHub profile data available</p>
                  </div>
                )}
              </div>

              {/* LinkedIn Intelligence */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Linkedin size={24} className="text-slate-400" />
                  <h3 className="text-slate-50 text-base font-semibold m-0">LinkedIn Profile</h3>
                </div>
                {candidate?.external_intel?.linkedin ? (
                  <div className="space-y-4">
                    {candidate.external_intel.linkedin.profile_url && (
                      <div className="pb-3 border-b border-slate-700">
                        <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-1">Profile</div>
                        <a href={candidate.external_intel.linkedin.profile_url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 text-sm hover:underline flex items-center gap-2">
                          <ExternalLink size={14} /> Visit Profile
                        </a>
                      </div>
                    )}

                    <div className="pb-3 border-b border-slate-700">
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Connections</div>
                      <div className="text-slate-200 font-semibold text-lg">{candidate.external_intel.linkedin.connections || 0}</div>
                      <div className="text-xs text-slate-400">Network size</div>
                    </div>

                    <div className="pb-3 border-b border-slate-700">
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Endorsements</div>
                      <div className="text-slate-200 font-semibold text-lg">{candidate.external_intel.linkedin.endorsement_count || 0}</div>
                      <div className="text-xs text-slate-400">Skills endorsed</div>
                    </div>

                    <div className="pb-3 border-b border-slate-700">
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Recommendations</div>
                      <div className="text-slate-200 font-semibold text-lg">{candidate.external_intel.linkedin.recommendation_count || 0}</div>
                      <div className="text-xs text-slate-400">Professional recommendations</div>
                    </div>

                    {candidate.external_intel.linkedin.headline && (
                      <div className="pb-3 border-b border-slate-700">
                        <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-1">Headline</div>
                        <div className="text-slate-200 text-sm">{candidate.external_intel.linkedin.headline}</div>
                      </div>
                    )}

                    <div>
                      <div className="text-xs uppercase text-slate-400 tracking-wide font-medium mb-2">Profile Strength</div>
                      <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-blue-500 to-blue-400" style={{ width: `${Math.min(((candidate.external_intel.linkedin.connections || 0) / 500) * 100, 100)}%` }}></div>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">{Math.min(((candidate.external_intel.linkedin.connections || 0) / 500) * 100, 100).toFixed(0)}% network strength</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    <p>No LinkedIn profile data available</p>
                  </div>
                )}
              </div>
            </div>

            {/* Summary Scores */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-slate-50 text-base font-semibold mb-6 m-0">External Intelligence Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                  <div className="text-slate-400 text-xs uppercase tracking-widest font-medium mb-2">GitHub Score</div>
                  <div className="text-cyan-400 text-3xl font-bold">{candidate?.external_intel?.github ? Math.min(Math.round(((candidate.external_intel.github.star_count || 0) / 5 + (candidate.external_intel.github.followers || 0) / 2) / 10), 100) : 0}</div>
                  <div className="text-slate-500 text-xs mt-1">out of 100</div>
                </div>
                
                <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                  <div className="text-slate-400 text-xs uppercase tracking-widest font-medium mb-2">LinkedIn Score</div>
                  <div className="text-blue-400 text-3xl font-bold">{candidate?.external_intel?.linkedin ? Math.min(Math.round(((candidate.external_intel.linkedin.connections || 0) / 50 + (candidate.external_intel.linkedin.endorsement_count || 0) / 10) / 2), 100) : 0}</div>
                  <div className="text-slate-500 text-xs mt-1">out of 100</div>
                </div>

                <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                  <div className="text-slate-400 text-xs uppercase tracking-widest font-medium mb-2">Overall Presence</div>
                  <div className="text-green-400 text-3xl font-bold">
                    {(() => {
                      const ghScore = candidate?.external_intel?.github ? Math.min(Math.round(((candidate.external_intel.github.star_count || 0) / 5 + (candidate.external_intel.github.followers || 0) / 2) / 10), 100) : 0;
                      const liScore = candidate?.external_intel?.linkedin ? Math.min(Math.round(((candidate.external_intel.linkedin.connections || 0) / 50 + (candidate.external_intel.linkedin.endorsement_count || 0) / 10) / 2), 100) : 0;
                      return candidate?.external_intel?.github || candidate?.external_intel?.linkedin ? Math.round((ghScore + liScore) / 2) : 0;
                    })()}
                  </div>
                  <div className="text-slate-500 text-xs mt-1">combined score</div>
                </div>

                <div className="bg-slate-700/30 rounded-lg p-4 text-center">
                  <div className="text-slate-400 text-xs uppercase tracking-widest font-medium mb-2">Data Richness</div>
                  <div className={`text-3xl font-bold ${(candidate?.external_intel?.github && candidate?.external_intel?.linkedin) ? 'text-amber-400' : candidate?.external_intel?.github || candidate?.external_intel?.linkedin ? 'text-yellow-400' : 'text-slate-400'}`}>
                    {candidate?.external_intel?.github && candidate?.external_intel?.linkedin ? 'Complete' : candidate?.external_intel?.github || candidate?.external_intel?.linkedin ? 'Partial' : 'None'}
                  </div>
                  <div className="text-slate-500 text-xs mt-1">profile coverage</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Decision Actions */}
      <div className="flex gap-4 mt-10 pt-6 border-t border-slate-700 flex-wrap">
        {candidate.hr_decision ? (
          <div className="flex items-center gap-2 px-6 py-3 bg-slate-700/30 border border-slate-600 rounded-lg text-slate-300 font-semibold">
            <CheckCircle size={18} className={candidate.hr_decision === 'rejected' ? 'text-red-400' : 'text-green-400'} />
            <span>✓ Decision Recorded: {candidate.hr_decision === 'rejected' ? 'Rejected' : candidate.hr_decision === 'selected' ? 'Recommended for Hire' : 'Further Review'}</span>
          </div>
        ) : (
          <>
            <button
              onClick={() => handleDecision('selected')}
              className="flex items-center gap-2 px-6 py-3 bg-green-500/20 hover:bg-green-500/30 border border-green-500/50 hover:border-green-500 rounded-lg text-green-400 font-semibold disabled:opacity-50 transition"
              disabled={decisionLoading}
            >
              <CheckCircle size={18} /> {decisionLoading ? 'Recording...' : 'Recommend for Hire'}
            </button>
            <button
              onClick={() => handleDecision('pending')}
              className="flex items-center gap-2 px-6 py-3 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/50 hover:border-amber-500 rounded-lg text-amber-400 font-semibold disabled:opacity-50 transition"
              disabled={decisionLoading}
            >
              <Clock size={18} /> {decisionLoading ? 'Recording...' : 'Further Review'}
            </button>
            <button
              onClick={() => handleDecision('rejected')}
              className="flex items-center gap-2 px-6 py-3 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 hover:border-red-500 rounded-lg text-red-400 font-semibold disabled:opacity-50 transition"
              disabled={decisionLoading}
            >
              <AlertTriangle size={18} /> {decisionLoading ? 'Recording...' : 'Reject'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
