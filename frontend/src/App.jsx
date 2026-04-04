import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import CandidateDetail from './pages/CandidateDetail';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/candidates" element={<Dashboard />} />
          <Route path="/candidates/:id" element={<CandidateDetail />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
