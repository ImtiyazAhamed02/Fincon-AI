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
  { to: '/agents',   icon: Bot,             label: 'Agent Monitor'           },
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
        w-[260px] flex-shrink-0 flex flex-col h-screen
        fixed inset-y-0 left-0 z-50
        transform transition-transform duration-200 ease-in-out
        md:relative md:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}
        style={{
          background: isDark
            ? 'linear-gradient(180deg, #080c1a 0%, #0a0f20 100%)'
            : 'linear-gradient(180deg, #ffffff 0%, #f8f9fc 100%)',
          borderRight: `1px solid var(--border-subtle)`,
        }}
      >
        {/* Logo */}
        <div className="px-6 pt-6 pb-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center relative"
              style={{
                background: 'var(--gradient-primary)',
                boxShadow: '0 4px 20px rgba(79, 139, 255, 0.35)',
              }}>
              <Activity className="w-5 h-5 text-white" />
              {/* Glow ring */}
              <div className="absolute inset-0 rounded-2xl animate-pulse-glow"
                style={{
                  background: 'var(--gradient-primary)',
                  opacity: 0.3,
                  filter: 'blur(8px)',
                }}
              />
            </div>
            <div>
              <span className="text-lg font-black tracking-tight gradient-text">FINCON</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="status-dot status-dot-online" style={{ width: 6, height: 6 }} />
                <span className="text-[10px] font-medium" style={{ color: 'var(--text-tertiary)' }}>AI Platform</span>
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
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group relative ${
                    isActive ? '' : ''
                  }`
                }
                style={({ isActive }) => ({
                  color: isActive ? 'var(--text-primary)' : 'var(--text-tertiary)',
                  background: isActive
                    ? (isDark ? 'rgba(79, 139, 255, 0.1)' : 'rgba(59, 130, 246, 0.08)')
                    : 'transparent',
                  borderLeft: isActive ? '3px solid var(--accent-blue)' : '3px solid transparent',
                })}
              >
                {({ isActive }) => (
                  <>
                    <Icon style={{
                      width: 18, height: 18,
                      color: isActive ? 'var(--accent-blue)' : 'var(--text-muted)',
                      transition: 'color 0.15s',
                    }} />
                    <span className="flex-1">{label}</span>
                    {isActive && <ChevronRight className="w-3.5 h-3.5" style={{ color: 'var(--accent-blue)', opacity: 0.6 }} />}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Bottom Section */}
        <div className="p-4" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          {/* System Status */}
          <div className="card rounded-xl p-3 mb-3 hidden sm:block">
            <p className="text-[10px] font-bold uppercase tracking-widest mb-2.5"
              style={{ color: 'var(--text-muted)' }}>
              System Status
            </p>
            <div className="space-y-2">
              {[
                { label: 'AI Engine', status: 'Online', icon: Zap, color: 'var(--accent-emerald)' },
                { label: 'Risk Shield', status: 'Active', icon: Shield, color: 'var(--accent-blue)' },
              ].map(({ label, status, icon: SIcon, color }) => (
                <div key={label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <SIcon className="w-3.5 h-3.5" style={{ color }} />
                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="status-dot status-dot-online" style={{ width: 5, height: 5 }} />
                    <span className="text-[10px] font-medium" style={{ color }}>{status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* User */}
          <div className="flex items-center gap-3 px-2">
            <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white"
              style={{ background: 'var(--gradient-primary)' }}>
              FU
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold truncate" style={{ color: 'var(--text-primary)' }}>FINCON User</p>
              <p className="text-[10px] truncate" style={{ color: 'var(--text-muted)' }}>Pro Plan</p>
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
        background: isDark
          ? 'rgba(8, 12, 26, 0.85)'
          : 'rgba(255, 255, 255, 0.85)',
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
  '/analysis':  { title: 'Stock Analysis', subtitle: 'Run individual or full multi-agent analysis' },
  '/portfolio': { title: 'Portfolio',      subtitle: 'Manage and optimize your investments' },
  '/agents':    { title: 'Agent Monitor',  subtitle: 'Real-time agent status and execution logs' },
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
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar title={meta.title} subtitle={meta.subtitle} onMenuClick={() => setIsSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/"         element={<Dashboard />} />
            <Route path="/analysis" element={<StockAnalysis />} />
            <Route path="/portfolio"element={<Portfolio />} />
            <Route path="/agents"   element={<AgentMonitor />} />
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
