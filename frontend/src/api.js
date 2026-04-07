// Central API base URL — change this one line to point to staging/prod
export const API_BASE = 'http://127.0.0.1:8000';

export const endpoints = {
  candidates: `${API_BASE}/api/candidates`,
  requirements: `${API_BASE}/api/requirements`,
  systemActivity: `${API_BASE}/api/system/activity`,
  uploadResume: `${API_BASE}/api/candidates/upload-resume`,
  uploadRequirement: `${API_BASE}/api/requirements/upload-requirement`,
};
