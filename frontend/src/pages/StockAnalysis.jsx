import React, { useState } from 'react';
import axios from 'axios';
import {
  Newspaper, TrendingUp, ShieldAlert, Briefcase,
  Users, Zap, AlertTriangle, CheckCircle2, Clock,
  BarChart3, Activity, ChevronDown, ChevronUp, BookOpen
} from 'lucide-react';
import Markdown from '../components/Markdown';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ─────────────────────────────────────────────────────────────────────────────
// Agent definitions
// ─────────────────────────────────────────────────────────────────────────────
const AGENTS = [
  {
    key: 'news',
    label: 'News Sentiment Agent',
    description: 'Fetches latest news headlines and analyzes market sentiment — bullish / bearish signals.',
    icon: Newspaper,
    color: '#3b82f6',
    endpoint: 'news',
    getBody: (ticker) => ({ ticker }),
  },
  {
    key: 'technical',
    label: 'Technical Analysis Agent',
    description: 'Multi-timeframe analysis with RSI, MACD, Bollinger Bands, risk signals and trade quality score.',
    icon: TrendingUp,
    color: '#8b5cf6',
    endpoint: 'technical',
    getBody: (ticker) => ({ ticker }),
  },
  {
    key: 'risk',
    label: 'Risk Assessment Agent',
    description: 'Risk attribution, scenario analysis, stress testing, and historical comparison.',
    icon: ShieldAlert,
    color: '#f59e0b',
    endpoint: 'risk',
    getBody: (ticker) => ({ ticker }),
  },
  {
    key: 'fundamental',
    label: 'Fundamental Analysis Agent',
    description: 'Evaluates growth, margins, financial health, valuation multiples, and competitive positioning.',
    icon: BookOpen,
    color: '#ec4899',
    endpoint: 'fundamental',
    getBody: (ticker) => ({ ticker }),
  },
  {
    key: 'portfolio',
    label: 'Portfolio Manager Agent',
    description: 'Reviews portfolio allocation, diversification quality and generates rebalancing suggestions.',
    icon: Briefcase,
    color: '#10b981',
    endpoint: 'portfolio',
    getBody: () => ({}),
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Agent Card Component
// ─────────────────────────────────────────────────────────────────────────────
function AgentCard({ agent, ticker, portfolioId, state, onRun }) {
  const { icon: Icon, label, description, color } = agent;
  const { loading, result, error } = state;
  const [expanded, setExpanded] = useState(false);

  const statusIcon = loading
    ? <div className="w-4 h-4 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: `${color}40`, borderTopColor: color }} />
    : result
      ? <CheckCircle2 className="w-4 h-4" style={{ color: '#10b981' }} />
      : error
        ? <AlertTriangle className="w-4 h-4 text-red-400" />
        : <Clock className="w-4 h-4 text-slate-600" />;

  return (
    <div className="rounded-2xl overflow-hidden transition-all duration-300"
      style={{
        background: 'rgba(15,23,42,0.7)',
        border: `1px solid ${result ? color + '40' : 'rgba(255,255,255,0.06)'}`,
        backdropFilter: 'blur(16px)',
        boxShadow: result ? `0 0 20px ${color}15` : 'none',
      }}>

      {/* Card Header */}
      <div className="px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: `${color}08` }}>
        <div className="flex items-center space-x-3 min-w-0">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
            <Icon className="w-5 h-5" style={{ color }} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white">{label}</p>
            <p className="text-xs text-slate-500 mt-0.5 truncate sm:max-w-xs md:max-w-none">{description}</p>
          </div>
        </div>
        <div className="flex items-center justify-between sm:justify-end space-x-3 mt-2 sm:mt-0">
          <div className="flex items-center space-x-2">
            {statusIcon}
            <span className="text-[10px] text-slate-500 sm:hidden">Status</span>
          </div>
          <button
            onClick={onRun}
            disabled={loading || (!ticker && agent.key !== 'portfolio')}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
            style={{
              background: `linear-gradient(135deg, ${color}cc, ${color}88)`,
              boxShadow: `0 4px 12px ${color}30`,
            }}
          >
            {loading
              ? <><div className="w-3 h-3 border border-white/30 border-t-white rounded-full animate-spin" /><span>Running…</span></>
              : <><Zap className="w-3 h-3" /><span>Run Agent</span></>
            }
          </button>
        </div>
      </div>

      {/* Result Area */}
      {(result || error) && (
        <div className="px-5 py-4">
          {error && (
            <div className="flex items-start space-x-2 text-red-400 text-xs p-3 rounded-xl"
              style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {result && (
            <>
              <div className={`text-slate-300 ${!expanded ? 'max-h-36 overflow-hidden' : ''}`}
                style={{ maskImage: !expanded ? 'linear-gradient(to bottom, black 60%, transparent 100%)' : 'none' }}>
                <Markdown content={result} />
              </div>
              <button onClick={() => setExpanded(e => !e)}
                className="mt-2.5 flex items-center space-x-1 text-xs font-semibold transition-colors"
                style={{ color }}>
                {expanded ? <><ChevronUp className="w-3.5 h-3.5" /><span>Show less</span></>
                           : <><ChevronDown className="w-3.5 h-3.5" /><span>Show full output</span></>}
              </button>
            </>
          )}
        </div>
      )}

      {/* Idle State */}
      {!result && !error && !loading && (
        <div className="px-5 py-5 text-center">
          <p className="text-xs text-slate-600 italic">No output yet. Press <strong className="text-slate-500">Run Agent</strong> to start.</p>
        </div>
      )}

      {/* Loading State */}
      {loading && !result && (
        <div className="px-5 py-5 flex items-center justify-center space-x-3">
          <div className="flex space-x-1">
            {[0, 1, 2].map(i => (
              <div key={i} className="w-1.5 h-1.5 rounded-full animate-bounce"
                style={{ background: color, animationDelay: `${i * 150}ms` }} />
            ))}
          </div>
          <span className="text-xs text-slate-500">Agent is reasoning…</span>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Full Crew Result Card
// ─────────────────────────────────────────────────────────────────────────────
function FullCrewCard({ state, onRun, ticker, companyName }) {
  const { loading, result, error } = state;
  const [expanded, setExpanded] = useState(false);

  const rec = result && ['BUY', 'HOLD', 'SELL'].find(r => result.toUpperCase().includes(r));
  const recColor = rec === 'BUY' ? '#10b981' : rec === 'SELL' ? '#ef4444' : '#f59e0b';

  return (
    <div className="rounded-2xl overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, rgba(37,99,235,0.08), rgba(124,58,237,0.06))',
        border: `1px solid ${result ? 'rgba(59,130,246,0.35)' : 'rgba(59,130,246,0.15)'}`,
        boxShadow: result ? '0 0 30px rgba(59,130,246,0.12)' : 'none',
      }}>

      <div className="px-6 py-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)' }}>
            <Users className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <p className="text-base font-bold text-white">Full Multi-Agent Crew</p>
            <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">News → Technical → Risk → Fundamental → Portfolio → CIO recommendation</p>
          </div>
        </div>
        <div className="flex items-center justify-between md:justify-end space-x-3 mt-2 md:mt-0">
          {rec && (
            <span className="px-4 py-1.5 rounded-full text-sm font-black"
              style={{ background: `${recColor}20`, color: recColor, border: `1px solid ${recColor}40` }}>
              {rec}
            </span>
          )}
          <button
            onClick={onRun}
            disabled={loading || !ticker}
            className="btn-primary flex items-center space-x-2 disabled:opacity-30 whitespace-nowrap"
          >
            {loading
              ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /><span>Running Full Crew…</span></>
              : <><Zap className="w-4 h-4" /><span>Run Full Analysis</span></>
            }
          </button>
        </div>
      </div>

      <div className="px-6 py-5">
        {!result && !error && !loading && (
          <p className="text-sm text-slate-600 italic text-center py-4">
            Enter a ticker above and run the full crew to get a comprehensive investment recommendation from all agents.
          </p>
        )}
        {loading && (
          <div className="flex flex-col items-center py-8 space-y-5">
            <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4">
              {[
                { icon: Newspaper,  color: '#3b82f6', d: '0ms'   },
                { icon: TrendingUp, color: '#8b5cf6', d: '150ms' },
                { icon: ShieldAlert,color: '#f59e0b', d: '300ms' },
                { icon: BookOpen,   color: '#ec4899', d: '450ms' },
                { icon: Briefcase,  color: '#10b981', d: '600ms' },
                { icon: Users,      color: '#60a5fa', d: '750ms' },
              ].map(({ icon: Icon, color, d }, i) => (
                <div key={i} className="flex flex-col items-center space-y-2">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center animate-pulse"
                    style={{ background: `${color}15`, border: `1px solid ${color}30`, animationDelay: d }}>
                    <Icon className="w-4.5 h-4.5 sm:w-5 sm:h-5" style={{ color }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="text-sm text-slate-400">All 6 agents are deliberating… this may take 60–120s</p>
            <div className="flex space-x-1.5">
              {[0,1,2,3,4].map(i => (
                <div key={i} className="w-2 h-2 rounded-full bg-blue-500 animate-bounce"
                  style={{ animationDelay: `${i*100}ms` }} />
              ))}
            </div>
          </div>
        )}
        {error && (
          <div className="flex items-start space-x-2 text-red-400 text-xs p-4 rounded-xl"
            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" /><span>{error}</span>
          </div>
        )}
        {result && (
          <>
            <div className={`text-slate-200 ${!expanded ? 'max-h-60 overflow-hidden' : ''}`}
              style={{ maskImage: !expanded ? 'linear-gradient(to bottom, black 50%, transparent 100%)' : 'none' }}>
              <Markdown content={result} />
            </div>
            <button onClick={() => setExpanded(e => !e)}
              className="mt-3 flex items-center space-x-1.5 text-sm font-semibold text-blue-400 hover:text-blue-300 transition-colors">
              {expanded ? <><ChevronUp className="w-4 h-4" /><span>Collapse</span></>
                        : <><ChevronDown className="w-4 h-4" /><span>Expand full recommendation</span></>}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Stock Analysis Page
// ─────────────────────────────────────────────────────────────────────────────
export default function StockAnalysis() {
  const [ticker, setTicker] = useState('');
  const [companyName, setCompanyName] = useState('');

  const initState = { loading: false, result: null, error: null };
  const [states, setStates] = useState({
    news: { ...initState }, technical: { ...initState },
    risk: { ...initState }, fundamental: { ...initState },
    portfolio: { ...initState }, full: { ...initState },
  });

  const set = (key, patch) => setStates(prev => ({ ...prev, [key]: { ...prev[key], ...patch } }));

  const runAgent = async (key, endpoint, body) => {
    set(key, { loading: true, result: null, error: null });
    try {
      const res = await axios.post(`${API}/api/analyze/${endpoint}`, body);
      set(key, { loading: false, result: res.data.result || res.data.recommendation || JSON.stringify(res.data, null, 2) });
    } catch (err) {
      set(key, { loading: false, error: err.response?.data?.detail || err.message });
    }
  };

  const runAll = () => {
    AGENTS.forEach(a => {
      const body = a.getBody(ticker);
      runAgent(a.key, a.endpoint, body);
    });
    setTimeout(() => {
      runAgent('full', 'stock', { company_name: companyName || ticker, ticker });
    }, 500);
  };

  return (
    <div className="p-4 sm:p-6 md:p-8 space-y-6 animate-fade-up">

      {/* Input Card */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center space-x-2 mb-5">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <h2 className="text-sm font-bold text-white">Configure Analysis</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-500 font-semibold uppercase tracking-widest block mb-2">Stock Ticker *</label>
            <input
              id="ticker-input"
              className="fincon-input"
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500 font-semibold uppercase tracking-widest block mb-2">Company Name</label>
            <input
              id="company-input"
              className="fincon-input"
              value={companyName}
              onChange={e => setCompanyName(e.target.value)}
              placeholder="Apple Inc."
            />
          </div>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-5 pt-5" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <p className="text-xs text-slate-600">Run agents individually or launch the full crew at once</p>
          <button
            onClick={runAll}
            disabled={!ticker || Object.values(states).some(s => s.loading)}
            className="btn-primary flex items-center justify-center space-x-2 w-full sm:w-auto"
          >
            <Activity className="w-4 h-4" />
            <span>Run All Agents</span>
          </button>
        </div>
      </div>

      {/* Individual Agents */}
      <div>
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Individual Agents</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {AGENTS.map(agent => (
            <AgentCard
              key={agent.key}
              agent={agent}
              ticker={ticker}
              portfolioId={null}
              state={states[agent.key]}
              onRun={() => runAgent(agent.key, agent.endpoint, agent.getBody(ticker))}
            />
          ))}
        </div>
      </div>

      {/* Full Crew */}
      <div>
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Full Multi-Agent Crew</h3>
        <FullCrewCard
          state={states.full}
          ticker={ticker}
          companyName={companyName}
          onRun={() => runAgent('full', 'stock', { company_name: companyName || ticker, ticker })}
        />
      </div>

    </div>
  );
}
