import React from 'react';

/**
 * RiskAssessmentChart Component
 * Visualizes risk assessment data with:
 * - Overall risk score with gauge
 * - Individual risk factors breakdown
 * - Red flags listing
 * - Risk severity indicators
 */
const RiskAssessmentChart = ({ riskData = {} }) => {
  if (!riskData || Object.keys(riskData).length === 0) {
    return <div className="flex items-center justify-center min-h-50 p-6 bg-gray-100 text-gray-500 rounded-lg text-base">No risk assessment data available</div>;
  }

  const {
    overall_risk_score = 0,
    skill_gap_risk = 0,
    experience_risk = 0,
    consistency_risk = 0,
    red_flags_count = 0,
    red_flags = [],
    confidence_adjustment = 0
  } = riskData;

  const getRiskLevel = (score) => {
    if (score >= 0.8) return { level: 'CRITICAL', color: '#dc2626', icon: '🔴' };
    if (score >= 0.6) return { level: 'HIGH', color: '#ea580c', icon: '🟠' };
    if (score >= 0.4) return { level: 'MEDIUM', color: '#eab308', icon: '🟡' };
    if (score >= 0.2) return { level: 'LOW', color: '#84cc16', icon: '🟢' };
    return { level: 'MINIMAL', color: '#22c55e', icon: '✅' };
  };

  const overallPercentage = overall_risk_score * 100;
  const riskLevel = getRiskLevel(overall_risk_score);

  const riskFactors = [
    { name: 'Skill Gap Risk', score: skill_gap_risk },
    { name: 'Experience Risk', score: experience_risk },
    { name: 'Consistency Risk', score: consistency_risk }
  ];

  return (
    <div className="flex flex-col gap-6 p-5 bg-red-50 rounded-xl border-l-4 border-red-600">
      {/* Overall Risk Gauge */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <span>Overall Risk Assessment</span>
        </h3>
        
        <div className="flex flex-col items-center gap-5">
          <svg viewBox="0 0 200 120" className="w-full max-w-sm h-auto">
            {/* Background arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="20"
              strokeLinecap="round"
            />
            
            {/* Risk arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke={riskLevel.color}
              strokeWidth="20"
              strokeLinecap="round"
              strokeDasharray={`${(overallPercentage / 100) * 502} 502`}
              className="animate-pulse"
            />
            
            {/* Center text */}
            <text x="100" y="75" textAnchor="middle" className="text-2xl font-bold" style={{ fill: riskLevel.color }}>
              {overallPercentage.toFixed(0)}%
            </text>
            <text x="100" y="95" textAnchor="middle" className="text-sm font-semibold" style={{ fill: '#6b7280' }}>
              {riskLevel.level}
            </text>
          </svg>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 w-full max-w-lg">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full" style={{ backgroundColor: '#22c55e' }}></span>
              <span className="text-xs text-gray-700">Minimal</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full" style={{ backgroundColor: '#84cc16' }}></span>
              <span className="text-xs text-gray-700">Low</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full" style={{ backgroundColor: '#eab308' }}></span>
              <span className="text-xs text-gray-700">Medium</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full" style={{ backgroundColor: '#ea580c' }}></span>
              <span className="text-xs text-gray-700">High</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full" style={{ backgroundColor: '#dc2626' }}></span>
              <span className="text-xs text-gray-700">Critical</span>
            </div>
          </div>
        </div>

        {/* Confidence Adjustment */}
        {confidence_adjustment !== 0 && (
          <div className={`flex items-center gap-2 mt-4 p-3 rounded ${confidence_adjustment > 0 ? 'bg-green-50' : 'bg-red-50'}`}>
            <span className="text-lg">{confidence_adjustment > 0 ? '⬆️' : '⬇️'}</span>
            <span className={`text-sm ${confidence_adjustment > 0 ? 'text-green-800' : 'text-red-800'}`}>
              Confidence {confidence_adjustment > 0 ? 'increased' : 'decreased'} by{' '}
              <strong>{Math.abs(confidence_adjustment * 100).toFixed(0)}%</strong>
            </span>
          </div>
        )}
      </div>

      {/* Risk Factors Breakdown */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Risk Factors Breakdown</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {riskFactors.map((factor) => {
            const percentage = factor.score * 100;
            const level = getRiskLevel(factor.score);
            
            return (
              <div key={factor.name} className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-lg">{level.icon}</span>
                  <span className="font-semibold text-gray-900">{factor.name}</span>
                </div>
                
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                  <div
                    className="h-full"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: level.color
                    }}
                  />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-semibold text-gray-700">{percentage.toFixed(0)}%</span>
                  <span className="text-xs font-semibold" style={{ color: level.color }}>{level.level}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Red Flags */}
      {red_flags && red_flags.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>🚩</span>
            <span>Red Flags Identified ({red_flags_count})</span>
          </h3>
          
          <div className="space-y-3">
            {red_flags.map((flag, idx) => (
              <div key={idx} className="flex gap-4 p-3 bg-red-50 rounded-lg border border-red-200">
                <div className="shrink-0 w-8 h-8 bg-red-200 text-red-700 rounded-full flex items-center justify-center font-semibold text-sm">
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <div className="text-gray-800">{flag}</div>
                  <div className="mt-2">
                    <button className="text-xs bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 transition-colors">
                      Review
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 p-3 bg-yellow-50 text-sm text-gray-700 rounded border-l-4 border-yellow-300">
            <strong>⚠️ Important:</strong> Red flags should be addressed during the interview or
            considered in hiring decisions. They may indicate potential issues or areas requiring
            closer examination.
          </div>
        </div>
      )}

      {/* Risk Summary */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Risk Summary</h3>
        
        <div>
          {overall_risk_score < 0.4 && (
            <div className="p-4 bg-green-50 border-l-4 border-green-500 rounded flex gap-3">
              <span className="text-2xl">✓</span>
              <div className="text-sm text-gray-800">
                <strong className="text-green-700">Low Risk Profile:</strong> The candidate presents minimal risk factors.
                Most data points are consistent, and identified skill gaps can be addressed
                through training.
              </div>
            </div>
          )}
          
          {overall_risk_score >= 0.4 && overall_risk_score < 0.7 && (
            <div className="p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded flex gap-3">
              <span className="text-2xl">⚠️</span>
              <div className="text-sm text-gray-800">
                <strong className="text-yellow-700">Moderate Risk:</strong> There are some concerns that should be addressed
                in the interview. Consider asking follow-up questions about inconsistencies or
                skill gaps.
              </div>
            </div>
          )}
          
          {overall_risk_score >= 0.7 && (
            <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded flex gap-3">
              <span className="text-2xl">🔴</span>
              <div className="text-sm text-gray-800">
                <strong className="text-red-700">High Risk Profile:</strong> Significant risk factors have been identified.
                Recommend thorough verification of key claims and careful consideration before
                proceeding with hire.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Next Steps</h3>
        
        <div className="space-y-3">
          {skill_gap_risk > 0.5 && (
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <span className="text-lg shrink-0">📚</span>
              <span className="text-sm text-gray-800">
                Plan training program to address identified skill gaps
              </span>
            </div>
          )}
          
          {experience_risk > 0.5 && (
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <span className="text-lg shrink-0">🤝</span>
              <span className="text-sm text-gray-800">
                Consider pairing with senior mentor for first 3-6 months
              </span>
            </div>
          )}
          
          {consistency_risk > 0.5 && (
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <span className="text-lg shrink-0">🔍</span>
              <span className="text-sm text-gray-800">
                Conduct thorough background verification and reference checks
              </span>
            </div>
          )}
          
          {red_flags_count > 0 && (
            <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <span className="text-lg shrink-0">💬</span>
              <span className="text-sm text-gray-800">
                Address red flags directly in interview or follow-up communication
              </span>
            </div>
          )}
          
          {overall_risk_score < 0.3 && (
            <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
              <span className="text-lg shrink-0">🎉</span>
              <span className="text-sm text-gray-800">
                Low-risk candidate - proceed with confidence
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskAssessmentChart;
