// Central API base URL — change this one line to point to staging/prod
export const API_BASE = 'http://127.0.0.1:8000/api/v1';

/**
 * Comprehensive API Service for Autonomous Talent Partner
 * Version 2.0 - Advanced Dashboard Integration
 */

export const endpoints = {
  // Candidate Management
  candidates: `${API_BASE}/candidates`,
  candidateDetail: (id) => `${API_BASE}/candidates/${id}`,
  uploadResume: `${API_BASE}/candidates/upload-resume`,
  deleteCandidate: (id) => `${API_BASE}/candidates/${id}`,
  
  // AI Review & Scoring
  reviewCandidate: (id) => `${API_BASE}/candidates/${id}/review`,
  enrichCandidate: (id) => `${API_BASE}/candidates/${id}/enrich`,
  recordDecision: (id) => `${API_BASE}/candidates/${id}/decision`,
  
  // Job Requirements
  requirements: `${API_BASE}/requirements`,
  uploadRequirement: `${API_BASE}/requirements/upload-requirement`,
  
  // New Job Builder
  jobs: `${API_BASE}/jobs`,
  jobSuggestions: (id) => `${API_BASE}/jobs/suggestions/${id}`,
  jobApplySuggestion: (id, sugId) => `${API_BASE}/jobs/apply-suggestions/${id}/${sugId}`,
  jobFinalize: (id) => `${API_BASE}/jobs/finalize/${id}`,
  jobEdit: (id) => `${API_BASE}/jobs/edit/${id}`,
  
  // Advanced Analytics
  candidateScores: (id) => `${API_BASE}/candidates/${id}/scores`,
  comprehensiveAnalysis: (id) => `${API_BASE}/candidates/${id}/comprehensive-analysis`,
  riskAssessment: (id) => `${API_BASE}/candidates/${id}/risk-assessment`,
  neographAnalysis: (id) => `${API_BASE}/candidates/${id}/neo4j-analysis`,
  feedbackLoops: (id) => `${API_BASE}/candidates/${id}/feedback`,
  
  // System & Dashboard
  systemActivity: `${API_BASE}/system/activity`,
  systemStats: `${API_BASE}/system/stats`,
  dashboardMetrics: `${API_BASE}/system/metrics`,
  
  // Chat & Communication
  chat: `${API_BASE}/system/chat`,
  
  // Batch Operations
  matchCandidates: `${API_BASE}/candidates/match`,
  bullkReview: `${API_BASE}/candidates/bulk-review`,
};

/**
 * Advanced API Client with error handling, retries, and caching
 */
export class APIClient {
  constructor(baseURL = API_BASE) {
    this.baseURL = baseURL;
    this.cache = new Map();
    this.timeouts = new Map();
  }

  /**
   * Generic fetch wrapper with error handling
   */
  async request(url, options = {}) {
    // Filter out internal options that aren't part of Fetch API (caching is handled at the get() level)
    // eslint-disable-next-line no-unused-vars
    const { cache, ...fetchOptions } = options;

    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
      ...fetchOptions,
      // Set proper fetch cache control (don't let invalid values slip through)
      cache: 'no-store',
    };

    try {
      const response = await fetch(url, defaultOptions);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${url}]:`, error);
      throw error;
    }
  }

  /**
   * GET request with optional caching
   */
  async get(url, options = {}) {
    const cacheKey = url;
    const cachedData = this.cache.get(cacheKey);

    if (cachedData && !options.skipCache) {
      return cachedData;
    }

    const { cache, ...fetchOptions } = options;
    const shouldUseCache = cache !== false;

    const data = await this.request(url, {
      method: 'GET',
      ...fetchOptions,
    });

    // Only cache if caching is enabled (default: true)
    if (shouldUseCache) {
      this.cache.set(cacheKey, data);
      // Auto-clear cache after 5 minutes
      if (this.timeouts.has(cacheKey)) {
        clearTimeout(this.timeouts.get(cacheKey));
      }
      this.timeouts.set(
        cacheKey,
        setTimeout(() => this.cache.delete(cacheKey), 5 * 60 * 1000)
      );
    }

    return data;
  }

  /**
   * POST request
   */
  async post(url, body, options = {}) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(body),
      ...options,
    });
  }

  /**
   * PATCH request
   */
  async patch(url, body, options = {}) {
    return this.request(url, {
      method: 'PATCH',
      body: JSON.stringify(body),
      ...options,
    });
  }

  /**
   * DELETE request
   */
  async delete(url, options = {}) {
    return this.request(url, {
      method: 'DELETE',
      ...options,
    });
  }

  /**
   * Clear all caches
   */
  clearCache() {
    this.cache.clear();
    this.timeouts.forEach(timeout => clearTimeout(timeout));
    this.timeouts.clear();
  }
}

// Initialize API client instance
export const apiClient = new APIClient(API_BASE);

/**
 * Candidate API Methods
 */
export const candidateAPI = {
  /**
   * Get all candidates with pagination
   */
  async listCandidates(page = 1, pageSize = 20, options = {}) {
    const { skipCache, ...filters } = options;
    const params = new URLSearchParams({
      page,
      page_size: pageSize,
      ...filters,
    });
    return apiClient.get(`${endpoints.candidates}?${params}`, { skipCache });
  },

  /**
   * Get specific candidate with full details
   */
  async getCandidate(candidateId, options = {}) {
    return apiClient.get(endpoints.candidateDetail(candidateId), options);
  },

  /**
   * Upload resume with optional session_id for real-time updates via WebSocket
   */
  async uploadResume(file, sessionId = null) {
    const formData = new FormData();
    formData.append('file', file);

    let url = endpoints.uploadResume;
    if (sessionId) {
      url += `?session_id=${encodeURIComponent(sessionId)}`;
    }

    return apiClient.request(url, {
      method: 'POST',
      body: formData,
      headers: {},
    });
  },

  /**
   * Trigger AI review with optional session_id for real-time updates via WebSocket
   */
  async reviewCandidate(candidateId, sessionId = null) {
    let url = endpoints.reviewCandidate(candidateId);
    if (sessionId) {
      url += `?session_id=${encodeURIComponent(sessionId)}`;
    }
    const result = await apiClient.post(url, {});
    // Clear the candidates cache so fresh data is fetched
    apiClient.clearCache();
    return result;
  },

  /**
   * Enrich candidate with external data
   */
  async enrichCandidate(candidateId, sessionId = null) {
    let url = endpoints.enrichCandidate(candidateId);
    if (sessionId) {
      url += `?session_id=${encodeURIComponent(sessionId)}`;
    }
    const result = await apiClient.post(url, {});
    // Clear the candidates cache so fresh data is fetched
    apiClient.clearCache();
    return result;
  },

  /**
   * Record HR decision
   */
  async recordDecision(candidateId, decision, reason = '') {
    const result = await apiClient.patch(endpoints.recordDecision(candidateId), {
      decision,
      reason,
    });
    // Clear the candidates cache so fresh data is fetched
    apiClient.clearCache();
    return result;
  },

  /**
   * Delete candidate
   */
  async deleteCandidate(candidateId) {
    return apiClient.delete(endpoints.deleteCandidate(candidateId));
  },

  /**
   * Get comprehensive scoring
   */
  async getComprehensiveAnalysis(candidateId) {
    return apiClient.get(endpoints.comprehensiveAnalysis(candidateId));
  },

  /**
   * Get risk assessment
   */
  async getRiskAssessment(candidateId) {
    return apiClient.get(endpoints.riskAssessment(candidateId));
  },

  /**
   * Get Neo4j graph analysis
   */
  async getNeo4jAnalysis(candidateId) {
    return apiClient.get(endpoints.neographAnalysis(candidateId));
  },

  /**
   * Get feedback history
   */
  async getFeedbackHistory(candidateId) {
    return apiClient.get(endpoints.feedbackLoops(candidateId));
  },

  /**
   * Match candidates to job
   */
  async matchCandidates(jobDescription, topK = 10) {
    return apiClient.post(endpoints.matchCandidates, {
      job_description: jobDescription,
      top_k: topK,
    });
  },
};

/**
 * System & Dashboard API Methods
 */
export const systemAPI = {
  /**
   * Get system statistics
   */
  async getStats() {
    return apiClient.get(endpoints.systemStats, { cache: false });
  },

  /**
   * Get dashboard metrics
   */
  async getMetrics() {
    return apiClient.get(endpoints.dashboardMetrics, { cache: false });
  },

  /**
   * Get activity logs
   */
  async getActivity(limit = 50) {
    return apiClient.get(`${endpoints.systemActivity}?limit=${limit}`);
  },
};

/**
 * Requirements API Methods
 */
export const requirementAPI = {
  /**
   * Get all requirements
   */
  async listRequirements() {
    return apiClient.get(endpoints.requirements);
  },

  /**
   * Upload job requirement
   */
  async uploadRequirement(file) {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.request(endpoints.uploadRequirement, {
      method: 'POST',
      body: formData,
      headers: {},
    });
  },
};

/**
 * Modern Job Builder API Methods
 */
export const jobAPI = {
  async createJob(title, text, source, sessionId = null) {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    const url = params.toString() ? `${endpoints.jobs}?${params}` : endpoints.jobs;
    return apiClient.post(url, { title, text, source });
  },
  
  async getJob(jobId, format = 'json') {
    return apiClient.get(`${endpoints.jobs}/${jobId}?format=${format}`, { cache: false });
  },
  
  async editJob(jobId, payload) {
    return apiClient.request(endpoints.jobEdit(jobId), {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },
  
  async getSuggestions(jobId, sessionId = null) {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    const url = params.toString() ? `${endpoints.jobSuggestions(jobId)}?${params}` : endpoints.jobSuggestions(jobId);
    return apiClient.post(url, {});
  },
  
  async applySuggestion(jobId, suggestionId, sessionId = null) {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    const url = params.toString() ? `${endpoints.jobApplySuggestion(jobId, suggestionId)}?${params}` : endpoints.jobApplySuggestion(jobId, suggestionId);
    return apiClient.post(url, {});
  },
  
  async finalizeJob(jobId, sessionId = null) {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    const url = params.toString() ? `${endpoints.jobFinalize(jobId)}?${params}` : endpoints.jobFinalize(jobId);
    return apiClient.post(url, {});
  },

  async publishJob(jobId, sessionId = null) {
    const params = new URLSearchParams();
    if (sessionId) params.append('session_id', sessionId);
    const url = params.toString() ? `${endpoints.jobs}/publish/${jobId}?${params}` : `${endpoints.jobs}/publish/${jobId}`;
    return apiClient.post(url, {});
  },

  async generateEmbeddings(jobId) {
    return apiClient.post(`${endpoints.jobs}/embeddings/${jobId}`, {});
  }
};
