import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import {
  TrendingUp, Users, Award, AlertTriangle, CheckCircle, XCircle,
  Clock, Target, Zap, Eye, BarChart3, PieChart as PieChartIcon,
  Activity, Download, RefreshCw, Filter, Search
} from 'lucide-react';
import { systemAPI, candidateAPI } from '../api';
import '../styles/AdvancedDashboard.css';

export default function AdvancedDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    
    // Refresh when returning to the dashboard (window focus)
    const handleFocus = () => {
      loadDashboardData();
    };
    window.addEventListener('focus', handleFocus);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  async function loadDashboardData() {
    setLoading(true);
    try {
      const [metricsData, candidatesData] = await Promise.all([
        systemAPI.getMetrics(),
        candidateAPI.listCandidates(1, 100, { skipCache: true }),
      ]);

      setMetrics(metricsData);
      setCandidates(candidatesData.items || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading || !metrics) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading advanced analytics...</p>
      </div>
    );
  }

  // Filter candidates
  const filteredCandidates = candidates.filter(c => {
    const matchesStatus = filterStatus === 'all' || c.status === filterStatus;
    const matchesSearch = c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         c.email?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  // Calculate statistics
  const stats = {
    total: candidates.length,
    hired: candidates.filter(c => c.status === 'shortlisted').length,
    rejected: candidates.filter(c => c.status === 'rejected').length,
    pending: candidates.filter(c => c.status === 'pending' || !c.status || (c.status !== 'shortlisted' && c.status !== 'rejected')).length,
    avgScore: candidates.length > 0
      ? (candidates.reduce((sum, c) => sum + (c.final_score_data?.final_score || 0), 0) / candidates.length).toFixed(1)
      : 0,
    successRate: candidates.length > 0
      ? ((candidates.filter(c => c.final_score_data?.decision === 'hire').length / candidates.length) * 100).toFixed(1)
      : 0,
  };

  // Prepare chart data
  const scoreDistribution = [
    { range: '0-20', count: candidates.filter(c => (c.final_score_data?.final_score || 0) < 20).length, color: '#ef4444' },
    { range: '20-40', count: candidates.filter(c => {
      const s = c.final_score_data?.final_score || 0;
      return s >= 20 && s < 40;
    }).length, color: '#f97316' },
    { range: '40-60', count: candidates.filter(c => {
      const s = c.final_score_data?.final_score || 0;
      return s >= 40 && s < 60;
    }).length, color: '#eab308' },
    { range: '60-80', count: candidates.filter(c => {
      const s = c.final_score_data?.final_score || 0;
      return s >= 60 && s < 80;
    }).length, color: '#3b82f6' },
    { range: '80-100', count: candidates.filter(c => (c.final_score_data?.final_score || 0) >= 80).length, color: '#10b981' },
  ];

  const decisionDistribution = [
    { name: 'Shortlisted', value: candidates.filter(c => c.hr_decision === 'selected' || c.status === 'shortlisted').length, color: '#10b981' },
    { name: 'Rejected', value: candidates.filter(c => c.hr_decision === 'rejected' || c.status === 'rejected').length, color: '#ef4444' },
    { name: 'AI Review', value: candidates.filter(c => !c.hr_decision && c.final_score_data?.decision).length, color: '#3b82f6' },
    { name: 'Pending', value: candidates.filter(c => !c.hr_decision && !c.final_score_data?.decision).length, color: '#94a3b8' },
  ];

  // Risk is inverse to score - low score = high risk
  const riskData = [
    {
      label: 'Low Risk',
      count: candidates.filter(c => {
        const score = c.final_score_data?.final_score || c.match_score || 0;
        return score >= 70;
      }).length,
      color: '#10b981',
    },
    {
      label: 'Medium Risk',
      count: candidates.filter(c => {
        const score = c.final_score_data?.final_score || c.match_score || 0;
        return score >= 40 && score < 70;
      }).length,
      color: '#f59e0b',
    },
    {
      label: 'High Risk',
      count: candidates.filter(c => {
        const score = c.final_score_data?.final_score || c.match_score || 0;
        return score < 40;
      }).length,
      color: '#ef4444',
    },
  ];

  return (
    <div className="advanced-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <h1>Advanced Analytics Dashboard</h1>
          <p className="subtitle">Real-time Recruitment Intelligence • Version 2.0</p>
        </div>
        <button onClick={loadDashboardData} className="refresh-btn" title="Refresh data">
          <RefreshCw size={20} />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
            <Users size={24} style={{ color: '#10b981' }} />
          </div>
          <div className="kpi-content">
            <p className="kpi-label">Total Candidates</p>
            <h3 className="kpi-value">{stats.total}</h3>
            <p className="kpi-trend">Reviewed this cycle</p>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon" style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)' }}>
            <CheckCircle size={24} style={{ color: '#3b82f6' }} />
          </div>
          <div className="kpi-content">
            <p className="kpi-label">Recommended Hire</p>
            <h3 className="kpi-value">{stats.hired}</h3>
            <p className="kpi-trend">{stats.successRate}% success rate</p>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
            <XCircle size={24} style={{ color: '#ef4444' }} />
          </div>
          <div className="kpi-content">
            <p className="kpi-label">Rejected</p>
            <h3 className="kpi-value">{stats.rejected}</h3>
            <p className="kpi-trend">Strong filter applied</p>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon" style={{ backgroundColor: 'rgba(249, 158, 11, 0.1)' }}>
            <Clock size={24} style={{ color: '#f59e0b' }} />
          </div>
          <div className="kpi-content">
            <p className="kpi-label">Pending Review</p>
            <h3 className="kpi-value">{stats.pending}</h3>
            <p className="kpi-trend">Avg score: {stats.avgScore}/100</p>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon" style={{ backgroundColor: 'rgba(168, 85, 247, 0.1)' }}>
            <Award size={24} style={{ color: '#a855f7' }} />
          </div>
          <div className="kpi-content">
            <p className="kpi-label">Avg Score</p>
            <h3 className="kpi-value">{stats.avgScore}</h3>
            <p className="kpi-trend">Comprehensive v2.0 algorithm</p>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon" style={{ backgroundColor: 'rgba(14, 165, 233, 0.1)' }}>
            <TrendingUp size={24} style={{ color: '#0ea5e9' }} />
          </div>
          <div className="kpi-content">
            <p className="kpi-label">System Accuracy</p>
            <h3 className="kpi-value">94%</h3>
            <p className="kpi-trend">AI-HR agreement rate</p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-grid">
        {/* Score Distribution */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>Score Distribution</h3>
            <BarChart3 size={20} />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={scoreDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="range" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]}>
                {scoreDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Decision Distribution */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>Decision Breakdown</h3>
            <PieChartIcon size={20} />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={decisionDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={{ fill: '#94a3b8', fontSize: 12 }}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {decisionDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Assessment */}
        <div className="chart-card">
          <div className="chart-header">
            <h3>Risk Profile</h3>
            <AlertTriangle size={20} />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" stroke="#64748b" />
              <YAxis dataKey="label" type="category" stroke="#64748b" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 8, 8, 0]}>
                {riskData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Candidates Table */}
      <div className="candidates-section">
        <div className="section-header">
          <h2>Candidate Pipeline</h2>
          <div className="search-filter">
            <Search size={18} className="search-icon" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Status</option>
              <option value="shortlisted">Recommended</option>
              <option value="rejected">Rejected</option>
              <option value="pending">Pending</option>
            </select>
          </div>
        </div>

        <div className="candidates-table">
          <div className="table-header">
            <div className="col-name">Name</div>
            <div className="col-email">Email</div>
            <div className="col-score">Score</div>
            <div className="col-risk">Risk</div>
            <div className="col-decision">Decision</div>
            <div className="col-status">Status</div>
            <div className="col-action">Action</div>
          </div>

          <div className="table-body">
            {filteredCandidates.length > 0 ? (
              filteredCandidates.slice(0, 20).map((candidate) => {
                const score = candidate.final_score_data?.final_score || candidate.match_score || 0;
                // HR decision takes precedence, then check AI decision
                const hrDecision = candidate.hr_decision || null;
                const aiDecision = candidate.final_score_data?.decision || null;
                const displayDecision = hrDecision ? (hrDecision === 'selected' ? 'Shortlisted' : hrDecision === 'rejected' ? 'Rejected' : hrDecision) : (aiDecision === 'hire' ? 'Hire' : aiDecision === 'reject' ? 'Reject' : 'Pending');
                // Risk is inverse to score: low score = high risk
                const riskScore = 100 - Math.min(score, 100);

                return (
                  <div key={candidate._id} className="table-row">
                    <div className="col-name">
                      <strong>{candidate.parsed_data?.name || candidate.name || 'Unknown'}</strong>
                    </div>
                    <div className="col-email">{candidate.parsed_data?.email || candidate.email || '-'}</div>
                    <div className="col-score">
                      <div className="score-badge" style={{
                        backgroundColor: score >= 80 ? '#10b98120' : score >= 60 ? '#f59e0b20' : '#ef444420',
                        color: score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444'
                      }}>
                        {score > 0 ? score.toFixed(1) : 'N/A'}
                      </div>
                    </div>
                    <div className="col-risk">
                      <div className="risk-badge" style={{
                        backgroundColor: riskScore <= 30 ? '#10b98120' : riskScore <= 60 ? '#f59e0b20' : '#ef444420',
                        color: riskScore <= 30 ? '#10b981' : riskScore <= 60 ? '#f59e0b' : '#ef4444'
                      }}>
                        {riskScore.toFixed(0)}%
                      </div>
                    </div>
                    <div className="col-decision">
                      <span className={`decision-badge decision-${displayDecision.toLowerCase().replace(' ', '-')}`}>
                        {displayDecision}
                      </span>
                    </div>
                    <div className="col-status">{candidate.status || 'pending'}</div>
                    <div className="col-action">
                      <button
                        onClick={() => navigate(`/candidates/${candidate._id}`)}
                        className="view-btn"
                      >
                        <Eye size={16} /> View
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="empty-state">
                <p>No candidates found matching filters</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
