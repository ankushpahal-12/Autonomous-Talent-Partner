import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Upload, Users, Settings, Zap } from 'lucide-react';

export default function Layout({ children }) {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Upload Resumes', path: '/upload', icon: Upload },
    { name: 'Talent Pool', path: '/candidates', icon: Users },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="app-container">
      <aside className="sidebar">
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
