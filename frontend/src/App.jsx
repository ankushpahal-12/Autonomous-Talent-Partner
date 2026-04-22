import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import AdvancedDashboard from './pages/AdvancedDashboard';
import Upload from './pages/Upload';
import Candidates from './pages/Candidates';
import CandidateDetail from './pages/CandidateDetail';
import EnhancedCandidateDetail from './pages/EnhancedCandidateDetail';
import EnhanceCandidates from './pages/EnhanceCandidates';
import Applicants from './pages/Applicants';
import ActivityLogs from './pages/ActivityLogs';

import { SidebarProvider } from './context/SidebarContext';

function App() {
  return (
    <Router>
      <SidebarProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/advanced-dashboard" element={<AdvancedDashboard />} />
            <Route path="/upload" element={<Upload />} />
            {/* <Route path="/candidates-upload" element={<Candidates />} /> */}
            <Route path="/enhance-candidates" element={<EnhanceCandidates />} />
            <Route path="/applicants" element={<Applicants />} />
            <Route path="/activity" element={<ActivityLogs />} />
            <Route path="/candidates" element={<Dashboard />} />
            <Route path="/candidates/:id" element={<CandidateDetail />} />
            <Route path="/enhanced-candidates/:id" element={<EnhancedCandidateDetail />} />
          </Routes>
        </Layout>
      </SidebarProvider>
    </Router>
  );
}

export default App;
