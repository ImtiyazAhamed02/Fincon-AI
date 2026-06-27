import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, TrendingUp, PieChart, Bot, Clock,
  Activity, ChevronRight, Bell, Settings, Menu
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import StockAnalysis from './pages/StockAnalysis';
import Portfolio from './pages/Portfolio';
import AgentMonitor from './pages/AgentMonitor';
import History from './pages/History';

// ─────────────────────────────────────────────────────────────────────────────
// Nav items — mapped to real FINCON pages
// ─────────────────────────────────────────────────────────────────────────────
const NAV = [
  { to: '/',         icon: LayoutDashboard, label: 'Dashboard',       end: true },
  { to: '/analysis', icon: TrendingUp,      label: 'Stock Analysis'          },
  { to: '/portfolio',icon: PieChart,        label: 'Portfolio'               },
  { to: '/agents',   icon: Bot,             label: 'Agent Monitor'           },
  { to: '/history',  icon: Clock,           label: 'History'                 },
];

function Sidebar() {
  return (
    <aside className="w-[240px] flex-shrink-0 flex flex-col h-screen sticky top-0"
      style={{ background: 'rgba(9,13,31,0.95)', borderRight: '1px solid rgba(255,255,255,0.05)' }}>

      {/* Logo */}
      <div className="px-6 pt-7 pb-6">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'linear-gradient(135deg,#2563eb,#7c3aed)', boxShadow: '0 0 20px rgba(37,99,235,0.4)' }}>
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-lg font-black tracking-tight gradient-text-blue">FINCON</span>
            <div className="flex items-center space-x-1.5 mt-0.5">
              <span className="status-dot-green" style={{ width: 6, height: 6 }} />
              <span className="text-[10px] text-slate-500 font-medium">AI Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto">
        <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest px-3 mb-2">Navigation</p>
        {NAV.map(({ to, icon: Icon, label, end }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group relative ${
                isActive
                  ? 'text-white'
                  : 'text-slate-500 hover:text-slate-200 hover:bg-white/5'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute inset-0 rounded-xl"
                    style={{ background: 'linear-gradient(135deg,rgba(37,99,235,0.2),rgba(124,58,237,0.15))', border: '1px solid rgba(59,130,246,0.25)' }} />
                )}
                <Icon className={`w-4.5 h-4.5 relative z-10 transition-colors ${isActive ? 'text-blue-400' : 'text-slate-600 group-hover:text-slate-400'}`} style={{ width: 17, height: 17 }} />
                <span className="relative z-10 flex-1">{label}</span>
                {isActive && <ChevronRight className="w-3.5 h-3.5 relative z-10 text-blue-400/60" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="p-4 mt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        {/* Agent Status Bar */}
        <div className="rounded-xl p-3 mb-3" style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.05)' }}>
          <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-widest mb-2">Agent Status</p>
          {[
            { label: 'News Agent', color: '#10b981' },
            { label: 'Tech Agent', color: '#3b82f6' },
            { label: 'Risk Agent', color: '#f59e0b' },
            { label: 'Portfolio Agent', color: '#8b5cf6' },
          ].map(({ label, color }) => (
            <div key={label} className="flex items-center justify-between py-0.5">
              <span className="text-xs text-slate-400">{label}</span>
              <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
            </div>
          ))}
        </div>

        {/* User */}
        <div className="flex items-center space-x-3 px-2">
          <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white"
            style={{ background: 'linear-gradient(135deg,#7c3aed,#2563eb)' }}>
            FU
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">FINCON User</p>
            <p className="text-[10px] text-slate-500 truncate">Pro Plan</p>
          </div>
          <Settings className="w-4 h-4 text-slate-600 hover:text-slate-300 cursor-pointer transition-colors flex-shrink-0" />
        </div>
      </div>
    </aside>
  );
}

function TopBar({ title, subtitle }) {
  return (
    <header className="px-8 py-4 flex items-center justify-between sticky top-0 z-20"
      style={{ background: 'rgba(9,13,31,0.85)', backdropFilter: 'blur(20px)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
      <div>
        <h1 className="text-lg font-bold text-white">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center space-x-3">
        <div className="relative">
          <Bell className="w-5 h-5 text-slate-500 hover:text-slate-300 cursor-pointer transition-colors" />
          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-blue-500" />
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl"
          style={{ background: 'rgba(30,41,59,0.6)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <span className="status-dot-green" style={{ width: 7, height: 7 }} />
          <span className="text-xs text-slate-300 font-medium">API Connected</span>
        </div>
      </div>
    </header>
  );
}

// Page title map
const PAGE_META = {
  '/':          { title: 'Dashboard',      subtitle: 'Your AI-powered financial command center' },
  '/analysis':  { title: 'Stock Analysis', subtitle: 'Run individual or full multi-agent stock analysis' },
  '/portfolio': { title: 'Portfolio',      subtitle: 'Analyze and optimize your investment portfolio' },
  '/agents':    { title: 'Agent Monitor',  subtitle: 'Real-time status and activity of all AI agents' },
  '/history':   { title: 'History',        subtitle: 'Browse past analysis sessions and recommendations' },
};

function Layout() {
  const { pathname } = useLocation();
  const meta = PAGE_META[pathname] || { title: 'FINCON', subtitle: '' };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#090d1f' }}>
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar title={meta.title} subtitle={meta.subtitle} />
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
