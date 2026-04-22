import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Cell } from 'recharts';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { Mail, Phone, Briefcase, Award, ArrowLeft, Cpu, Heart, CheckCircle, AlertTriangle, Lightbulb, Terminal, Binary, BarChart2, Download, Trash2, RefreshCw, Globe, ChevronDown, FileText, FileCode, Zap } from 'lucide-react';

const API = 'http://127.0.0.1:8000';

// Zap icon inline
const ZapIcon = ({ size = 24, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

const Github = ({ size = 24, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

const Linkedin = ({ size = 24, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect width="4" height="12" x="2" y="9" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

// Helper for parsing text into bullet points with Tailwind styling
const renderBulletPoints = (text) => {
  if (!text) return null;
  
  // First, clean all ** markers and process headings
  let cleanedText = text;
  
  // Split by heading pattern: **SomeText:** or **SomeText**
  const headingPattern = /\*\*([^*]+?)\*\*:?/g;
  const sections = [];
  let lastIndex = 0;
  let match;
  
  // Find all headings
  const headingMatches = [];
  while ((match = headingPattern.exec(text)) !== null) {
    headingMatches.push({
      heading: match[1].trim(),
      start: match.index,
      end: match.index + match[0].length
    });
  }
  
  // Function to highlight scores and key metrics
  const highlightContent = (str) => {
    const scorePattern = /(\b\d{1,3}(?:\.\d{1,2})?\s*(?:%|\/100|\s*points?|out\s+of\s+100)?)/gi;
    const keywords = ['strong', 'excellent', 'good', 'weak', 'poor', 'critical', 'high', 'low', 'perfect', 'outstanding'];
    const keywordPattern = new RegExp(`\\b(${keywords.join('|')})\\b`, 'gi');
    
    let parts = str.split(scorePattern);
    
    return parts.map((part, idx) => {
      if (!part) return null;
      if (scorePattern.test(part)) {
        return (
          <span key={`score-${idx}`} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/40 font-semibold text-cyan-300">
            {part}
          </span>
        );
      }
      if (keywordPattern.test(part)) {
        return (
          <span key={`keyword-${idx}`} className="font-semibold text-amber-300">{part}</span>
        );
      }
      return part;
    }).filter(Boolean);
  };

  // If headings found, render structured sections
  if (headingMatches.length > 0) {
    return (
      <div className="mt-4 space-y-5">
        {headingMatches.map((headingMatch, sectionIdx) => {
          // Get text between this heading and next heading (or end of text)
          const contentStart = headingMatch.end;
          const nextHeadingStart = sectionIdx < headingMatches.length - 1 ? headingMatches[sectionIdx + 1].start : text.length;
          const contentText = text.substring(contentStart, nextHeadingStart).trim();
          
          // Split content into bullet points, removing ** markers
          const bulletPoints = contentText
            .replace(/\*\*([^*]+?)\*\*:?/g, '$1') // Remove ** markers
            .split(/(?:\r?\n|(?<=[.!?])\s+)/)
            .filter(p => p.trim().length > 3 && !p.match(/\*\*[^*]+\*\*/))
            .map(p => {
              let clean = p.trim();
              if (clean.startsWith('-') || clean.startsWith('*')) clean = clean.substring(1).trim();
              if (!/[.!?]$/.test(clean)) clean += '.';
              return clean;
            });

          return (
            <div key={sectionIdx} className="space-y-3">
              {/* Heading - Bold, gradient, no asterisks */}
              <h4 className="text-sm font-bold text-white bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                {headingMatch.heading}
              </h4>
              
              {/* Bullet Points under this heading */}
              {bulletPoints.length > 0 ? (
                <ul className="ml-4 space-y-2">
                  {bulletPoints.map((point, idx) => {
                    const isKeyPoint = /\b(strong|excellent|good|critical|high|perfect|outstanding|must|important|\d+%|\d+\/100)\b/i.test(point);
                    
                    return (
                      <li 
                        key={idx} 
                        className={`flex gap-2 text-sm ${isKeyPoint ? 'bg-slate-700/30 border-l-3 border-cyan-500 pl-3 py-1.5 rounded-r' : ''}`}
                      >
                        <span className={`flex-shrink-0 font-bold ${isKeyPoint ? 'text-cyan-400' : 'text-slate-400'}`}>
                          {isKeyPoint ? '✓' : '•'}
                        </span>
                        <span className={`leading-relaxed ${isKeyPoint ? 'text-slate-100 font-medium' : 'text-slate-300'}`}>
                          {highlightContent(point)}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              ) : null}
            </div>
          );
        })}
      </div>
    );
  }

  // Fallback: Simple bullet points without headings, remove ** if present
  const cleanText = text.replace(/\*\*([^*]+?)\*\*:?/g, '$1');
  const points = cleanText.split(/(?:\r?\n|\.(?=\s|$))/).filter(p => p.trim().length > 3);
  
  return (
    <ul className="space-y-3 mt-4 mb-0">
      {points.map((p, i) => {
        let clean = p.trim();
        if (clean.startsWith('-') || clean.startsWith('*')) clean = clean.substring(1).trim();
        if (!/[.!?]$/.test(clean)) clean += '.';
        
        const isKeyPoint = /\b(strong|excellent|good|critical|high|perfect|outstanding|must|important|\d+%|\d+\/100)\b/i.test(clean);
        
        return (
          <li 
            key={i} 
            className={`flex gap-3 ${isKeyPoint ? 'bg-slate-700/40 border-l-4 border-cyan-500 pl-4 py-2 rounded-r-lg' : 'text-slate-300'}`}
          >
            <span className={`flex-shrink-0 text-lg font-bold ${isKeyPoint ? 'text-cyan-400' : 'text-slate-500'}`}>
              {isKeyPoint ? '✓' : '•'}
            </span>
            <span className={`text-sm leading-relaxed ${isKeyPoint ? 'text-slate-100 font-medium' : 'text-slate-300'}`}>
              {highlightContent(clean)}
            </span>
          </li>
        );
      })}
    </ul>
  );
};

// Custom Tooltip for Recharts
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-recharts-tooltip">
        <p style={{ margin: 0, fontWeight: 'bold' }}>{payload[0].payload.full || label}</p>
        <p style={{ margin: '4px 0 0 0', color: '#22d3ee' }}>Project Occurrences: {payload[0].value}</p>
      </div>
    );
  }
  return null;
};

/** Extracts the key fields from the report */
function parseReport(agentReports) {
  if (!agentReports) return null;
  const fd = agentReports.final_decision;
  if (fd) {
    return {
      score: fd.final_score ?? 0,
      decision: fd.decision ?? 'N/A',
      explanation: fd.explanation ?? '',
      eloStatement: fd.elo_statement ?? null,
      techFit: agentReports.tech?.tech_stack_match?.toUpperCase() ?? 'N/A',
      cultureFit: agentReports.culture?.culture_fit_score ?? 'N/A',
      rejectionFeedback: agentReports.rejection_feedback ?? null,
      eloRanking: agentReports.elo_ranking ?? null,
      flightRisk: agentReports.flight_risk ?? null,
      behavioralProfile: agentReports.behavioral_profile ?? null,
    };
  }
  const lead = agentReports.lead;
  if (lead) {
    return {
      score: lead.overall_match_score ?? 0,
      decision: lead.recommendation ?? 'N/A',
      explanation: lead.final_summary ?? '',
      eloStatement: null,
      techFit: agentReports.tech?.tech_stack_match?.toUpperCase() ?? 'N/A',
      cultureFit: agentReports.culture?.culture_fit_score ?? 'N/A',
      rejectionFeedback: null,
      eloRanking: agentReports.elo_ranking ?? null,
      flightRisk: agentReports.flight_risk ?? null,
      behavioralProfile: agentReports.behavioral_profile ?? null,
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
  const [enriching, setEnriching] = useState(false);
  const [actionError, setActionError] = useState('');

  useEffect(() => {
    async function fetchCandidate() {
      // Validate ID exists and is not 'undefined'
      if (!id || id === 'undefined') {
        setLoading(false);
        // Redirect back to applicants if no valid ID
        setTimeout(() => navigate('/applicants'), 500);
        return;
      }
      try {
        // Add cache buster to ensure fresh data
        const res = await fetch(`${API}/api/v1/candidates/${id}?t=${Date.now()}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const response = await res.json();
        setCandidate(response.data || response);
      } catch (err) {
        console.error('Failed to fetch candidate details:', err);
        setActionError('Failed to load candidate details. Redirecting...');
        setTimeout(() => navigate('/applicants'), 1500);
      } finally {
        setLoading(false);
      }
    }
    fetchCandidate();
  }, [id, navigate]);

  const handleDecision = async (decision) => {
    setReviewing(true);
    setActionError('');
    try {
      const res = await fetch(`${API}/api/v1/candidates/${id}/decision`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reason: 'Manual HR Review' })
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'Decision update failed');
      
      // Reload candidate data to reflect the decision
      await new Promise(resolve => setTimeout(resolve, 500));
      const refreshRes = await fetch(`${API}/api/v1/candidates/${id}?t=${Date.now()}`);
      if (refreshRes.ok) {
        const response = await refreshRes.json();
        const updatedCandidate = response.data || response;
        setCandidate(updatedCandidate);
      }
    } catch (err) {
      setActionError(err.message);
      console.error('Decision update failed:', err);
    } finally {
      setReviewing(false);
    }
  };

  const handleEnrich = async () => {
    setEnriching(true);
    setActionError('');
    try {
      const res = await fetch(`${API}/api/v1/candidates/${id}/enrich`, { method: 'POST' });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'External enrichment failed');
      alert('Enrichment engine triggered! Social data (GitHub/LinkedIn) is being fetched in the background.');
    } catch (err) {
      setActionError(err.message);
      console.error('Enrichment failed:', err);
    } finally {
      setTimeout(() => setEnriching(false), 2000);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to permanently delete this candidate from the database?')) return;
    try {
      const res = await fetch(`${API}/api/v1/candidates/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      navigate('/applicants');
    } catch (err) {
      setActionError(err.message);
    }
  };

  const runAIReview = async () => {
    setGeneratingAI(true);
    setActionError('');
    try {
      // Trigger the review
      const res = await fetch(`${API}/api/v1/candidates/${id}/review`, { method: 'POST' });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || 'AI Review failed');
      
      // Poll for completed analysis (max 30 seconds)
      let attempts = 0;
      const maxAttempts = 15; // 30 seconds with 2 second intervals
      let analysisComplete = false;
      
      while (!analysisComplete && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds before polling
        attempts++;
        
        try {
          const pollRes = await fetch(`${API}/api/v1/candidates/${id}?t=${Date.now()}`);
          if (!pollRes.ok) break;
          const response = await pollRes.json();
          const updatedCandidate = response.data || response;
          
          // Check if analysis is complete
          if (updatedCandidate.agent_reports?.final_decision) {
            setCandidate(updatedCandidate);
            analysisComplete = true;
            break;
          }
        } catch (err) {
          console.error('Error polling for analysis results:', err);
        }
      }
      
      if (!analysisComplete) {
        console.warn('Analysis did not complete within timeout, but may be still processing');
      }
    } catch (err) {
      setActionError(err.message);
      console.error('AI Review failed:', err);
    } finally {
      setGeneratingAI(false);
    }
  };

  const [showExportOptions, setShowExportOptions] = useState(false);

  const handleDownloadPDF = async () => {
    const element = document.getElementById('candidate-report-container');
    if (!element) return;
    setShowExportOptions(false);
    try {
      const canvas = await html2canvas(element, { 
        backgroundColor: '#0F172A',
        scale: 2,
        useCORS: true,
        logging: false 
      });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
      
      // If content is very long, we might need multiple pages, but for bento, single stretched page or scaled is fine
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, Math.min(pdfHeight, 297)); 
      pdf.save(`Analysis_${candidate.parsed_data?.name?.replace(/\s+/g, '_') || 'Candidate'}.pdf`);
    } catch (err) {
      console.error('PDF Export failed:', err);
      alert('Failed to generate PDF. Check console for details.');
    }
  };

  const handleDownloadWord = () => {
    setShowExportOptions(false);
    const name = candidate.parsed_data?.name || 'Candidate';
    const score = displayScore;
    const decision = parsedReport?.decision || 'Under Review';
    const explanation = parsedReport?.explanation || 'No summary available.';
    
    const htmlContent = `
      <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
      <head><meta charset='utf-8'><title>${name} Report</title>
      <style>
        body { font-family: sans-serif; line-height: 1.6; color: #1e293b; max-width: 800px; margin: 40px auto; }
        .header { text-align: center; border-bottom: 3px solid #0891b2; padding-bottom: 10px; margin-bottom: 30px; }
        .score-box { background: #f1f5f9; padding: 20px; border-radius: 12px; border-left: 10px solid ${score >= 80 ? '#10b981' : '#f59e0b'}; margin-bottom: 30px; }
        .score-val { font-size: 32pt; font-weight: 800; color: ${score >= 80 ? '#10b981' : '#0891b2'}; margin: 0; }
        h2 { color: #0f172a; border-left: 4px solid #0891b2; padding-left: 12px; margin-top: 40px; }
        .footer { margin-top: 60px; font-size: 9pt; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 20px; }
      </style>
      </head>
      <body>
        <div class="header">
          <h1 style="color: #0891b2; margin: 0;">Autonomous Talent Partner</h1>
          <p style="color: #64748b;">360° Artificial Intelligence Candidate Evaluation</p>
        </div>

        <div class="score-box">
          <p style="margin: 0; text-transform: uppercase; font-size: 10pt; font-weight: 700; color: #64748b;">Match Score</p>
          <div class="score-val">${score}%</div>
          <p style="margin: 10px 0 0 0; font-size: 14pt;"><strong>Decision:</strong> ${decision.toUpperCase()}</p>
        </div>

        <h2>I. Candidate Profile Summary</h2>
        <p><strong>Name:</strong> ${name}</p>
        <p><strong>Email:</strong> ${candidate.parsed_data?.email || 'N/A'}</p>
        <p><strong>Roles Detected:</strong> ${candidate.parsed_data?.roles?.join(', ') || 'N/A'}</p>

        <h2>II. AI Executive Analysis</h2>
        <p>${explanation}</p>

        <h2>III. Technical Verified Evidence</h2>
        <p><strong>Resume Claimed Skills:</strong> ${candidate.parsed_data?.skills?.join(', ') || 'N/A'}</p>
        <p><strong>GitHub Evidence:</strong> Found ${candidate.external_intel?.github?.public_repos || 0} repositories with ${candidate.external_intel?.github?.total_stars || 0} total stars. Top verified languages include: ${candidate.external_intel?.github?.top_languages?.join(', ') || 'None found'}.</p>

        <h2>IV. Culture & Resonance</h2>
        <p>The candidate shows a culture fit resonance of <strong>${candidate.agent_reports?.culture?.culture_fit_score || 0}/10</strong> with specific alignment in ${candidate.agent_reports?.culture?.strengths?.slice(0, 3).join(', ') || 'general collaboration'}.</p>

        <div class="footer">
          Digitally Signed & Generated by Autonomous Talent Partner Swarm on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}
        </div>
      </body>
      </html>
    `;

    const blob = new Blob(['\ufeff', htmlContent], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Analysis_Report_${name.replace(/\s+/g, '_')}.doc`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <div style={{ textAlign: 'center' }}>
        <div className="loader" style={{ width: '40px', height: '40px', margin: '0 auto 16px' }}></div>
        <p style={{ color: '#64748b' }}>Loading candidate details...</p>
      </div>
    </div>
  );
  
  if (actionError) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <div style={{ textAlign: 'center', color: '#ef4444' }}>
        <p>{actionError}</p>
      </div>
    </div>
  );
  
  if (!candidate) return (
    <div className="bento-item" style={{ textAlign: 'center', padding: '60px' }}>
      <p>Candidate not found.</p>
    </div>
  );

  const data = candidate.parsed_data || {};
  const parsedReport = parseReport(candidate.agent_reports);
  const displayScore = parsedReport?.score ?? candidate.match_score ?? 0;
  
  // Determine dynamic ring colors layout
  const scoreRingClass = displayScore >= 80 ? 'ring-excellent' : displayScore >= 60 ? 'ring-good' : 'ring-poor';
  const scoreColor = displayScore >= 80 ? 'var(--success)' : displayScore >= 60 ? '#f59e0b' : 'var(--error)';

  // Chart Data Preparation
  const evaluatedSkills = candidate?.agent_reports?.skill_counts?.skills || candidate?.agent_reports?.tech?.evaluated_skills || [];
  const skillsData = evaluatedSkills.length > 0 
    ? evaluatedSkills.map(s => ({ name: s.skill?.substring(0, 6) + '.', full: s.skill, value: s.implementation_count || s.proficiency_score || 1 })).slice(0,7)
    : (data.skills || []).slice(0, 7).map(s => ({ name: s.substring(0, 6) + '.', full: s, value: 3 + Math.floor(Math.random() * 5) }));

  const chartColors = ['#06b6d4', '#22d3ee', '#14b8a6', '#10b981', '#3b82f6', '#8b5cf6'];

  const cultureScore = candidate?.agent_reports?.culture?.culture_fit_score || 0;
  const cultureData = [
    { subject: 'Culture Fit', A: cultureScore * 10, fullMark: 100 },
    { subject: 'Collaboration', A: Math.min(100, cultureScore * 10 + 10), fullMark: 100 },
    { subject: 'Growth', A: Math.min(100, cultureScore * 10 + 8), fullMark: 100 },
    { subject: 'Innovation', A: Math.max(0, cultureScore * 10 - 5), fullMark: 100 },
    { subject: 'Communication', A: Math.min(100, cultureScore * 10 + 5), fullMark: 100 }
  ];



  const handleDownloadChart = async (containerId, fileName) => {
    const element = document.getElementById(containerId);
    if (!element) return;
    try {
      const canvas = await html2canvas(element, { backgroundColor: '#0B0E14' });
      const dataUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `${fileName}_${data.name?.replace(/\s+/g, '_') || 'Applicant'}.png`;
      link.href = dataUrl;
      link.click();
    } catch (err) {
      console.error('Failed to download chart', err);
    }
  };

  return (
    <div id="candidate-report-container" style={{ maxWidth: '1400px', margin: '0 auto', paddingBottom: '60px', padding: '20px' }}>
      {/* Top Header */}
      <div className="detail-header" style={{ marginBottom: '32px' }}>
        <button onClick={() => navigate(-1)} className="nav-item" style={{ border: 'none', cursor: 'pointer', padding: '8px 16px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px' }}>
          <ArrowLeft size={18} />
          Back to Applicants
        </button>

        <div className="action-buttons">
          <button 
            className="nav-item" 
            onClick={handleEnrich} 
            disabled={enriching}
            style={{ border: 'none', background: 'rgba(34, 211, 238, 0.1)', cursor: 'pointer', padding: '8px 16px', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent)' }}
          >
            <RefreshCw size={16} className={enriching ? 'spin' : ''} />
            {enriching ? 'Enriching...' : 'Enrich Profile'}
          </button>

          <div style={{ position: 'relative' }}>
            <button 
              className="nav-item" 
              onClick={() => setShowExportOptions(!showExportOptions)}
              style={{ border: 'none', background: 'rgba(16, 185, 129, 0.1)', cursor: 'pointer', padding: '8px 16px', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--emerald)' }}
            >
              <Download size={16} />
              Export Report
              <ChevronDown size={14} />
            </button>
            
            {showExportOptions && (
              <div style={{ 
                position: 'absolute', 
                top: 'calc(100% + 8px)', 
                right: 0, 
                background: '#1e293b', 
                border: '1px solid rgba(255,255,255,0.1)', 
                borderRadius: '12px', 
                overflow: 'hidden', 
                zIndex: 100,
                width: '180px',
                boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
              }}>
                <button onClick={handleDownloadPDF} style={{ width: '100%', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px', background: 'none', border: 'none', color: 'white', cursor: 'pointer', textAlign: 'left', transition: 'background 0.2s' }} onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.05)'} onMouseLeave={(e) => e.target.style.background = 'none'}>
                  <FileText size={16} color="var(--error)" /> 
                  Download PDF
                </button>
                <button onClick={handleDownloadWord} style={{ width: '100%', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: '10px', background: 'none', border: 'none', color: 'white', cursor: 'pointer', textAlign: 'left', transition: 'background 0.2s' }} onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.05)'} onMouseLeave={(e) => e.target.style.background = 'none'}>
                  <FileCode size={16} color="#3b82f6" /> 
                  Download Word
                </button>
              </div>
            )}
          </div>

          {candidate.hr_decision ? (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span style={{ 
                padding: '8px 16px', 
                borderRadius: '20px',
                background: candidate.hr_decision === 'rejected' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                color: candidate.hr_decision === 'rejected' ? '#ef4444' : '#10b981',
                fontWeight: 600,
                fontSize: '0.9rem'
              }}>
                ✓ {candidate.hr_decision === 'rejected' ? 'Rejected' : 'Approved'}
              </span>
            </div>
          ) : (
            <>
              <button
                className="btn-pill btn-reject"
                onClick={() => handleDecision('rejected')}
                disabled={reviewing || generatingAI || !parsedReport}
                title={!parsedReport ? "AI score required before decision" : ""}
              >
                {reviewing ? 'Processing...' : 'Reject application'}
              </button>
              <button
                className="btn-pill btn-approve"
                onClick={() => handleDecision('selected')}
                disabled={reviewing || generatingAI || !parsedReport}
                title={!parsedReport ? "AI score required before decision" : ""}
              >
                {reviewing ? 'Processing...' : 'Approve Candidate'}
              </button>
            </>
          )}

          <button 
            className="nav-item" 
            onClick={handleDelete}
            style={{ border: 'none', background: 'rgba(239, 68, 68, 0.1)', cursor: 'pointer', padding: '8px 16px', borderRadius: '20px', color: 'var(--error)' }}
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {actionError && (
        <div className="bento-item" style={{ borderColor: 'var(--error)', marginBottom: '24px', padding: '16px 24px', background: 'rgba(239, 68, 68, 0.1)' }}>
          <p style={{ color: 'var(--error)', margin: 0, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} /> {actionError}
          </p>
        </div>
      )}

      {/* Main Bento Grid */}
      <div className="bento-grid">
        
        {/* Core Profile & Score Card (Spans 12 columns on top) */}
        <div className="bento-item bento-full" style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '40px', background: 'linear-gradient(135deg, rgba(8, 14, 25, 0.8) 0%, rgba(15, 23, 42, 0.6) 100%)', border: '1px solid rgba(34, 211, 238, 0.1)', boxShadow: '0 0 40px rgba(34, 211, 238, 0.05)' }}>
            <div style={{ flex: 1, minWidth: '300px' }}>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '12px', background: 'linear-gradient(90deg, #fff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    {data.name || 'Unknown Candidate'}
                </h1>
                <div style={{ display: 'flex', gap: '20px', color: 'var(--text-muted)', flexWrap: 'wrap', fontSize: '0.95rem', alignItems: 'center' }}>
                    {data.email && <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Mail size={16} color="var(--accent)" /> {data.email}</span>}
                    {data.phone && <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Phone size={16} color="var(--accent)" /> {data.phone}</span>}
                    
                    {/* Prestige & Industry Badges */}
                    {candidate.agent_reports?.screener?.internship_details?.prestige_tier?.includes('Tier 1') && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', padding: '4px 12px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600, border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                        <Award size={14} /> Tier 1 Verified
                      </span>
                    )}
                    {candidate.agent_reports?.tech?.project_category?.includes('Industry') && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(34, 211, 238, 0.1)', color: 'var(--accent)', padding: '4px 12px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600, border: '1px solid rgba(34, 211, 238, 0.2)' }}>
                        <ZapIcon size={14} /> Industry Grade
                      </span>
                    )}

                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Briefcase size={16} color="var(--accent)" /> 
                        <span style={{ textTransform: 'capitalize', color: candidate.status === 'selected' ? 'var(--success)' : candidate.status === 'rejected' ? 'var(--error)' : 'white' }}>
                            {candidate.status.replace('_', ' ')}
                        </span>
                    </span>
                </div>
                
                <div style={{ marginTop: '24px', display: 'flex', gap: '16px' }}>
                    {!parsedReport && (
                    <button
                        onClick={runAIReview}
                        disabled={generatingAI}
                        className="btn-primary"
                        style={{ width: 'fit-content', padding: '12px 24px', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                        <Zap size={18} /> {generatingAI ? 'Running AI Engine...' : 'Run Autonomous Analysis'}
                    </button>
                    )}
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
                {candidate.agent_reports?.final_decision?.category_scores && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', minWidth: '400px' }}>
                    {Object.entries(candidate.agent_reports.final_decision.category_scores).map(([key, value]) => (
                      <div key={key} style={{ display: 'flex', flexDirection: 'column', padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                        <span style={{ fontSize: '0.6rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '4px' }}>{key.replace('_', ' ')}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ flex: 1, height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px' }}>
                            <div style={{ width: `${value}%`, height: '100%', background: value > 70 ? 'var(--neon-cyan)' : value > 40 ? 'var(--neon-amber)' : 'var(--neon-magenta)', borderRadius: '2px' }}></div>
                          </div>
                          <span style={{ fontSize: '0.8rem', fontWeight: 800 }}>{value}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>Autonomous Rating</p>
                    {parsedReport && (
                         <div style={{ fontSize: '1.25rem', fontWeight: 600, color: parsedReport.decision?.toLowerCase() === 'hire' || parsedReport.decision?.toLowerCase() === 'selected' ? 'var(--success)' : 'var(--error)' }}>
                            {parsedReport.decision?.toUpperCase()}
                         </div>
                    )}
                </div>
                <div className={`circular-progress ${scoreRingClass}`} style={{ '--progress': `${displayScore * 3.6}deg`, width: '130px', height: '130px' }}>
                     <span className="circular-value score-glow" style={{ color: scoreColor, fontSize: '2.5rem' }}>{displayScore}</span>
                     {candidate.external_intel?.github?.status === 'ok' && (
                       <div style={{ position: 'absolute', bottom: '-10px', background: 'var(--emerald)', color: 'white', padding: '2px 8px', borderRadius: '10px', fontSize: '0.6rem', fontWeight: 'bold', textTransform: 'uppercase', boxShadow: '0 0 10px var(--emerald)' }}>
                         Verified
                       </div>
                     )}
                </div>
            </div>
        </div>

        {/* ELO Ranking Section */}
        {parsedReport?.eloStatement && (
            <div className="bento-item bento-full" style={{ background: 'linear-gradient(to right, rgba(59, 130, 246, 0.05), rgba(6, 182, 212, 0.05))' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h3 className="card-title"><Award size={20} color="var(--accent)" /> Percentile Ranking</h3>
                    {parsedReport.eloRanking && (
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                            <span style={{ color: 'var(--accent)', fontWeight: 600 }}>Rank: #{parsedReport.eloRanking.rank_in_pool}</span>
                            {' / '}<span>{parsedReport.eloRanking.pool_size} in pool</span>
                        </div>
                    )}
                </div>
                <div style={{ marginTop: '12px', padding: '16px', background: 'rgba(59, 130, 246, 0.1)', borderLeft: '4px solid var(--accent)', borderRadius: '8px' }}>
                    <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
                        {parsedReport.eloStatement}
                    </p>
                    {parsedReport.eloRanking && (
                        <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                            <div style={{ padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', textAlign: 'center' }}>
                                <p style={{ margin: '0 0 4px 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Percentile</p>
                                <p style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent)' }}>{parsedReport.eloRanking.percentile.toFixed(1)}%</p>
                            </div>
                            <div style={{ padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', textAlign: 'center' }}>
                                <p style={{ margin: '0 0 4px 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Pool Avg</p>
                                <p style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--neon-cyan)' }}>{parsedReport.eloRanking.pool_avg_score.toFixed(1)}</p>
                            </div>
                            <div style={{ padding: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', textAlign: 'center' }}>
                                <p style={{ margin: '0 0 4px 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Pool Max</p>
                                <p style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: 'var(--neon-magenta)' }}>{parsedReport.eloRanking.pool_highest_score}</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        )}

        {/* Culture Assessment Radar */}
        {candidate?.agent_reports?.culture && (
            <div id="culture-chart-container" className="bento-item bento-half" style={{ background: 'linear-gradient(to bottom right, rgba(217, 70, 239, 0.05), transparent)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h3 className="card-title"><Heart size={20} color="var(--magenta)" /> Culture Assessment</h3>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <div className="score-glow" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--magenta)' }}>{cultureScore}/10</div>
                        <button onClick={() => handleDownloadChart('culture-chart-container', 'Culture_Assessment')} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }} title="Download Chart">
                            <Download size={16} />
                        </button>
                    </div>
                </div>
                
                <div style={{ width: '100%', height: '220px', marginTop: '10px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={cultureData}>
                            <PolarGrid stroke="rgba(255,255,255,0.1)" />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                            <Radar name="Candidate" dataKey="A" stroke="var(--magenta)" fill="var(--magenta)" fillOpacity={0.4} />
                            <Tooltip content={<CustomTooltip />} />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>

                {candidate.agent_reports.culture.pros?.length > 0 && (
                  <div style={{ marginTop: '12px' }}>
                     <p style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                       <span style={{ color: 'var(--magenta)', fontWeight: 600 }}>Score Indicators:</span> {candidate.agent_reports.culture.pros.slice(0,3).join(', ')}
                     </p>
                  </div>
                )}
            </div>
        )}

        {/* AI Analyzed Skills Bar Chart */}
        {skillsData && skillsData.length > 0 && (
            <div id="skills-chart-container" className="bento-item bento-half" style={{ background: 'linear-gradient(to bottom right, rgba(16, 185, 129, 0.05), transparent)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h3 className="card-title"><BarChart2 size={20} color="var(--emerald)" /> Skills Implementation Frequency</h3>
                    <button onClick={() => handleDownloadChart('skills-chart-container', 'Skills_Analysis')} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }} title="Download Chart">
                        <Download size={16} />
                    </button>
                </div>
                
                <div style={{ width: '100%', height: '240px', marginTop: '10px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={skillsData} margin={{ top: 10, right: 10, left: -25, bottom: 5 }}>
                            <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                                {skillsData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
                   <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Data Source</span>
                   <span style={{ fontSize: '0.85rem', color: 'var(--emerald)', fontWeight: 600 }}>Project Extractions</span>
                </div>
            </div>
        )}

        {/* External Intelligence (Enrichment) Panel */}
        {candidate.external_intel && (
            <div className="bento-item bento-full" style={{ background: 'rgba(15, 23, 42, 0.4)', borderTop: '3px solid var(--accent)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <h3 className="card-title" style={{ margin: 0 }}><Globe size={20} color="var(--accent)" /> 360° External Intelligence Enrichment</h3>
                    <div style={{ display: 'flex', gap: '8px' }}>
                       <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>Enriched</span>
                       <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status: {candidate.external_intel.enrichment_status}</span>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '32px' }}>
                    {/* GitHub Column */}
                    <div>
                        {candidate.external_intel.github?.status === 'ok' ? (
                            <div style={{ padding: '24px', borderRadius: '20px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
                                    {candidate.external_intel.github.avatar_url && (
                                        <img src={candidate.external_intel.github.avatar_url} alt="GitHub" style={{ width: '56px', height: '56px', borderRadius: '16px', border: '2px solid rgba(34, 211, 238, 0.2)' }} />
                                    )}
                                    <div>
                                        <h4 style={{ margin: 0, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                            <Github size={20} /> @{candidate.external_intel.github.username}
                                        </h4>
                                        <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{candidate.external_intel.github.bio || 'GitHub Developer Profile'}</p>
                                    </div>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '20px' }}>
                                    <div className="glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent)' }}>{candidate.external_intel.github.total_stars}</div>
                                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Stars</div>
                                    </div>
                                    <div className="glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent)' }}>{candidate.external_intel.github.public_repos}</div>
                                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Repos</div>
                                    </div>
                                    <div className="glass-panel" style={{ padding: '12px', textAlign: 'center' }}>
                                        <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent)' }}>{candidate.external_intel.github.contributions?.total || 0}</div>
                                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Github Active</div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center' }}>
                                <Github size={32} style={{ marginBottom: '12px', opacity: 0.2 }} />
                                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{candidate.external_intel.github?.status === 'rate_limited' ? 'GitHub API Rate Limited' : 'No GitHub Profile Linked'}</p>
                            </div>
                        )}
                    </div>

                    {/* LinkedIn Column */}
                    <div>
                        {candidate.external_intel.linkedin?.status === 'ok' ? (
                            <div style={{ padding: '24px', borderRadius: '20px', background: 'rgba(0, 114, 177, 0.05)', border: '1px solid rgba(0, 114, 177, 0.2)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
                                    <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: 'rgba(0, 114, 177, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <Linkedin size={28} color="#0072b1" />
                                    </div>
                                    <div>
                                        <h4 style={{ margin: 0, fontSize: '1.2rem', color: '#0072b1' }}>LinkedIn Professional Insight</h4>
                                        <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>{candidate.external_intel.linkedin.headline || 'Verified Profile Data'}</p>
                                    </div>
                                </div>

                                <div style={{ marginBottom: '20px' }}>
                                    <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px', marginBottom: '8px' }}>About / Summary</p>
                                    <p style={{ fontSize: '0.9rem', color: '#cbd5e1', lineHeight: '1.6', margin: 0 }}>
                                        {candidate.external_intel.linkedin.summary || 'No professional summary available on LinkedIn.'}
                                    </p>
                                </div>

                                <div>
                                    <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '1px', marginBottom: '12px' }}>Professional Timeline</p>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                        {candidate.external_intel.linkedin.experience?.slice(0, 3).map((exp, i) => (
                                            <div key={i} style={{ padding: '12px', borderRadius: '12px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                                                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{exp.title}</div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>{exp.company}</div>
                                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                                                    {exp.starts_at?.year ? `${exp.starts_at.month}/${exp.starts_at.year}` : ''} 
                                                    {exp.ends_at?.year ? ` — ${exp.ends_at.month}/${exp.ends_at.year}` : ' — Present'}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', border: '1px solid rgba(0, 114, 177, 0.1)' }}>
                                <Linkedin size={32} style={{ marginBottom: '12px', opacity: 0.2, color: '#0072b1' }} />
                                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                                    {candidate.external_intel.linkedin?.status === 'missing_api_key' ? 'LinkedIn API Key Required for Enrichment' : 'LinkedIn Profile Not Found'}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        )}

        {/* AI Core Reasoning (Bullet Points) */}
        {parsedReport?.explanation && (
            <div className="bento-item bento-full bg-gradient-to-br from-slate-800/50 to-slate-700/30 border border-cyan-500/20 rounded-xl overflow-hidden">
                <div className="border-l-4 border-cyan-500 bg-gradient-to-r from-cyan-500/10 to-transparent p-6">
                    <h3 className="card-title text-lg font-bold text-white flex items-center gap-2 mb-4">
                        <Lightbulb size={20} className="text-cyan-400" /> 
                        <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">Analysis Summary & Recommendation</span>
                    </h3>
                    
                    {renderBulletPoints(parsedReport.explanation)}
                </div>
                
                {parsedReport.rejectionFeedback && (
                    <div className="border-t border-red-500/20 bg-gradient-to-r from-red-500/10 via-transparent to-transparent p-6">
                        <div className="flex items-center gap-2 mb-4">
                            <AlertTriangle size={18} className="text-red-400" />
                            <p className="text-xs uppercase font-bold tracking-wider text-red-300">Rejection Feedback</p>
                        </div>
                        <div className="space-y-3">
                            {parsedReport.rejectionFeedback.missing_skills?.length > 0 && (
                                <div className="bg-slate-700/40 border-l-2 border-red-400 pl-4 py-3 rounded-r-lg">
                                    <p className="text-xs font-semibold text-red-300 mb-2">📌 Missing Skills:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {parsedReport.rejectionFeedback.missing_skills.map((skill, idx) => (
                                            <span key={idx} className="px-2 py-1 bg-red-500/20 text-red-300 text-xs rounded-md border border-red-500/30 font-medium">
                                                {skill}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {parsedReport.rejectionFeedback.suggestions && (
                                <div className="bg-slate-700/40 border-l-2 border-amber-400 pl-4 py-3 rounded-r-lg">
                                    <p className="text-xs font-semibold text-amber-300 mb-3">💡 Suggestions:</p>
                                    <ul className="space-y-2 ml-2">
                                        {parsedReport.rejectionFeedback.suggestions
                                          .split(/(?:\r?\n|(?<=[.!?])\s+)/)
                                          .filter(s => s.trim().length > 3)
                                          .map((suggestion, idx) => {
                                            let clean = suggestion.trim();
                                            if (clean.startsWith('-') || clean.startsWith('*')) clean = clean.substring(1).trim();
                                            if (!/[.!?]$/.test(clean)) clean += '.';
                                            return (
                                              <li key={idx} className="flex gap-2 text-sm">
                                                <span className="flex-shrink-0 font-bold text-amber-400">→</span>
                                                <span className="text-slate-300 leading-relaxed">{clean}</span>
                                              </li>
                                            );
                                          })
                                        }
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        )}

        {/* RAG Context Window */}
        {(candidate?.agent_reports?.rag_reasoning || candidate?.agent_reports?.lead?.rag_reasoning) && (
            <div className="bento-item bento-full bg-gradient-to-br from-slate-800/50 to-slate-700/30 border border-purple-500/20 rounded-xl overflow-hidden">
                <div className="border-l-4 border-purple-500 bg-gradient-to-r from-purple-500/10 to-transparent p-6">
                    <h3 className="card-title text-lg font-bold text-white flex items-center gap-2 mb-4">
                        <Terminal size={20} className="text-purple-400" /> 
                        <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">Graph & Vector Alignment Analysis</span>
                    </h3>
                    {renderBulletPoints(candidate.agent_reports.rag_reasoning || candidate.agent_reports.lead?.rag_reasoning)}
                </div>
            </div>
        )}

        {/* ========== HIGH IMPACT FEATURES ========== */}

        {/* Risk Assessment Dashboard */}
        {candidate?.comprehensive_analysis?.risk_assessment && (
          <div className="bento-item bento-full" style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(234, 179, 8, 0.05))', borderLeft: '4px solid #ef4444' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h3 className="card-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                <AlertTriangle size={20} color="#ef4444" /> Risk Assessment & Mitigation
              </h3>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: candidate.comprehensive_analysis.risk_assessment.overall_risk_score > 60 ? '#ef4444' : candidate.comprehensive_analysis.risk_assessment.overall_risk_score > 40 ? '#f59e0b' : '#10b981' }}>
                {candidate.comprehensive_analysis.risk_assessment.overall_risk_score}/100
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              <div style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                <p style={{ margin: '0 0 8px 0', fontSize: '0.8rem', textTransform: 'uppercase', color: '#ef4444', fontWeight: 700 }}>Skill Gap Risk</p>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ef4444' }}>{candidate.comprehensive_analysis.risk_assessment.skill_gap_risk}/100</div>
              </div>
              <div style={{ padding: '16px', background: 'rgba(234, 179, 8, 0.1)', borderRadius: '12px', border: '1px solid rgba(234, 179, 8, 0.2)' }}>
                <p style={{ margin: '0 0 8px 0', fontSize: '0.8rem', textTransform: 'uppercase', color: '#f59e0b', fontWeight: 700 }}>Experience Risk</p>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f59e0b' }}>{candidate.comprehensive_analysis.risk_assessment.experience_risk}/100</div>
              </div>
              <div style={{ padding: '16px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
                <p style={{ margin: '0 0 8px 0', fontSize: '0.8rem', textTransform: 'uppercase', color: '#6366f1', fontWeight: 700 }}>Consistency Risk</p>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#6366f1' }}>{candidate.comprehensive_analysis.risk_assessment.consistency_risk}/100</div>
              </div>
              <div style={{ padding: '16px', background: 'rgba(168, 85, 247, 0.1)', borderRadius: '12px', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                <p style={{ margin: '0 0 8px 0', fontSize: '0.8rem', textTransform: 'uppercase', color: '#a855f7', fontWeight: 700 }}>Red Flags</p>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#a855f7' }}>{candidate.comprehensive_analysis.risk_assessment.red_flags_count}</div>
              </div>
            </div>
            {candidate.comprehensive_analysis.risk_assessment.red_flags_count > 0 && (
              <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', borderLeft: '3px solid #ef4444' }}>
                <p style={{ fontSize: '0.85rem', color: '#fca5a5', margin: 0, fontWeight: 600 }}>
                  ⚠️ {candidate.comprehensive_analysis.risk_assessment.red_flags_count} red flag(s) identified. Review consistency analysis below.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Neo4j Knowledge Graph Insights */}
        {candidate?.comprehensive_analysis?.neo4j_insights && (
          <div className="bento-item bento-full" style={{ background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.05), rgba(6, 182, 212, 0.05))', borderLeft: '4px solid #06b6d4' }}>
            <h3 className="card-title" style={{ margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Binary size={20} color="var(--accent)" /> Neo4j Knowledge Graph Intelligence
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
              {candidate.comprehensive_analysis.neo4j_insights.skill_gaps?.length > 0 && (
                <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '12px' }}>⚡ Skill Gaps Identified</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {candidate.comprehensive_analysis.neo4j_insights.skill_gaps.map((skill, idx) => (
                      <span key={idx} style={{ padding: '6px 12px', background: 'rgba(239, 68, 68, 0.15)', color: '#fca5a5', borderRadius: '8px', fontSize: '0.75rem', fontWeight: 600, border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {candidate.comprehensive_analysis.neo4j_insights.transferable_skills?.length > 0 && (
                <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '12px' }}>✓ Transferable Skills</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {candidate.comprehensive_analysis.neo4j_insights.transferable_skills.slice(0, 6).map((skill, idx) => (
                      <span key={idx} style={{ padding: '6px 12px', background: 'rgba(16, 185, 129, 0.15)', color: '#86efac', borderRadius: '8px', fontSize: '0.75rem', fontWeight: 600, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {candidate.comprehensive_analysis.neo4j_insights.domain_specialization && (
                <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px' }}>🎯 Domain Specialization</p>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-main)' }}>{candidate.comprehensive_analysis.neo4j_insights.domain_specialization}</p>
                </div>
              )}
              {candidate.comprehensive_analysis.neo4j_insights.learning_curve && (
                <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px' }}>📈 Learning Curve</p>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-main)' }}>{candidate.comprehensive_analysis.neo4j_insights.learning_curve}</p>
                </div>
              )}
              {candidate.comprehensive_analysis.neo4j_insights.career_path_fit && (
                <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px' }}>🚀 Career Path Fit</p>
                  <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-main)' }}>{candidate.comprehensive_analysis.neo4j_insights.career_path_fit}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Education & Certifications */}
        {(data.education?.length > 0 || data.certifications?.length > 0) && (
          <div className="bento-item bento-half" style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(99, 102, 241, 0.05))', borderLeft: '4px solid #3b82f6' }}>
            <h3 className="card-title" style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Award size={20} color="#3b82f6" /> Education & Credentials
            </h3>
            {data.education?.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '12px' }}>Education</p>
                {data.education.map((edu, idx) => (
                  <div key={idx} style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', marginBottom: '10px', borderLeft: '3px solid #3b82f6' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'white' }}>{edu.degree || edu.institution}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--accent)', marginTop: '4px' }}>{edu.institution || edu.degree}</div>
                    {edu.graduation_year && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Graduated: {edu.graduation_year}</div>}
                  </div>
                ))}
              </div>
            )}
            {data.certifications?.length > 0 && (
              <div>
                <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '12px' }}>Certifications</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {data.certifications.map((cert, idx) => (
                    <span key={idx} style={{ padding: '8px 12px', background: 'rgba(59, 130, 246, 0.15)', color: '#93c5fd', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600, border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                      🏆 {cert}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Soft Skills Assessment */}
        {candidate?.parsed_data?.soft_skills?.length > 0 && (
          <div className="bento-item bento-half" style={{ background: 'linear-gradient(135deg, rgba(217, 70, 239, 0.05), rgba(168, 85, 247, 0.05))', borderLeft: '4px solid #d946ef' }}>
            <h3 className="card-title" style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Heart size={20} color="#d946ef" /> Soft Skills & Competencies
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '10px' }}>
              {candidate.parsed_data.soft_skills.map((skill, idx) => (
                <div key={idx} style={{ padding: '12px', background: 'rgba(217, 70, 239, 0.1)', borderRadius: '10px', textAlign: 'center', border: '1px solid rgba(217, 70, 239, 0.2)' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f0abfc' }}>{skill}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>Verified</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Interview Timeline */}
        {candidate?.interview_date && (
          <div className="bento-item bento-half" style={{ background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.05), rgba(6, 182, 212, 0.05))', borderLeft: '4px solid #06b6d4' }}>
            <h3 className="card-title" style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle size={20} color="var(--accent)" /> Interview Status
            </h3>
            <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <div style={{ marginBottom: '12px' }}>
                <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '4px' }}>Scheduled Date & Time</p>
                <p style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--success)' }}>
                  📅 {candidate.interview_date} {candidate.interview_time && `at ${candidate.interview_time}`}
                </p>
              </div>
              {candidate.interview_duration && (
                <div style={{ marginBottom: '12px', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  ⏱️ Duration: {candidate.interview_duration} minutes
                </div>
              )}
              {candidate.interviewer_name && (
                <div style={{ marginBottom: '12px', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  👤 Interviewer: {candidate.interviewer_name}
                </div>
              )}
              {candidate.meeting_link && (
                <div style={{ marginTop: '12px' }}>
                  <a href={candidate.meeting_link} target="_blank" rel="noopener noreferrer" style={{ padding: '8px 16px', background: 'var(--accent)', color: '#0f172a', borderRadius: '8px', textDecoration: 'none', fontWeight: 600, fontSize: '0.85rem', display: 'inline-block' }}>
                    🔗 Join Meeting
                  </a>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ========== SUPPORTING FEATURES ========== */}

        {/* Consistency Analysis */}
        {candidate?.comprehensive_analysis?.consistency_analysis && (
          <div className="bento-item bento-full" style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(6, 182, 212, 0.05))' }}>
            <h3 className="card-title" style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle size={20} color="#3b82f6" /> Background Consistency Verification
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
              <div style={{ padding: '16px', background: candidate.comprehensive_analysis.consistency_analysis.timeline_consistent ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', border: `1px solid ${candidate.comprehensive_analysis.consistency_analysis.timeline_consistent ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
                <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700, marginBottom: '8px', color: candidate.comprehensive_analysis.consistency_analysis.timeline_consistent ? 'var(--success)' : 'var(--error)' }}>Timeline Consistency</p>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: candidate.comprehensive_analysis.consistency_analysis.timeline_consistent ? 'var(--success)' : 'var(--error)' }}>
                  {candidate.comprehensive_analysis.consistency_analysis.timeline_consistent ? '✓ Valid' : '✗ Issues'}
                </div>
              </div>
              <div style={{ padding: '16px', background: candidate.comprehensive_analysis.consistency_analysis.skill_consistency ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', border: `1px solid ${candidate.comprehensive_analysis.consistency_analysis.skill_consistency ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
                <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700, marginBottom: '8px', color: candidate.comprehensive_analysis.consistency_analysis.skill_consistency ? 'var(--success)' : 'var(--error)' }}>Skill Consistency</p>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: candidate.comprehensive_analysis.consistency_analysis.skill_consistency ? 'var(--success)' : 'var(--error)' }}>
                  {candidate.comprehensive_analysis.consistency_analysis.skill_consistency ? '✓ Aligned' : '✗ Gaps'}
                </div>
              </div>
              <div style={{ padding: '16px', background: candidate.comprehensive_analysis.consistency_analysis.experience_level_match ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', border: `1px solid ${candidate.comprehensive_analysis.consistency_analysis.experience_level_match ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
                <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700, marginBottom: '8px', color: candidate.comprehensive_analysis.consistency_analysis.experience_level_match ? 'var(--success)' : 'var(--error)' }}>Experience Match</p>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: candidate.comprehensive_analysis.consistency_analysis.experience_level_match ? 'var(--success)' : 'var(--error)' }}>
                  {candidate.comprehensive_analysis.consistency_analysis.experience_level_match ? '✓ Matched' : '✗ Mismatch'}
                </div>
              </div>
              <div style={{ padding: '16px', background: candidate.comprehensive_analysis.consistency_analysis.title_progression_logical ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', border: `1px solid ${candidate.comprehensive_analysis.consistency_analysis.title_progression_logical ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
                <p style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700, marginBottom: '8px', color: candidate.comprehensive_analysis.consistency_analysis.title_progression_logical ? 'var(--success)' : 'var(--error)' }}>Career Progression</p>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: candidate.comprehensive_analysis.consistency_analysis.title_progression_logical ? 'var(--success)' : 'var(--error)' }}>
                  {candidate.comprehensive_analysis.consistency_analysis.title_progression_logical ? '✓ Logical' : '✗ Unusual'}
                </div>
              </div>
            </div>
            {candidate.comprehensive_analysis.consistency_analysis.inconsistencies?.length > 0 && (
              <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px', borderLeft: '3px solid #ef4444' }}>
                <p style={{ fontSize: '0.8rem', fontWeight: 700, color: '#fca5a5', marginBottom: '8px', margin: 0 }}>⚠️ Inconsistencies Found:</p>
                <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                  {candidate.comprehensive_analysis.consistency_analysis.inconsistencies.map((issue, idx) => (
                    <li key={idx} style={{ fontSize: '0.8rem', color: 'var(--text-main)', marginTop: '4px' }}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Flight Risk Assessment */}
        {candidate?.agent_reports?.flight_risk && (
          <div className="bento-item bento-half" style={{ background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(234, 179, 8, 0.05))', borderLeft: '4px solid #ef4444' }}>
            <h3 className="card-title" style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <TrendingUp size={20} color="#ef4444" /> Retention Risk Assessment
            </h3>
            {typeof candidate.agent_reports.flight_risk === 'object' ? (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                  <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '10px' }}>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, margin: '0 0 4px 0' }}>Flight Risk Score</p>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ef4444' }}>{candidate.agent_reports.flight_risk.score || 'N/A'}/100</div>
                  </div>
                  <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '10px' }}>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, margin: '0 0 4px 0' }}>Retention Prob.</p>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--success)' }}>{candidate.agent_reports.flight_risk.retention_probability || 'N/A'}%</div>
                  </div>
                </div>
                {candidate.agent_reports.flight_risk.key_factors && (
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
                    <p style={{ margin: '0 0 8px 0', fontWeight: 700, color: 'white' }}>Key Risk Factors:</p>
                    <p style={{ margin: 0 }}>{candidate.agent_reports.flight_risk.key_factors}</p>
                  </div>
                )}
              </>
            ) : (
              <p style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>{candidate.agent_reports.flight_risk}</p>
            )}
          </div>
        )}

        {/* Code Quality Metrics */}
        {candidate?.external_intel?.github?.code_quality && (
          <div className="bento-item bento-half" style={{ background: 'linear-gradient(135deg, rgba(34, 211, 238, 0.05), rgba(6, 182, 212, 0.05))', borderLeft: '4px solid #06b6d4' }}>
            <h3 className="card-title" style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Cpu size={20} color="var(--accent)" /> Code Quality Analysis
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {Object.entries(candidate.external_intel.github.code_quality).map(([key, value]) => (
                <div key={key} style={{ padding: '12px', background: 'rgba(34, 211, 238, 0.1)', borderRadius: '10px', border: '1px solid rgba(34, 211, 238, 0.2)' }}>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700, margin: '0 0 4px 0', textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</p>
                  <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent)' }}>{value}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Extracurricular & Hackathon Projects */}
        {(candidate?.parsed_data?.extracurricular_activities?.length > 0 || candidate?.parsed_data?.hackathons?.length > 0 || candidate?.parsed_data?.projects?.length > 0) && (
          <div className="bento-item bento-full" style={{ background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.05), rgba(217, 70, 239, 0.05))', borderLeft: '4px solid #a855f7' }}>
            <h3 className="card-title" style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Zap size={20} color="#a855f7" /> Projects & Extracurricular
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
              {candidate?.parsed_data?.projects?.slice(0, 3).map((project, idx) => (
                <div key={`proj-${idx}`} style={{ padding: '14px', background: 'rgba(168, 85, 247, 0.1)', borderRadius: '10px', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#e9d5ff', marginBottom: '6px' }}>💻 {project}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Personal/Professional Project</div>
                </div>
              ))}
              {candidate?.parsed_data?.hackathons?.slice(0, 3).map((hackathon, idx) => (
                <div key={`hack-${idx}`} style={{ padding: '14px', background: 'rgba(34, 211, 238, 0.1)', borderRadius: '10px', border: '1px solid rgba(34, 211, 238, 0.2)' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#cffafe', marginBottom: '6px' }}>🏆 {hackathon}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Hackathon Participation</div>
                </div>
              ))}
              {candidate?.parsed_data?.extracurricular_activities?.slice(0, 3).map((activity, idx) => (
                <div key={`extra-${idx}`} style={{ padding: '14px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#a7f3d0', marginBottom: '6px' }}>⭐ {activity}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Extracurricular Activity</div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
