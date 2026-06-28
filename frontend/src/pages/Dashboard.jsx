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

function MarketCard({ index }) {
  return (
    <div className="glass rounded-2xl p-5 glass-hover flex flex-col" style={{ minWidth: 0 }}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">{index.name}</p>
          <p className="text-xl font-bold text-white mt-1">{index.value}</p>
        </div>
        <span className={`badge mt-1 ${index.up ? 'badge-green' : 'badge-red'}`}>
          {index.up ? <ArrowUpRight className="w-3 h-3 mr-0.5" /> : <ArrowDownRight className="w-3 h-3 mr-0.5" />}
          {index.change}
        </span>
      </div>
      <div className="h-12 -mx-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={index.data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={`grad-${index.name}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={index.up ? '#10b981' : '#ef4444'} stopOpacity={0.25} />
                <stop offset="95%" stopColor={index.up ? '#10b981' : '#ef4444'} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="v" stroke={index.up ? '#10b981' : '#ef4444'}
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
    <div className="glass rounded-2xl p-5 glass-hover">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">{label}</p>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${color}18`, border: `1px solid ${color}30` }}>
          <Icon className="w-4.5 h-4.5" style={{ color, width: 17, height: 17 }} />
        </div>
      </div>
      <p className="text-3xl font-black text-white">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{sub}</p>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
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

  return (
    <div className="p-4 sm:p-6 md:p-8 space-y-6 sm:space-y-8 animate-fade-up">

      {/* Hero Banner */}
      <div className="relative rounded-2xl overflow-hidden p-5 sm:p-7"
        style={{
          background: 'linear-gradient(135deg, rgba(37,99,235,0.15) 0%, rgba(124,58,237,0.12) 50%, rgba(16,185,129,0.08) 100%)',
          border: '1px solid rgba(59,130,246,0.2)'
        }}>
        {/* Background orbs */}
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-20 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, #3b82f6, transparent)' }} />
        <div className="absolute bottom-0 left-1/2 w-48 h-48 rounded-full opacity-10 blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, #8b5cf6, transparent)' }} />

        <div className="relative flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-[10px] sm:text-xs font-semibold text-blue-400 uppercase tracking-widest">AI-Powered Intelligence</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white mb-1">Welcome to FINCON AI</h2>
            <p className="text-slate-400 text-xs sm:text-sm max-w-lg leading-relaxed">
               Your multi-agent financial intelligence platform. Run News, Technical, Risk, Fundamental &amp; Portfolio agents individually or launch the full CIO crew for comprehensive analysis.
            </p>
            <div className="flex flex-wrap items-center gap-3 mt-5">
              <button onClick={() => navigate('/analysis')} className="btn-primary flex items-center space-x-2 py-2 sm:py-2.5">
                <Zap className="w-4 h-4" />
                <span>Start Analysis</span>
              </button>
              <button onClick={() => navigate('/agents')} className="btn-secondary flex items-center space-x-2 py-2 sm:py-2.5">
                <Bot className="w-4 h-4" />
                <span>View Agents</span>
              </button>
            </div>
          </div>
          <div className="hidden lg:flex items-center space-x-1 opacity-80 flex-shrink-0">
            {[
              { icon: Newspaper, c: '#3b82f6', label: 'News' },
              { icon: TrendingUp, c: '#8b5cf6', label: 'Tech' },
              { icon: ShieldAlert, c: '#f59e0b', label: 'Risk' },
              { icon: BookOpen, c: '#ec4899', label: 'Fundamental' },
              { icon: Briefcase, c: '#10b981', label: 'Portfolio' },
            ].map(({ icon: Icon, c, label }, i) => (
              <div key={label} className="flex flex-col items-center space-y-2 px-3">
                <div className="w-11 h-11 rounded-2xl flex items-center justify-center"
                   style={{ background: `${c}15`, border: `1px solid ${c}30` }}>
                  <Icon className="w-4.5 h-4.5" style={{ color: c, width: 17, height: 17 }} />
                </div>
                <span className="text-[10px] text-slate-500">{label}</span>
              </div>
            ))}
            <ChevronRight className="text-slate-600 mx-1" style={{ width: 16 }} />
            <div className="flex flex-col items-center space-y-2 px-4">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
                style={{ background: 'rgba(96,165,250,0.15)', border: '1px solid rgba(96,165,250,0.3)' }}>
                <Users className="w-5 h-5 text-blue-400" />
              </div>
              <span className="text-[10px] text-slate-500">CIO</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Analyses Today"   value={stats.analyses_today}   sub="Based on history logs"     icon={BarChart2}  color="#3b82f6" />
        <StatCard label="Active Agents"    value="6"    sub="All systems online"     icon={Bot}        color="#10b981" />
        <StatCard label="Avg Confidence"   value={`${stats.avg_confidence}%`}  sub="Across all sessions"   icon={Activity}   color="#8b5cf6" />
        <StatCard label="Total Sessions" value={stats.sessions_this_week}  sub="Stored in SQLite"    icon={Clock}      color="#f59e0b" />
      </div>

      {/* Market Indices */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-white">Market Overview</h3>
          <span className="text-xs text-slate-500">Live data · refreshes every 15s</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {MARKET_INDICES.map(idx => <MarketCard key={idx.name} index={idx} />)}
        </div>
      </section>

      {/* Recent Sessions + Agent Activity */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Recent Sessions */}
        <div className="xl:col-span-3 glass rounded-2xl overflow-hidden flex flex-col">
          <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <h3 className="text-sm font-bold text-white">Recent Sessions</h3>
            <button onClick={() => navigate('/history')} className="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1 transition-colors">
              <span>View all</span><ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="fincon-table w-full min-w-[600px] px-6">
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
                  <tr><td colSpan="5" className="text-center text-xs text-slate-500 py-4">No recent sessions found</td></tr>
                ) : recentSessions.map(s => (
                  <tr key={s.id} className="cursor-pointer" onClick={() => navigate('/history')}>
                    <td className="font-bold text-white pl-6">{s.ticker}</td>
                    <td className="text-slate-400">{s.company}</td>
                    <td>
                      <span className={s.rec === 'BUY' ? 'badge-green' : s.rec === 'SELL' ? 'badge-red' : 'badge-amber'}>
                        {s.rec}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 h-1.5 rounded-full bg-slate-800 max-w-[80px]">
                          <div className="h-full rounded-full"
                            style={{ width: `${s.score}%`, background: s.score > 80 ? '#10b981' : s.score > 60 ? '#f59e0b' : '#ef4444' }} />
                        </div>
                        <span className="text-xs text-slate-400">{s.score}%</span>
                      </div>
                    </td>
                    <td className="text-slate-500 text-xs pr-6">{s.date} {s.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Agent Activity */}
        <div className="xl:col-span-2 glass rounded-2xl overflow-hidden">
          <div className="px-6 py-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <h3 className="text-sm font-bold text-white">Agent Activity</h3>
          </div>
          <div className="px-6 py-4 space-y-4">
               <p className="text-xs text-slate-500 italic">No agent activity running currently.</p>
          </div>
        </div>
      </div>

    </div>
  );
}
