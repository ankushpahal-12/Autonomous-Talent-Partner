import { useState, useEffect, useMemo, useCallback } from 'react';
import { endpoints } from '../api';



function normalizeRequirement(req) {
  return {
    _id: req._id || req.id,
    title: req.title || 'Untitled Position',
    description: req.description || '',
    required_skills: Array.isArray(req.required_skills) ? req.required_skills : [],
    nice_to_have: Array.isArray(req.nice_to_have) ? req.nice_to_have : [],
    experience_level: req.experience_level || 'mid',
    min_experience: req.min_experience || 0,
    max_experience: req.max_experience || 10,
    salary_range: req.salary_range || { min: 0, max: 0 },
    department: req.department || 'Engineering',
    status: req.status || 'active',
    created_at: req.created_at || new Date().toISOString(),
    updated_at: req.updated_at || new Date().toISOString(),
  };
}

function filterRequirements(requirements, filters) {
  return requirements.filter(req => {
    // Status filter
    if (filters.status && req.status !== filters.status) {
      return false;
    }

    // Experience level filter
    if (filters.experienceLevel && req.experience_level !== filters.experienceLevel) {
      return false;
    }

    // Department filter
    if (filters.department && req.department !== filters.department) {
      return false;
    }

    // Skill search
    if (filters.searchSkill) {
      const hasSkill = [...req.required_skills, ...req.nice_to_have].some(skill =>
        skill.toLowerCase().includes(filters.searchSkill.toLowerCase())
      );
      if (!hasSkill) return false;
    }

    return true;
  });
}

function searchRequirements(requirements, query) {
  if (!query.trim()) return requirements;

  const q = query.toLowerCase();
  return requirements.filter(req => 
    req.title.toLowerCase().includes(q) ||
    req.description.toLowerCase().includes(q) ||
    req.department.toLowerCase().includes(q)
  );
}


export function useRequirements() {
  const [requirements, setRequirements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReqId, setSelectedReqId] = useState(null);

  // Filters & Search
  const [filters, setFilters] = useState({
    status: null,
    experienceLevel: null,
    department: null,
    searchSkill: null,
  });
  const [searchQuery, setSearchQuery] = useState('');


  const fetchRequirements = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(endpoints.requirements);
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      
      const data = await res.json();
      const normalized = (data || []).map(normalizeRequirement);
      setRequirements(normalized);
    } catch (err) {
      setError(err.message || 'Failed to fetch requirements');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchRequirements();
  }, []);

  // ─────────────────────────────────────────────────────────────────────
  // CRUD OPERATIONS
  // ─────────────────────────────────────────────────────────────────────

  const createRequirement = useCallback(async (reqData) => {
    try {
      const res = await fetch(endpoints.requirements, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reqData),
      });
      
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      
      const created = await res.json();
      const normalized = normalizeRequirement(created);
      setRequirements(prev => [normalized, ...prev]);
      return normalized;
    } catch (err) {
      throw new Error(err.message || 'Failed to create requirement');
    }
  }, []);

  const updateRequirement = useCallback(async (reqId, updates) => {
    try {
      const res = await fetch(`${endpoints.requirements}/${reqId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      
      const updated = await res.json();
      const normalized = normalizeRequirement(updated);
      setRequirements(prev => 
        prev.map(r => r._id === reqId ? normalized : r)
      );
      return normalized;
    } catch (err) {
      throw new Error(err.message || 'Failed to update requirement');
    }
  }, []);

  const deleteRequirement = useCallback(async (reqId) => {
    try {
      const res = await fetch(`${endpoints.requirements}/${reqId}`, {
        method: 'DELETE',
      });
      
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      
      setRequirements(prev => prev.filter(r => r._id !== reqId));
      if (selectedReqId === reqId) {
        setSelectedReqId(null);
      }
    } catch (err) {
      throw new Error(err.message || 'Failed to delete requirement');
    }
  }, [selectedReqId]);

  // ─────────────────────────────────────────────────────────────────────
  // FILTER & SEARCH OPERATIONS
  // ─────────────────────────────────────────────────────────────────────

  const updateFilter = useCallback((filterName, value) => {
    setFilters(prev => ({ ...prev, [filterName]: value }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      status: null,
      experienceLevel: null,
      department: null,
      searchSkill: null,
    });
    setSearchQuery('');
  }, []);

  const updateSearch = useCallback((query) => {
    setSearchQuery(query);
  }, []);

  // ─────────────────────────────────────────────────────────────────────
  // COMPUTED VALUES (Memoized)
  // ─────────────────────────────────────────────────────────────────────

  const filtered = useMemo(() => {
    let result = filterRequirements(requirements, filters);
    result = searchRequirements(result, searchQuery);
    return result;
  }, [requirements, filters, searchQuery]);

  const selectedRequirement = useMemo(() => {
    return requirements.find(r => r._id === selectedReqId) || null;
  }, [requirements, selectedReqId]);

  const statistics = useMemo(() => {
    return {
      total: requirements.length,
      active: requirements.filter(r => r.status === 'active').length,
      archived: requirements.filter(r => r.status === 'archived').length,
      byDepartment: requirements.reduce((acc, r) => {
        acc[r.department] = (acc[r.department] || 0) + 1;
        return acc;
      }, {}),
      byExperienceLevel: requirements.reduce((acc, r) => {
        acc[r.experience_level] = (acc[r.experience_level] || 0) + 1;
        return acc;
      }, {}),
    };
  }, [requirements]);

  const uniqueSkills = useMemo(() => {
    const skills = new Set();
    requirements.forEach(req => {
      req.required_skills.forEach(s => skills.add(s));
    });
    return Array.from(skills).sort();
  }, [requirements]);

  const uniqueDepartments = useMemo(() => {
    const depts = new Set(requirements.map(r => r.department));
    return Array.from(depts).sort();
  }, [requirements]);

  // ─────────────────────────────────────────────────────────────────────
  // PUBLIC API
  // ─────────────────────────────────────────────────────────────────────

  return {
    // State
    loading,
    error,
    requirements,
    filtered,
    searchQuery,
    filters,
    selectedReqId,
    selectedRequirement,

    // Statistics
    statistics,
    uniqueSkills,
    uniqueDepartments,

    // Actions
    refetch: fetchRequirements,
    createRequirement,
    updateRequirement,
    deleteRequirement,

    // Selection
    selectRequirement: setSelectedReqId,
    clearSelection: () => setSelectedReqId(null),

    // Filters & Search
    updateFilter,
    clearFilters,
    updateSearch,

    // Helpers
    hasData: requirements.length > 0,
    isEmpty: requirements.length === 0,
    hasFiltersActive: Object.values(filters).some(v => v !== null) || searchQuery.trim() !== '',
  };
}
