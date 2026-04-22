import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Upload, Users, Settings, Zap, History as Activity, Menu, X, BarChart3, Sparkles } from 'lucide-react';
import ChatWidget from './ChatWidget';
import { useSidebar } from '../context/SidebarContext';

export default function Layout({ children }) {
  const location = useLocation();
  const { isSidebarOpen, toggleSidebar, closeSidebar } = useSidebar();

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Advanced Dashboard', path: '/advanced-dashboard', icon: BarChart3 },
    { name: 'Upload Jobs', path: '/upload', icon: Upload },
    { name: 'Applicants', path: '/applicants', icon: Users },
    { name: 'Enhance Candidates', path: '/enhance-candidates', icon: Sparkles },
    { name: 'Activity Feed', path: '/activity', icon: Activity },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  // Close sidebar on route change
  useEffect(() => {
    closeSidebar();
  }, [location.pathname]);

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
        onClick={closeSidebar}
      />

      <aside className={`sidebar ${isSidebarOpen ? 'open' : 'collapsed'}`}>
        <button className="sidebar-toggle-btn" onClick={toggleSidebar}>
          <Menu size={20} />
        </button>

        <div className="logo-container">
          <div className="score-circle" style={{ background: 'var(--accent)', color: 'white', border: 'none', minWidth: '32px' }}>
            <Zap size={20} fill="white" />
          </div>
          <span className="logo-text">Autonomous Talent</span>
        </div>

        <nav className="nav-links">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            const isMobile = typeof window !== 'undefined' && window.innerWidth <= 1024;
            
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => isMobile && closeSidebar()}
                title={!isSidebarOpen ? item.name : ''}
              >
                <Icon size={20} style={{ minWidth: '20px' }} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {isSidebarOpen && (
          <div style={{ marginTop: 'auto', padding: '0 12px' }}>
            <div className="glass-panel" style={{ padding: '16px', borderRadius: '16px', width: 'auto' }}>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>System Status</p>
              <p style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--success)' }}>● AI Online</p>
            </div>
          </div>
        )}
      </aside>

      <main className="main-content">
        {children}
      </main>
      <ChatWidget />
    </div>
  );
}
