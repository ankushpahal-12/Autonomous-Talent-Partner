import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Upload, Users, Settings, Zap, History as Activity, Menu, X } from 'lucide-react';

export default function Layout({ children }) {
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Upload Resumes', path: '/upload', icon: Upload },
    { name: 'Job Requirements', path: '/requirements', icon: Zap },
    { name: 'Applicants', path: '/applicants', icon: Users },
    { name: 'Activity Feed', path: '/activity', icon: Activity },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  // Close sidebar on route change
  useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  return (
    <div className="app-container">
      {/* Mobile Header */}
      <header className="mobile-header">
        <div className="logo-container" style={{ marginBottom: 0, paddingLeft: 0 }}>
          <div className="score-circle" style={{ background: 'var(--accent)', color: 'white', border: 'none', width: '32px', height: '32px' }}>
            <Zap size={16} fill="white" />
          </div>
          <span className="logo-text" style={{ fontSize: '1rem' }}>Autonomous Talent</span>
        </div>
        <button className="search-icon-btn" onClick={toggleSidebar}>
          {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </header>

      {/* Backdrop */}
      <div 
        className={`mobile-overlay ${isSidebarOpen ? 'visible' : ''}`} 
        onClick={() => setIsSidebarOpen(false)}
      />

      <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="logo-container">
          <div className="score-circle" style={{ background: 'var(--accent)', color: 'white', border: 'none' }}>
            <Zap size={20} fill="white" />
          </div>
          <span className="logo-text">Autonomous Talent</span>
        </div>

        <nav className="nav-links">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)}
              >
                <Icon size={20} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div style={{ marginTop: 'auto', padding: '0 12px' }}>
          <div className="glass-panel" style={{ padding: '16px', borderRadius: '16px', width: 'auto' }}>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>System Status</p>
            <p style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--success)' }}>● AI Online</p>
          </div>
        </div>
      </aside>

      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
