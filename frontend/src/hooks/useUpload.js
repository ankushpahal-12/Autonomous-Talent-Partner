import { useState, useCallback, useEffect } from 'react';
import { endpoints, jobAPI } from '../api';

export function useUpload() {
  // ─────────────────────────────────────────────────────────────────────
  // FILE UPLOAD STATE
  // ─────────────────────────────────────────────────────────────────────
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadedCandidates, setUploadedCandidates] = useState([]);

  // ─────────────────────────────────────────────────────────────────────
  // JOB CREATION STATE
  // ─────────────────────────────────────────────────────────────────────
  const [jobTitle, setJobTitle] = useState('');
  const [jobText, setJobText] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');
  const [jobFile, setJobFile] = useState(null);
  const [fileUploadProgress, setFileUploadProgress] = useState(0);
  const [fileError, setFileError] = useState('');
  const [fileSuccess, setFileSuccess] = useState('');
  const [mode, setMode] = useState('upload');
  const [job, setJob] = useState(null);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [embeddingProgress, setEmbeddingProgress] = useState(0);

  // ─────────────────────────────────────────────────────────────────────
  // JOB EDITING STATE
  // ─────────────────────────────────────────────────────────────────────
  const [editingDescription, setEditingDescription] = useState(false);
  const [editedDescription, setEditedDescription] = useState('');
  const [suggestionPreview, setSuggestionPreview] = useState(null);
  const [previewingMerge, setPreviewingMerge] = useState(false);
  const [showPublishConfirm, setShowPublishConfirm] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // ─────────────────────────────────────────────────────────────────────
  // CANDIDATE MANAGEMENT STATE
  // ─────────────────────────────────────────────────────────────────────
  const [candidateName, setCandidateName] = useState('');
  const [candidateCV, setCandidateCV] = useState(null);
  const [candidateDragActive, setCandidateDragActive] = useState(false);
  const [candidateLoading, setCandidateLoading] = useState(false);
  const [candidateError, setCandidateError] = useState('');
  const [candidateSuccess, setCandidateSuccess] = useState('');
  const [candidateUploadProgress, setCandidateUploadProgress] = useState(0);
  const [analyzingCandidate, setAnalyzingCandidate] = useState(null);
  const [allCandidates, setAllCandidates] = useState([]);
  const [expandedJobId, setExpandedJobId] = useState(null);

  // ─────────────────────────────────────────────────────────────────────
  // JOBS MANAGEMENT STATE
  // ─────────────────────────────────────────────────────────────────────
  const [allJobs, setAllJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsError, setJobsError] = useState('');
  const [jobsFilterStatus, setJobsFilterStatus] = useState('all');
  const [jobsDisplayCount, setJobsDisplayCount] = useState(5);
  const [deletingJobId, setDeletingJobId] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [processingJobId, setProcessingJobId] = useState(null);

  // ─────────────────────────────────────────────────────────────────────
  // JOB OPERATIONS
  // ─────────────────────────────────────────────────────────────────────
  const createJob = useCallback(async (sessionId = null) => {
    if (!jobTitle.trim()) {
      setError("Job Title is mandatory.");
      return false;
    }
    if (mode === 'upload' && !jobFile) {
      setError("Please select a file to upload.");
      return false;
    }
    if (mode === 'write' && !jobText.trim()) {
      setError("Please enter job description.");
      return false;
    }
    if (mode === 'ai' && !aiPrompt.trim()) {
      setError("Please enter your requirements for AI to generate a JD.");
      return false;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const source = mode === 'upload' ? 'upload' : (mode === 'ai' ? 'ai_generated' : 'manual');
      let textContent = '';
      
      if (mode === 'write') {
        textContent = jobText;
      } else if (mode === 'ai') {
        textContent = aiPrompt;
      } else {
        textContent = `Job file: ${jobFile?.name || 'Uploaded file'}`;
      }
      
      const newJob = await jobAPI.createJob(jobTitle, textContent, source, sessionId);
      setJob(newJob);
      setStep(2);
      setSuccess("✓ Job Created Successfully! Now getting AI suggestions...");
      return true;
    } catch (err) {
      setError(err.message || "Failed to create job.");
      return false;
    } finally {
      setLoading(false);
    }
  }, [jobTitle, mode, jobFile, jobText, aiPrompt]);

  const getSuggestions = useCallback(async (jobId = null, sessionId = null) => {
    const id = jobId || job?.job_id;
    if (!id) return false;
    
    setLoading(true);
    setError('');
    
    try {
      await jobAPI.getSuggestions(id, sessionId);
      const updatedJob = await jobAPI.getJob(id, 'json');
      setJob(updatedJob);
      setSuccess("✓ AI Suggestions Generated! Review and apply them below.");
      return true;
    } catch (err) {
      setError("Failed to generate suggestions: " + err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [job?.job_id]);

  const applySuggestion = useCallback(async (sugId, sessionId = null) => {
    if (!job) return false;
    
    setLoading(true);
    setError('');
    try {
      const result = await jobAPI.applySuggestion(job.job_id, sugId, sessionId);
      setJob(result);
      setEditedDescription(result.description);
      
      if (!editingDescription) {
        setEditingDescription(true);
      }
      
      setSuccess("✓ Suggestion merged into description! Review the changes above.");
      setSuggestionPreview(null);
      setPreviewingMerge(false);
      return true;
    } catch (err) {
      setError("Failed to apply suggestion: " + err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [job, editingDescription]);

  const previewSuggestionMerge = useCallback((suggestion) => {
    setSuggestionPreview(suggestion);
    setPreviewingMerge(true);
  }, []);

  const cancelPreview = useCallback(() => {
    setSuggestionPreview(null);
    setPreviewingMerge(false);
  }, []);

  const startEditing = useCallback(() => {
    setEditedDescription(job?.description || '');
    setEditingDescription(true);
    setError('');
  }, [job?.description]);

  const cancelEditing = useCallback(() => {
    setEditingDescription(false);
    setEditedDescription('');
  }, []);

  const saveJobEdit = useCallback(async (sessionId = null) => {
    if (!editedDescription.trim()) {
      setError('Description cannot be empty');
      return false;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (sessionId) params.append('session_id', sessionId);
      const queryString = params.toString() ? `?${params}` : '';
      
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/jobs/edit/${job.job_id}${queryString}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            description: editedDescription,
            change_reason: 'HR manual edit before finalization'
          })
        }
      ).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);
        return r.json();
      });
      
      setJob(response);
      setEditingDescription(false);
      setEditedDescription('');
      setSuccess('✓ Job description updated successfully!');
      return true;
    } catch (err) {
      setError('Failed to update job: ' + err.message);
      return false;
    } finally {
      setLoading(false);
    }
  }, [job?.job_id, editedDescription]);

  const publishJob = useCallback(async (sessionId = null) => {
    if (!job || !job.job_id) return false;
    
    setLoading(true);
    setError('');
    try {
      const publishedJob = await jobAPI.publishJob(job.job_id, sessionId);
      setJob(publishedJob);
      setStep(4);
      setSuccess('✓ Job Published Successfully! Now active for hiring.');
      return true;
    } catch (err) {
      setError('Failed to publish job: ' + err.message);
      setStep(3);
      return false;
    } finally {
      setLoading(false);
    }
  }, [job]);

  const fetchAllCandidates = useCallback(async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/candidates?page=1&page_size=100');
      if (!response.ok) {
        console.warn(`Failed to fetch candidates: HTTP ${response.status}`);
        return;
      }
      
      const data = await response.json();
      if (data.status === 'success') {
        setAllCandidates(data.items || []);
      }
    } catch (err) {
      console.warn('Failed to fetch candidates:', err.message);
    }
  }, []);

  const fetchAllJobs = useCallback(async () => {
    setJobsLoading(true);
    setJobsError('');
    
    try {
      let url = 'http://127.0.0.1:8000/api/v1/jobs?limit=100&skip=0';
      if (jobsFilterStatus !== 'all') {
        url += `&status=${jobsFilterStatus}`;
      }
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch jobs`);
      }
      
      const data = await response.json();
      setAllJobs(data.jobs || []);
      return true;
    } catch (err) {
      setJobsError(err.message || 'Failed to fetch jobs');
      setAllJobs([]);
      return false;
    } finally {
      setJobsLoading(false);
    }
  }, [jobsFilterStatus]);

  // Fetch candidates on component mount
  useEffect(() => {
    fetchAllCandidates();
  }, [fetchAllCandidates]);

  const deleteJob = useCallback(async (jobId, jobTitle) => {
    setDeletingJobId(jobId);
    
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/jobs/${jobId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        let errorDetail = 'Failed to delete job';
        try {
          const error = JSON.parse(errorText);
          errorDetail = error.detail || errorDetail;
        } catch {
          errorDetail = errorText || errorDetail;
        }
        throw new Error(errorDetail);
      }
      
      setAllJobs(prevJobs => prevJobs.filter(j => j.job_id !== jobId));
      setSuccess(`✓ Job "${jobTitle}" deleted successfully!`);
      return true;
    } catch (err) {
      setError(`Failed to delete job: ${err.message}`);
      return false;
    } finally {
      setDeletingJobId(null);
      setShowDeleteConfirm(null);
    }
  }, []);

  const publishJobFromList = useCallback(async (jobId, jobTitle) => {
    setProcessingJobId(jobId);
    
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/jobs/publish/${jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to publish job');
      }
      
      const data = await response.json();
      
      if (!data || !data.job_id) {
        throw new Error('Invalid response from server');
      }
      
      setAllJobs(prevJobs => [...prevJobs].map(j => j.job_id === jobId ? data : j));
      setSuccess(`✓ Job "${jobTitle}" published successfully!`);
      return true;
    } catch (err) {
      setError(`Failed to publish job: ${err.message}`);
      return false;
    } finally {
      setProcessingJobId(null);
    }
  }, []);

  // ─────────────────────────────────────────────────────────────────────
  // CANDIDATE OPERATIONS
  // ─────────────────────────────────────────────────────────────────────
  const uploadCandidate = useCallback(async () => {
    if (!candidateName.trim()) {
      setCandidateError('❌ Please enter candidate name');
      return false;
    }
    if (!candidateCV) {
      setCandidateError('❌ Please select a CV file');
      return false;
    }

    setCandidateError('');
    setCandidateSuccess('');
    setCandidateLoading(true);
    
    const formData = new FormData();
    formData.append('file', candidateCV);

    setCandidateUploadProgress(20);
    await new Promise(resolve => setTimeout(resolve, 300));
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/candidates/upload-resume', {
        method: 'POST',
        body: formData
      });

      setCandidateUploadProgress(70);
      await new Promise(resolve => setTimeout(resolve, 300));

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({detail: 'Upload failed'}));
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setCandidateUploadProgress(100);
      
      setAllCandidates([...allCandidates, data]);
      setUploadedCandidates([...uploadedCandidates, data]);
      setCandidateSuccess(`✓ CV uploaded successfully for ${candidateName}!`);
      setCandidateName('');
      setCandidateCV(null);
      
      setTimeout(() => {
        setCandidateUploadProgress(0);
        setCandidateLoading(false);
      }, 1500);
      return true;
    } catch (err) {
      setCandidateUploadProgress(0);
      setCandidateError(`❌ ${err.message}`);
      setCandidateLoading(false);
      return false;
    }
  }, [candidateName, candidateCV, allCandidates, uploadedCandidates]);

  const analyzeCandidate = useCallback(async (candidateId) => {
    setAnalyzingCandidate(candidateId);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/candidates/${candidateId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) throw new Error('Analysis failed');
      
      const result = await response.json();
      setSuccess(`✓ Resume analysis started! Check WebSocket for updates.`);
      
      setAllCandidates(prev => prev.map(c => c.candidate_id === candidateId ? {...c, analysis: result} : c));
      return true;
    } catch (err) {
      setError(`Failed to analyze resume: ${err.message}`);
      return false;
    } finally {
      setAnalyzingCandidate(null);
    }
  }, []);

  // ─────────────────────────────────────────────────────────────────────
  // FILE HANDLING
  // ─────────────────────────────────────────────────────────────────────
  const validateFile = useCallback((file) => {
    if (!file) return { valid: false, error: 'No file selected' };
    
    const validTypes = ['application/pdf', 'application/msword', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
      'text/plain'];
    
    if (!validTypes.includes(file.type)) {
      return { valid: false, error: 'Only PDF, DOCX, DOC, and TXT files are supported' };
    }
    if (file.size > 10 * 1024 * 1024) {
      return { valid: false, error: 'File size must be less than 10MB' };
    }
    return { valid: true, error: null };
  }, []);

  // ─────────────────────────────────────────────────────────────────────
  // FILE SELECTION
  // ─────────────────────────────────────────────────────────────────────
  const handleFileSelect = useCallback((file) => {
    const validation = validateFile(file);
    if (!validation.valid) {
      setUploadError(validation.error);
      setSelectedFile(null);
      return false;
    }
    setUploadError(null);
    setSelectedFile(file);
    return true;
  }, [validateFile]);

  // ─────────────────────────────────────────────────────────────────────
  // FILE UPLOAD
  // ─────────────────────────────────────────────────────────────────────
  const uploadFile = useCallback(async (file, sessionId = null) => {
    if (!file) {
      setUploadError('No file selected');
      return false;
    }

    const validation = validateFile(file);
    if (!validation.valid) {
      setUploadError(validation.error);
      return false;
    }

    setUploading(true);
    setUploadError(null);
    setUploadProgress(0);
    setUploadSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      let uploadUrl = endpoints.uploadResume;
      if (sessionId) {
        uploadUrl += `?session_id=${encodeURIComponent(sessionId)}`;
      }

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 20;
        });
      }, 200);

      const response = await fetch(uploadUrl, {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const data = await response.json();
      const candidateName = file.name;

      setUploadSuccess({
        message: `✓ File uploaded successfully!`,
        candidate: candidateName,
        timestamp: new Date().toLocaleTimeString(),
      });

      setUploadedCandidates((prev) => [
        ...prev,
        {
          id: data.candidate_id || candidateName,
          name: candidateName,
          uploadedAt: new Date(),
        },
      ]);

      return true;
    } catch (err) {
      setUploadError(err.message || 'Upload failed');
      setUploadProgress(0);
      return false;
    } finally {
      setUploading(false);
    }
  }, [validateFile]);

  // ─────────────────────────────────────────────────────────────────────
  // CLEAR STATE
  // ─────────────────────────────────────────────────────────────────────
  const clearUploadState = useCallback(() => {
    setSelectedFile(null);
    setUploadProgress(0);
    setUploadError(null);
    setUploadSuccess(null);
    setUploadedCandidates([]);
  }, []);

  // ─────────────────────────────────────────────────────────────────────
  // PUBLIC API
  // ─────────────────────────────────────────────────────────────────────
  return {
    // File Upload State
    uploadProgress,
    uploading,
    uploadError,
    uploadSuccess,
    selectedFile,
    uploadedCandidates,
    
    // Job Creation State
    jobTitle, setJobTitle,
    jobText, setJobText,
    aiPrompt, setAiPrompt,
    jobFile, setJobFile,
    fileUploadProgress, setFileUploadProgress,
    fileError, setFileError,
    fileSuccess, setFileSuccess,
    mode, setMode,
    job, setJob,
    step, setStep,
    loading, setLoading,
    error, setError,
    success, setSuccess,
    embeddingProgress, setEmbeddingProgress,
    
    // Job Editing State
    editingDescription, setEditingDescription,
    editedDescription, setEditedDescription,
    suggestionPreview, setSuggestionPreview,
    previewingMerge, setPreviewingMerge,
    showPublishConfirm, setShowPublishConfirm,
    dragActive, setDragActive,
    
    // Candidate State
    candidateName, setCandidateName,
    candidateCV, setCandidateCV,
    candidateDragActive, setCandidateDragActive,
    candidateLoading, setCandidateLoading,
    candidateError, setCandidateError,
    candidateSuccess, setCandidateSuccess,
    candidateUploadProgress, setCandidateUploadProgress,
    analyzingCandidate, setAnalyzingCandidate,
    allCandidates, setAllCandidates,
    expandedJobId, setExpandedJobId,
    fetchAllCandidates,
    
    // Jobs Management State
    allJobs, setAllJobs,
    jobsLoading, setJobsLoading,
    jobsError, setJobsError,
    jobsFilterStatus, setJobsFilterStatus,
    jobsDisplayCount, setJobsDisplayCount,
    deletingJobId, setDeletingJobId,
    showDeleteConfirm, setShowDeleteConfirm,
    processingJobId, setProcessingJobId,
    
    // File Upload Actions
    handleFileSelect,
    uploadFile,
    clearUploadState,
    validateFile,
    
    // Job Actions
    createJob,
    getSuggestions,
    applySuggestion,
    previewSuggestionMerge,
    cancelPreview,
    startEditing,
    cancelEditing,
    saveJobEdit,
    publishJob,
    fetchAllJobs,
    deleteJob,
    publishJobFromList,
    
    // Candidate Actions
    uploadCandidate,
    analyzeCandidate,
    
    // Helpers
    canUpload: selectedFile !== null && !uploading,
  };
}
