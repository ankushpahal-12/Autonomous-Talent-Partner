import React, { useState } from 'react';

/**
 * Neo4jInsights Component
 * Visualizes Neo4j knowledge graph analysis including:
 * - Skill relationships and transferability
 * - Career path alignment
 * - Learning curve estimation
 * - Domain specialization
 */
const Neo4jInsights = ({ neo4jInsights = {} }) => {
  const [expandedSection, setExpandedSection] = useState('overview');

  if (!neo4jInsights || Object.keys(neo4jInsights).length === 0) {
    return <div className="flex items-center justify-center min-h-[150px] p-6 bg-gray-100 text-gray-500 rounded-lg text-base">No Neo4j insights available</div>;
  }

  const {
    skill_relationships = {},
    transferable_skills = [],
    skill_gaps = [],
    career_path_fit = 'unknown',
    seniority_gap = 0,
    domain_specialization = 'unknown',
    learning_curve = 'unknown'
  } = neo4jInsights;

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const getLearningCurveColor = (curve) => {
    switch (curve.toLowerCase()) {
      case 'minimal':
        return '#22c55e';
      case 'short':
        return '#84cc16';
      case 'medium':
        return '#eab308';
      case 'long':
        return '#f97316';
      default:
        return '#6b7280';
    }
  };

  const getCareerFitColor = (fit) => {
    switch (fit.toLowerCase()) {
      case 'meets_requirement':
      case 'overqualified':
        return '#22c55e';
      case 'below_requirement':
        return '#ef4444';
      default:
        return '#3b82f6';
    }
  };

  return (
    <div className="flex flex-col gap-5 p-5 bg-gray-50 rounded-xl">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-white rounded-lg p-4 shadow-sm flex items-center gap-3 border-l-4 border-indigo-500 hover:shadow-md hover:scale-105 transition-all">
          <div className="text-2xl flex-shrink-0">📈</div>
          <div className="flex-1">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Career Path Fit</div>
            <div
              className="text-sm font-bold capitalize"
              style={{ color: getCareerFitColor(career_path_fit) }}
            >
              {career_path_fit.replace(/_/g, ' ').toUpperCase()}
            </div>
            {seniority_gap !== 0 && (
              <div className="text-xs text-gray-400 mt-1">
                {seniority_gap > 0 ? `+${seniority_gap}` : seniority_gap} level(s)
              </div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm flex items-center gap-3 border-l-4 border-indigo-500 hover:shadow-md hover:scale-105 transition-all">
          <div className="text-2xl flex-shrink-0">🎓</div>
          <div className="flex-1">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Learning Curve</div>
            <div
              className="text-sm font-bold"
              style={{ color: getLearningCurveColor(learning_curve) }}
            >
              {learning_curve.toUpperCase()}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm flex items-center gap-3 border-l-4 border-indigo-500 hover:shadow-md hover:scale-105 transition-all">
          <div className="text-2xl flex-shrink-0">🎯</div>
          <div className="flex-1">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Domain Specialization</div>
            <div className="text-sm font-bold">
              {domain_specialization === 'strong' ? '🔥 Strong' : '📚 General'}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm flex items-center gap-3 border-l-4 border-indigo-500 hover:shadow-md hover:scale-105 transition-all">
          <div className="text-2xl flex-shrink-0">🔍</div>
          <div className="flex-1">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Total Insights</div>
            <div className="text-sm font-bold text-gray-900">
              {transferable_skills.length + skill_gaps.length}
            </div>
          </div>
        </div>
      </div>

      {/* Collapsible Sections */}
      <div className="flex flex-col gap-3">
        {/* Skill Gaps Section */}
        {skill_gaps.length > 0 && (
          <div className="bg-white rounded-lg overflow-hidden shadow-sm">
            <div
              className="flex justify-between items-center p-4 bg-gradient-to-r from-gray-100 to-gray-200 cursor-pointer hover:bg-gray-200 transition-colors border-b-2 border-transparent hover:border-indigo-500"
              onClick={() => toggleSection('gaps')}
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">⚠️</span>
                <span className="font-semibold text-gray-900">Skill Gaps ({skill_gaps.length})</span>
              </div>
              <span className="text-xl">{expandedSection === 'gaps' ? '−' : '+'}</span>
            </div>
            {expandedSection === 'gaps' && (
              <div className="p-4">
                <div className="space-y-3">
                  {skill_gaps.map((gap, idx) => (
                    <div key={idx} className="flex items-center gap-4 p-3 bg-red-50 rounded">
                      <span className="font-semibold text-red-600 min-w-fit">{idx + 1}</span>
                      <span className="text-gray-800 flex-1">{gap}</span>
                      <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded">High Priority</span>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-yellow-50 text-sm text-gray-700 rounded border-l-4 border-yellow-300">
                  These are skills required for the role but not found in the candidate's profile.
                  Consider training or hiring complementary team members.
                </div>
              </div>
            )}
          </div>
        )}

        {/* Transferable Skills Section */}
        {transferable_skills.length > 0 && (
          <div className="bg-white rounded-lg overflow-hidden shadow-sm">
            <div
              className="flex justify-between items-center p-4 bg-gradient-to-r from-gray-100 to-gray-200 cursor-pointer hover:bg-gray-200 transition-colors border-b-2 border-transparent hover:border-indigo-500"
              onClick={() => toggleSection('transferable')}
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">⭐</span>
                <span className="font-semibold text-gray-900">Transferable Skills ({transferable_skills.length})</span>
              </div>
              <span className="text-xl">{expandedSection === 'transferable' ? '−' : '+'}</span>
            </div>
            {expandedSection === 'transferable' && (
              <div className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    {transferable_skills.slice(0, Math.ceil(transferable_skills.length / 2)).map((skill, idx) => (
                      <div key={idx} className="flex items-center gap-2 p-2 hover:bg-green-50 rounded">
                        <span className="text-green-500 font-bold">✓</span>
                        <span className="text-gray-800">{skill}</span>
                      </div>
                    ))}
                  </div>
                  {transferable_skills.length > 5 && (
                    <div className="space-y-2">
                      {transferable_skills.slice(Math.ceil(transferable_skills.length / 2)).map((skill, idx) => (
                        <div key={idx} className="flex items-center gap-2 p-2 hover:bg-green-50 rounded">
                          <span className="text-green-500 font-bold">✓</span>
                          <span className="text-gray-800">{skill}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="mt-4 p-3 bg-green-50 text-sm text-gray-700 rounded border-l-4 border-green-300">
                  These skills from the candidate's background can be applied to the required skills,
                  reducing the learning curve.
                </div>
              </div>
            )}
          </div>
        )}

        {/* Skill Relationships Section */}
        {Object.keys(skill_relationships).length > 0 && (
          <div className="bg-white rounded-lg overflow-hidden shadow-sm">
            <div
              className="flex justify-between items-center p-4 bg-gradient-to-r from-gray-100 to-gray-200 cursor-pointer hover:bg-gray-200 transition-colors border-b-2 border-transparent hover:border-indigo-500"
              onClick={() => toggleSection('relationships')}
            >
              <div className="flex items-center gap-3">
                <span className="text-lg">🔗</span>
                <span className="font-semibold text-gray-900">Skill Relationships ({Object.keys(skill_relationships).length})</span>
              </div>
              <span className="text-xl">{expandedSection === 'relationships' ? '−' : '+'}</span>
            </div>
            {expandedSection === 'relationships' && (
              <div className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(skill_relationships).map(([gap, candidates], idx) => (
                    <div key={idx} className="p-3 border border-gray-200 rounded hover:shadow-md transition-shadow">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-semibold text-indigo-600">{gap}</span>
                        <span className="text-blue-500">→</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {candidates.map((cand, cidx) => (
                          <span key={cidx} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{cand}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-blue-50 text-sm text-gray-700 rounded border-l-4 border-blue-300">
                  Shows how candidate's existing skills relate to missing required skills.
                  Green arrows indicate strong transferability.
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Learning Path Recommendation */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-l-4 border-blue-500 p-4">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-2xl">💡</span>
          <span className="font-bold text-gray-900 text-lg">Learning Path</span>
        </div>
        <div className="text-gray-700 leading-relaxed space-y-2">
          {learning_curve.toLowerCase() === 'minimal' && (
            <p>
              ✓ <strong>Fast onboarding expected.</strong> The candidate has most required skills
              or closely related skills. Minimal training needed.
            </p>
          )}
          {learning_curve.toLowerCase() === 'short' && (
            <p>
              ⚡ <strong>Quick ramp-up possible.</strong> The candidate has transferable skills and
              can quickly learn the few missing skills. Estimated ramp-up: 2-4 weeks.
            </p>
          )}
          {learning_curve.toLowerCase() === 'medium' && (
            <p>
              ⏱️ <strong>Moderate learning required.</strong> The candidate will need dedicated
              training on several skills. Estimated ramp-up: 1-3 months with proper support.
            </p>
          )}
          {learning_curve.toLowerCase() === 'long' && (
            <p>
              📚 <strong>Significant training needed.</strong> The candidate lacks many required
              skills but shows learning potential. Consider a structured onboarding program (3-6 months).
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Neo4jInsights;
