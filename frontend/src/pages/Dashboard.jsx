import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp, TrendingDown, Activity, Bot, Clock,
  ArrowUpRight, ArrowDownRight, Zap, BarChart2,
  Newspaper, ShieldAlert, Briefcase, Users, ChevronRight,
  Sparkles, BookOpen
} from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useTheme } from '../context/ThemeContext';

// Mock market data for sparklines
const sparkData = (base, vol) =>
  Array.from({ length: 20 }, (_, i) => ({
    x: i,
    v: base + (Math.random() - 0.48) * vol * (1 + i * 0.05),
  }));

const MARKET_INDICES = [
  { name: 'S&P 500',    value: '5,248.32', change: '+1.24%', up: true,  data: sparkData(5200, 80) },
  { name: 'NASDAQ',     value: '18,391.61',change: '+1.87%', up: true,  data: sparkData(18300, 200) },
  { name: 'DOW JONES',  value: '39,512.84',change: '-0.31%', up: false, data: sparkData(39500, 300) },
  { name: 'VIX',        value: '13.24',    change: '-5.42%', up: false, data: sparkData(13, 2) },
];

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';


// Custom tooltip for recharts
const SparkTooltip = () => null;

function MarketCard({ index, isDark }) {
  const upColor = 'var(--accent-emerald)';
  const downColor = 'var(--accent-rose)';
  const strokeColor = index.up ? '#10b981' : '#ef4444';

  return (
    <div
      className="card card-hover flex flex-col transition-all duration-300"
      style={{
        borderTop: `2px solid ${index.up ? 'var(--accent-emerald)' : 'var(--accent-rose)'}`,
        minWidth: 0,
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <p
            className="text-[11px] font-bold uppercase tracking-widest"
            style={{ color: 'var(--text-muted)' }}
          >
            {index.name}
          </p>
          <p
            className="text-xl font-bold mt-1"
            style={{ color: 'var(--text-primary)' }}
          >
            {index.value}
          </p>
        </div>
        <span className={`mt-1 ${index.up ? 'badge-green' : 'badge-red'}`}>
          {index.up ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : <ArrowDownRight className="w-3 h-3 mr-0.5" />}
          {index.change}
        </span>
      </div>
      <div className="h-12 -mx-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={index.data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={`grad-${index.name}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={strokeColor} stopOpacity={0.25} />
                <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="v" stroke={strokeColor}
              strokeWidth={1.5} fill={`url(#grad-${index.name})`} dot={false} />
            <Tooltip content={<SparkTooltip />} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, icon: Icon, color }) {
  return (
    <div
      className="card card-hover transition-all duration-300"
      style={{
        borderLeft: `3px solid ${color}`,
      }}
    >
      <div className="flex items-center justify-between mb-4">
        <p
          className="text-xs font-semibold uppercase tracking-widest"
          style={{ color: 'var(--text-muted)' }}
        >
          {label}
        </p>
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{
            background: `${color}14`,
            border: `1px solid ${color}30`,
          }}
        >
          <Icon style={{ color, width: 17, height: 17 }} />
        </div>
      </div>
      <p
        className="text-3xl font-black"
        style={{ color: 'var(--text-primary)' }}
      >
        {value}
      </p>
      <p
        className="text-xs mt-1"
        style={{ color: 'var(--text-muted)' }}
      >
        {sub}
      </p>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [tick, setTick] = useState(0);
  const [recentSessions, setRecentSessions] = useState([]);
  const [stats, setStats] = useState({
    analyses_today: 0,
    avg_confidence: 0,
    sessions_this_week: 0
  });

  useEffect(() => {
    const t = setInterval(() => setTick(x => x + 1), 3000);
    
    // Fetch dashboard data
    axios.get(`${API}/api/history/sessions`).then(res => {
      setRecentSessions((res.data.sessions || []).slice(0, 5));
    }).catch(err => console.error(err));

    axios.get(`${API}/api/history/stats`).then(res => {
      if (res.data.stats) {
        setStats(res.data.stats);
      }
    }).catch(err => console.error(err));

    return () => clearInterval(t);
  }, []);

  const agentIcons = [
    { icon: Newspaper, c: 'var(--accent-blue)', raw: '#4f8bff', label: 'News' },
    { icon: TrendingUp, c: 'var(--accent-purple)', raw: '#a78bfa', label: 'Tech' },
    { icon: ShieldAlert, c: 'var(--accent-amber)', raw: '#f59e0b', label: 'Risk' },
    { icon: BookOpen, c: 'var(--accent-rose)', raw: '#f472b6', label: 'Fundamental' },
    { icon: Briefcase, c: 'var(--accent-emerald)', raw: '#34d399', label: 'Portfolio' },
  ];

  return (
    <div className="p-4 sm:p-6 md:p-8 space-y-6 sm:space-y-8 animate-fade-up">

      {/* ── Hero Banner ──────────────────────────────────────────── */}
      <div
        className="relative rounded-2xl overflow-hidden p-6 sm:p-8"
        style={{
          background: isDark
            ? 'linear-gradient(135deg, rgba(79,139,255,0.12) 0%, rgba(167,139,250,0.10) 50%, rgba(52,211,153,0.06) 100%)'
            : 'linear-gradient(135deg, rgba(79,139,255,0.08) 0%, rgba(167,139,250,0.06) 50%, rgba(52,211,153,0.04) 100%)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Background orbs */}
        <div
          className="absolute top-0 right-0 w-72 h-72 rounded-full opacity-20 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, var(--accent-blue), transparent)' }}
        />
        <div
          className="absolute bottom-0 left-1/2 w-56 h-56 rounded-full opacity-10 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, var(--accent-purple), transparent)' }}
        />

        <div className="relative flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <Sparkles className="w-4 h-4" style={{ color: 'var(--accent-blue)' }} />
              <span
                className="text-[10px] sm:text-xs font-semibold uppercase tracking-widest"
                style={{ color: 'var(--accent-blue)' }}
              >
                AI-Powered Intelligence
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black mb-2 gradient-text">
              Welcome to FINCON AI
            </h2>
            <p
              className="text-xs sm:text-sm max-w-lg leading-relaxed"
              style={{ color: 'var(--text-tertiary)' }}
            >
               Your multi-agent financial intelligence platform. Run News, Technical, Risk, Fundamental &amp; Portfolio agents individually or launch the full CIO crew for comprehensive analysis.
            </p>
            <div className="flex flex-wrap items-center gap-3 mt-6">
              <button onClick={() => navigate('/analysis')} className="btn-primary flex items-center space-x-2 py-2.5 px-5">
                <Zap className="w-4 h-4" />
                <span>Start Analysis</span>
              </button>
              <button onClick={() => navigate('/agents')} className="btn-secondary flex items-center space-x-2 py-2.5 px-5">
                <Bot className="w-4 h-4" />
                <span>View Agents</span>
              </button>
            </div>
          </div>

          {/* Agent Pipeline Visualization – desktop only */}
          <div className="hidden lg:flex items-center space-x-1 opacity-90 flex-shrink-0">
            {agentIcons.map(({ icon: Icon, c, raw, label }) => (
              <div key={label} className="flex flex-col items-center space-y-2 px-3">
                <div
                  className="w-11 h-11 rounded-2xl flex items-center justify-center transition-transform duration-200 hover:scale-110"
                  style={{
                    background: `${raw}15`,
                    border: `1px solid ${raw}30`,
                  }}
                >
                  <Icon style={{ color: c, width: 17, height: 17 }} />
                </div>
                <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{label}</span>
              </div>
            ))}
            <ChevronRight style={{ color: 'var(--text-muted)', width: 16 }} className="mx-1" />
            <div className="flex flex-col items-center space-y-2 px-4">
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center transition-transform duration-200 hover:scale-110"
                style={{
                  background: 'rgba(79,139,255,0.12)',
                  border: '1px solid rgba(79,139,255,0.25)',
                }}
              >
                <Users className="w-5 h-5" style={{ color: 'var(--accent-blue)' }} />
              </div>
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>CIO</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Stats Row ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Analyses Today"   value={stats.analyses_today}   sub="Based on history logs"     icon={BarChart2}  color="var(--accent-blue)" />
        <StatCard label="Active Agents"    value="6"    sub="All systems online"     icon={Bot}        color="var(--accent-emerald)" />
        <StatCard label="Avg Confidence"   value={`${stats.avg_confidence}%`}  sub="Across all sessions"   icon={Activity}   color="var(--accent-purple)" />
        <StatCard label="Total Sessions" value={stats.sessions_this_week}  sub="Stored in SQLite"    icon={Clock}      color="var(--accent-amber)" />
      </div>

      {/* ── Market Indices ───────────────────────────────────────── */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
            Market Overview
          </h3>
          <div className="flex items-center space-x-2">
            <span className="status-dot status-dot-online" />
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
              Live data · refreshes every 15s
            </span>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {MARKET_INDICES.map(idx => <MarketCard key={idx.name} index={idx} isDark={isDark} />)}
        </div>
      </section>

      {/* ── Recent Sessions + Agent Activity ──────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">

        {/* Recent Sessions Table */}
        <div
          className="xl:col-span-3 card overflow-hidden flex flex-col"
          style={{ padding: 0 }}
        >
          <div
            className="px-6 py-4 flex items-center justify-between"
            style={{ borderBottom: '1px solid var(--border-subtle)' }}
          >
            <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
              Recent Sessions
            </h3>
            <button
              onClick={() => navigate('/history')}
              className="btn-ghost text-xs flex items-center space-x-1 py-1 px-2"
              style={{ color: 'var(--accent-blue)' }}
            >
              <span>View all</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="table-pro w-full min-w-[600px]">
              <thead>
                <tr>
                  <th className="pl-6">Ticker</th>
                  <th>Company</th>
                  <th>Recommendation</th>
                  <th>Confidence</th>
                  <th className="pr-6">Time</th>
                </tr>
              </thead>
              <tbody>
                {recentSessions.length === 0 ? (
                  <tr>
                    <td
                      colSpan="5"
                      className="text-center text-xs py-8"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      No recent sessions found. Start an analysis to see results here.
                    </td>
                  </tr>
                ) : recentSessions.map(s => (
                  <tr
                    key={s.id}
                    className="cursor-pointer transition-colors duration-150"
                    onClick={() => navigate('/history')}
                    style={{ '--hover-bg': 'var(--bg-elevated)' }}
                  >
                    <td className="pl-6 font-bold" style={{ color: 'var(--text-primary)' }}>
                      {s.ticker}
                    </td>
                    <td style={{ color: 'var(--text-tertiary)' }}>{s.company}</td>
                    <td>
                      <span className={
                        s.rec === 'BUY' ? 'badge-green' :
                        s.rec === 'SELL' ? 'badge-red' :
                        'badge-amber'
                      }>
                        {s.rec}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <div
                          className="flex-1 h-1.5 rounded-full max-w-[80px]"
                          style={{ background: 'var(--bg-input)' }}
                        >
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${s.score}%`,
                              background: s.score > 80
                                ? 'var(--accent-emerald)'
                                : s.score > 60
                                  ? 'var(--accent-amber)'
                                  : 'var(--accent-rose)',
                            }}
                          />
                        </div>
                        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          {s.score}%
                        </span>
                      </div>
                    </td>
                    <td className="text-xs pr-6" style={{ color: 'var(--text-muted)' }}>
                      {s.date} {s.time}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Agent Activity Sidebar */}
        <div
          className="xl:col-span-2 card overflow-hidden"
          style={{ padding: 0 }}
        >
          <div
            className="px-6 py-4"
            style={{ borderBottom: '1px solid var(--border-subtle)' }}
          >
            <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
              Agent Activity
            </h3>
          </div>
          <div className="px-6 py-6 space-y-4">
            {/* Agent status indicators */}
            {[
              { name: 'News Agent', icon: Newspaper, color: 'var(--accent-blue)', raw: '#4f8bff' },
              { name: 'Technical Agent', icon: TrendingUp, color: 'var(--accent-purple)', raw: '#a78bfa' },
              { name: 'Risk Agent', icon: ShieldAlert, color: 'var(--accent-amber)', raw: '#f59e0b' },
              { name: 'Fundamental Agent', icon: BookOpen, color: 'var(--accent-rose)', raw: '#f472b6' },
              { name: 'Portfolio Agent', icon: Briefcase, color: 'var(--accent-emerald)', raw: '#34d399' },
              { name: 'CIO Orchestrator', icon: Users, color: 'var(--accent-cyan)', raw: '#22d3ee' },
            ].map(({ name, icon: Icon, color, raw }) => (
              <div
                key={name}
                className="flex items-center justify-between py-2"
                style={{ borderBottom: '1px solid var(--border-subtle)' }}
              >
                <div className="flex items-center space-x-3">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{
                      background: `${raw}12`,
                      border: `1px solid ${raw}25`,
                    }}
                  >
                    <Icon style={{ color, width: 14, height: 14 }} />
                  </div>
                  <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                    {name}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="status-dot status-dot-online" />
                  <span className="text-[10px] font-medium" style={{ color: 'var(--accent-emerald)' }}>
                    Ready
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}
