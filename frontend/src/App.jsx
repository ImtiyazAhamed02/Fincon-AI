import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, TrendingUp, PieChart, Bot, Clock,
  Activity, ChevronRight, Bell, Menu, X, Sun, Moon,
  Zap, Shield
} from 'lucide-react';
import { useTheme } from './context/ThemeContext';
import Dashboard from './pages/Dashboard';
import StockAnalysis from './pages/StockAnalysis';
import Portfolio from './pages/Portfolio';
import AgentMonitor from './pages/AgentMonitor';
import History from './pages/History';

const NAV = [
  { to: '/',         icon: LayoutDashboard, label: 'Dashboard',       end: true },
  { to: '/analysis', icon: TrendingUp,      label: 'Stock Analysis'          },
  { to: '/portfolio',icon: PieChart,        label: 'Portfolio'               },
  { to: '/history',  icon: Clock,           label: 'History'                 },
];

// ─────────────────────────────────────────────────────────────────────────────
// Sidebar
// ─────────────────────────────────────────────────────────────────────────────
function Sidebar({ isOpen, onClose }) {
  const { isDark } = useTheme();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside className={`
        w-[260px] flex flex-col h-screen
        fixed inset-y-0 left-0 z-50
        transform transition-transform duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}
        style={{
          background: '#000000',
          borderRight: `1px solid #171717`,
        }}
      >
        {/* Logo */}
        <div className="px-6 pt-6 pb-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center relative"
              style={{
                background: 'var(--gradient-primary)',
              }}>
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight text-white">FINCON</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="status-dot status-dot-online" style={{ width: 6, height: 6, background: '#ffffff' }} />
                <span className="text-[10px] font-bold uppercase" style={{ color: '#888888' }}>AI Platform</span>
              </div>
            </div>
          </div>
          <button onClick={onClose}
            className="md:hidden p-1.5 rounded-lg transition-colors"
            style={{ color: 'var(--text-tertiary)' }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 overflow-y-auto">
          <p className="text-[10px] font-bold uppercase tracking-widest px-3 mb-3"
            style={{ color: 'var(--text-muted)' }}>
            Main Menu
          </p>
          <div className="space-y-1">
            {NAV.map(({ to, icon: Icon, label, end }) => (
              <NavLink key={to} to={to} end={end} onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-bold transition-all duration-150 group relative`
                }
                style={({ isActive }) => ({
                  color: isActive ? '#ffffff' : '#888888',
                  background: isActive ? '#121212' : 'transparent',
                  borderLeft: isActive ? '3px solid #6366f1' : '3px solid transparent',
                })}
              >
                {({ isActive }) => (
                  <>
                    <Icon style={{
                      width: 18, height: 18,
                      color: isActive ? '#6366f1' : '#555555',
                      transition: 'color 0.15s',
                    }} />
                    <span className="flex-1">{label}</span>
                    {isActive && <ChevronRight className="w-3.5 h-3.5" style={{ color: '#6366f1', opacity: 0.8 }} />}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Bottom Section */}
        <div className="p-4" style={{ borderTop: '1px solid #171717' }}>
          {/* System Status */}
          <div className="card rounded-lg p-3 mb-3 hidden sm:block" style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}>
            <p className="text-[10px] font-bold uppercase tracking-widest mb-2.5"
              style={{ color: '#555555' }}>
              System Status
            </p>
            <div className="space-y-2">
              {[
                { label: 'AI Engine', status: 'Online', icon: Zap, color: '#ffffff' },
                { label: 'Risk Shield', status: 'Active', icon: Shield, color: '#ffffff' },
              ].map(({ label, status, icon: SIcon, color }) => (
                <div key={label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <SIcon className="w-3.5 h-3.5" style={{ color: '#6366f1' }} />
                    <span className="text-xs" style={{ color: '#888888' }}>{label}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="status-dot" style={{ width: 5, height: 5, background: '#ffffff' }} />
                    <span className="text-[10px] font-bold uppercase" style={{ color }}>{status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* User */}
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-md flex-shrink-0 flex items-center justify-center text-xs font-bold text-white"
              style={{ background: '#6366f1' }}>
              FU
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold truncate" style={{ color: '#ffffff' }}>FINCON User</p>
              <p className="text-[10px] truncate" style={{ color: '#555555' }}>Pro Plan</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Top Bar
// ─────────────────────────────────────────────────────────────────────────────
function TopBar({ title, subtitle, onMenuClick }) {
  const { isDark, toggleTheme } = useTheme();

  return (
    <header className="px-4 sm:px-8 py-3.5 flex items-center justify-between sticky top-0 z-20"
      style={{
        background: 'var(--bg-header)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border-subtle)',
      }}
    >
      <div className="flex items-center">
        <button onClick={onMenuClick}
          className="md:hidden p-2 mr-3 rounded-xl transition-colors"
          style={{ color: 'var(--text-secondary)' }}
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-base sm:text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
            {title}
          </h1>
          {subtitle && (
            <p className="text-[10px] sm:text-xs mt-0.5 hidden sm:block" style={{ color: 'var(--text-tertiary)' }}>
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl transition-all duration-200"
          style={{
            background: isDark ? 'rgba(79, 139, 255, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            border: `1px solid ${isDark ? 'rgba(79, 139, 255, 0.2)' : 'rgba(245, 158, 11, 0.2)'}`,
            color: isDark ? 'var(--accent-blue)' : 'var(--accent-amber)',
          }}
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Notifications */}
        <div className="relative p-2 rounded-xl transition-colors cursor-pointer"
          style={{ color: 'var(--text-tertiary)' }}>
          <Bell className="w-4.5 h-4.5" style={{ width: 18, height: 18 }} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
            style={{ background: 'var(--accent-blue)' }} />
        </div>

        {/* API Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl"
          style={{
            background: isDark ? 'rgba(16, 185, 129, 0.08)' : 'rgba(5, 150, 105, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
          }}>
          <span className="status-dot status-dot-online" style={{ width: 6, height: 6 }} />
          <span className="text-[10px] sm:text-xs font-semibold whitespace-nowrap"
            style={{ color: 'var(--accent-emerald)' }}>
            API Live
          </span>
        </div>
      </div>
    </header>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page Meta
// ─────────────────────────────────────────────────────────────────────────────
const PAGE_META = {
  '/':          { title: 'Dashboard',      subtitle: 'Your AI-powered financial command center' },
  '/analysis':  { title: 'Stock Analysis', subtitle: 'Run individual or coordinated analysis modules' },
  '/portfolio': { title: 'Portfolio',      subtitle: 'Manage and optimize your investments' },
  '/history':   { title: 'History',        subtitle: 'Browse past analysis sessions' },
};

// ─────────────────────────────────────────────────────────────────────────────
// Layout
// ─────────────────────────────────────────────────────────────────────────────
function Layout() {
  const { pathname } = useLocation();
  const { isDark } = useTheme();
  const meta = PAGE_META[pathname] || { title: 'FINCON', subtitle: '' };
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden w-full" style={{ background: 'var(--bg-base)' }}>
      {/* Drawer Sidebar */}
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      
      {/* Desktop layout spacing */}
      <div className="hidden md:block w-[260px] flex-shrink-0" />

      {/* Main viewport */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0 w-full">
        <TopBar title={meta.title} subtitle={meta.subtitle} onMenuClick={() => setIsSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/"         element={<Dashboard />} />
            <Route path="/analysis" element={<StockAnalysis />} />
            <Route path="/portfolio"element={<Portfolio />} />
            <Route path="/history"  element={<History />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
