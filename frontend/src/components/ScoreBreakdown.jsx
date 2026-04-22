import React from 'react';

/**
 * ScoreBreakdown Component
 * Displays comprehensive scoring breakdown with category scores,
 * confidence levels, and final recommendation
 */
const ScoreBreakdown = ({ comprehensiveAnalysis, enhancedDecision }) => {
  if (!comprehensiveAnalysis || !enhancedDecision) {
    return <div className="flex items-center justify-center min-h-50 p-6 bg-gray-100 text-gray-500 rounded-lg text-base">No scoring data available</div>;
  }

  const {
    data_aggregation = {},
    consistency_analysis = {},
    comparative_analysis = {},
    neo4j_insights = {},
    risk_assessment = {}
  } = comprehensiveAnalysis;

  const {
    final_score = 0,
    category_scores = {},
    meta_confidence_score = 0,
    decision = 'unknown',
    explanation = ''
  } = enhancedDecision;

  const getScoreColor = (score) => {
    if (score >= 80) return '#22c55e'; // green
    if (score >= 60) return '#eab308'; // yellow
    if (score >= 40) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  const getDecisionColor = (decision) => {
    switch (decision.toLowerCase()) {
      case 'hire':
      case 'strong_hire':
        return '#22c55e';
      case 'reject':
        return '#ef4444';
      case 'further_interview':
      case 'consider_further':
        return '#3b82f6';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className="flex flex-col gap-6 p-5">
      {/* Final Score Card */}
      <div className="bg-linear-to-br from-indigo-600 to-purple-700 rounded-xl p-6 text-white shadow-lg">
        <div className="flex flex-col md:flex-row gap-8">
          <div 
            className="flex flex-col items-center justify-center"
          >
            <div 
              className="w-32 h-32 rounded-full border-8 flex flex-col items-center justify-center"
              style={{ borderColor: getScoreColor(final_score) }}
            >
              <span className="text-4xl font-bold">{final_score}</span>
              <span className="text-lg opacity-90">/100</span>
            </div>
          </div>
          <div className="flex-1">
            <div 
              className="inline-block px-4 py-2 rounded-lg font-semibold text-sm mb-3"
              style={{ backgroundColor: getDecisionColor(decision) }}
            >
              {decision.toUpperCase().replace('_', ' ')}
            </div>
            <div className="text-base opacity-95 mb-3">
              Confidence: {(meta_confidence_score * 100).toFixed(0)}%
            </div>
            <div className="text-sm opacity-90 leading-relaxed">{explanation}</div>
          </div>
        </div>
      </div>

      {/* Category Scores */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h3 className="text-base font-semibold text-gray-900 mb-4">Category Breakdown</h3>
        <div className="space-y-4">
          {Object.entries(category_scores).map(([category, score]) => (
            <div key={category}>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-semibold text-gray-700">{category.replace('_', ' ')}</label>
                <span className="text-sm font-semibold" style={{ color: getScoreColor(score) }}>{score}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all duration-500"
                  style={{
                    width: `${score}%`,
                    backgroundColor: getScoreColor(score)
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Data Aggregation Metrics */}
      {Object.keys(data_aggregation).length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Data Aggregation</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {[
              { label: 'Technical Depth', value: data_aggregation.technical_depth, unit: '/100' },
              { label: 'Role Fit', value: data_aggregation.role_fit, unit: '/100' },
              { label: 'Culture Alignment', value: data_aggregation.culture_alignment, unit: '/100' },
              { label: 'Code Quality', value: data_aggregation.code_quality, unit: '/100' },
              { label: 'External Verification', value: data_aggregation.external_verification, unit: '/100' }
            ].map((metric) => (
              metric.value !== undefined && (
                <div key={metric.label} className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow text-center">
                  <div className="text-xs text-gray-600 font-semibold mb-2">{metric.label}</div>
                  <div className="text-2xl font-bold" style={{ color: getScoreColor(metric.value) }}>
                    {metric.value.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500">{metric.unit}</div>
                </div>
              )
            ))}
          </div>
        </div>
      )}

      {/* Consistency Analysis */}
      {Object.keys(consistency_analysis).length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Consistency Analysis</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-semibold text-gray-700">Timeline Consistent:</span>
              <span className={`text-lg font-bold ${consistency_analysis.timeline_consistent ? 'text-green-600' : 'text-red-600'}`}>
                {consistency_analysis.timeline_consistent ? '✓' : '✗'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-semibold text-gray-700">Experience Level Match:</span>
              <span className={`text-lg font-bold ${consistency_analysis.experience_level_match ? 'text-green-600' : 'text-red-600'}`}>
                {consistency_analysis.experience_level_match ? '✓' : '✗'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-semibold text-gray-700">Title Progression Logical:</span>
              <span className={`text-lg font-bold ${consistency_analysis.title_progression_logical ? 'text-green-600' : 'text-red-600'}`}>
                {consistency_analysis.title_progression_logical ? '✓' : '✗'}
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-semibold text-gray-700">Skill Consistency Score:</span>
              <span className="text-lg font-bold text-blue-600">{(consistency_analysis.skill_consistency * 100).toFixed(0)}%</span>
            </div>
            {consistency_analysis.red_flags && consistency_analysis.red_flags.length > 0 && (
              <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
                <h4 className="font-semibold text-red-800 mb-2">Red Flags:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {consistency_analysis.red_flags.map((flag, idx) => (
                    <li key={idx} className="text-sm text-red-700">{flag}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Comparative Analysis */}
      {Object.keys(comparative_analysis).length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Comparative Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow text-center">
              <div className="text-xs text-gray-600 font-semibold mb-2">Must-Have Skills Coverage</div>
              <div className="text-2xl font-bold text-blue-600">{(comparative_analysis.must_have_skills_coverage * 100).toFixed(0)}%</div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow text-center">
              <div className="text-xs text-gray-600 font-semibold mb-2">Nice-to-Have Skills Coverage</div>
              <div className="text-2xl font-bold text-blue-600">{(comparative_analysis.nice_to_have_skills_coverage * 100).toFixed(0)}%</div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow text-center">
              <div className="text-xs text-gray-600 font-semibold mb-2">Experience Seniority Match</div>
              <div className="text-2xl font-bold text-blue-600">{comparative_analysis.experience_seniority_match}</div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow text-center">
              <div className="text-xs text-gray-600 font-semibold mb-2">Learning Potential</div>
              <div className="text-2xl font-bold text-blue-600">{(comparative_analysis.learning_potential * 100).toFixed(0)}%</div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow text-center">
              <div className="text-xs text-gray-600 font-semibold mb-2">Growth Trajectory</div>
              <div className="text-2xl font-bold text-blue-600">{comparative_analysis.growth_trajectory}</div>
            </div>
            {comparative_analysis.overqualified_risk && (
              <div className="p-4 border-2 border-yellow-300 bg-yellow-50 rounded-lg text-center">
                <div className="text-xs text-yellow-700 font-semibold mb-2">Overqualification Risk</div>
                <div className="text-2xl font-bold text-yellow-600">⚠️ High</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Neo4j Insights */}
      {Object.keys(neo4j_insights).length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Neo4j Knowledge Graph Insights</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {neo4j_insights.career_path_fit && (
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="text-xs text-gray-600 font-semibold mb-2">Career Path Fit</div>
                <div className="text-lg font-bold text-gray-900">{neo4j_insights.career_path_fit}</div>
              </div>
            )}
            {neo4j_insights.domain_specialization && (
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="text-xs text-gray-600 font-semibold mb-2">Domain Specialization</div>
                <div className="text-lg font-bold text-gray-900">{neo4j_insights.domain_specialization}</div>
              </div>
            )}
            {neo4j_insights.learning_curve && (
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="text-xs text-gray-600 font-semibold mb-2">Learning Curve</div>
                <div className="text-lg font-bold text-gray-900">{neo4j_insights.learning_curve}</div>
              </div>
            )}
            {neo4j_insights.skill_gaps && neo4j_insights.skill_gaps.length > 0 && (
              <div className="p-4 border border-gray-200 rounded-lg md:col-span-2">
                <div className="text-xs text-gray-600 font-semibold mb-3">Skill Gaps Identified ({neo4j_insights.skill_gaps.length})</div>
                <div className="flex flex-wrap gap-2">
                  {neo4j_insights.skill_gaps.slice(0, 5).map((gap, idx) => (
                    <span key={idx} className="text-xs bg-red-100 text-red-800 px-3 py-1 rounded-full">{gap}</span>
                  ))}
                  {neo4j_insights.skill_gaps.length > 5 && (
                    <span className="text-xs bg-red-100 text-red-800 px-3 py-1 rounded-full">+{neo4j_insights.skill_gaps.length - 5} more</span>
                  )}
                </div>
              </div>
            )}
            {neo4j_insights.transferable_skills && neo4j_insights.transferable_skills.length > 0 && (
              <div className="p-4 border border-gray-200 rounded-lg md:col-span-2">
                <div className="text-xs text-gray-600 font-semibold mb-3">Transferable Skills ({neo4j_insights.transferable_skills.length})</div>
                <div className="flex flex-wrap gap-2">
                  {neo4j_insights.transferable_skills.slice(0, 5).map((skill, idx) => (
                    <span key={idx} className="text-xs bg-green-100 text-green-800 px-3 py-1 rounded-full">{skill}</span>
                  ))}
                  {neo4j_insights.transferable_skills.length > 5 && (
                    <span className="text-xs bg-green-100 text-green-800 px-3 py-1 rounded-full">+{neo4j_insights.transferable_skills.length - 5} more</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Risk Assessment Summary */}
      {Object.keys(risk_assessment).length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="text-base font-semibold text-gray-900 mb-4">Risk Assessment</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 border-2 border-red-300 bg-red-50 rounded-lg text-center">
              <div className="text-xs text-red-700 font-semibold mb-2">Overall Risk</div>
              <div className="text-2xl font-bold text-red-600">{(risk_assessment.overall_risk_score * 100).toFixed(0)}%</div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg text-center">
              <div className="text-xs text-gray-600 font-semibold mb-2">Skill Gap Risk</div>
              <div className="text-2xl font-bold text-gray-900">{(risk_assessment.skill_gap_risk * 100).toFixed(0)}%</div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg text-center">
              <div className="text-xs text-gray-600 font-semibold mb-2">Experience Risk</div>
              <div className="text-2xl font-bold text-gray-900">{(risk_assessment.experience_risk * 100).toFixed(0)}%</div>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg text-center">
              <div className="text-xs text-gray-600 font-semibold mb-2">Consistency Risk</div>
              <div className="text-2xl font-bold text-gray-900">{(risk_assessment.consistency_risk * 100).toFixed(0)}%</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScoreBreakdown;
