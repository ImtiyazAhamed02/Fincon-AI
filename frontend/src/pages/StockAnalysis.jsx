import React, { useState } from 'react';
import axios from 'axios';
import {
  Newspaper, TrendingUp, ShieldAlert, Briefcase,
  Users, Zap, AlertTriangle, CheckCircle2, Clock,
  BarChart3, Activity, ChevronDown, ChevronUp, BookOpen
} from 'lucide-react';
import Markdown from '../components/Markdown';
import { useTheme } from '../context/ThemeContext';

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
      ? <CheckCircle2 className="w-4 h-4" style={{ color: 'var(--accent-emerald)' }} />
      : error
        ? <AlertTriangle className="w-4 h-4" style={{ color: 'var(--accent-rose)' }} />
        : <Clock className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />;

  const statusLabel = loading ? 'Running' : result ? 'Complete' : error ? 'Error' : 'Idle';

  return (
    <div
      className="card card-hover rounded-2xl overflow-hidden transition-all duration-300"
      style={{
        borderTop: `3px solid ${color}`,
        boxShadow: result ? `var(--shadow-card), 0 0 20px ${color}12` : 'var(--shadow-card)',
      }}
    >
      {/* Card Header */}
      <div
        className="px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        style={{ background: `${color}06` }}
      >
        <div className="flex items-center space-x-3 min-w-0">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: `${color}12`, border: `1px solid ${color}25` }}
          >
            <Icon className="w-5 h-5" style={{ color }} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{label}</p>
            <p className="text-xs mt-0.5 truncate sm:max-w-xs md:max-w-none" style={{ color: 'var(--text-tertiary)' }}>
              {description}
            </p>
          </div>
        </div>
        <div className="flex items-center justify-between sm:justify-end space-x-3 mt-2 sm:mt-0">
          <div className="flex items-center space-x-2">
            {statusIcon}
            <span className="text-[10px] font-medium sm:hidden" style={{ color: 'var(--text-tertiary)' }}>
              {statusLabel}
            </span>
          </div>
          <button
            onClick={onRun}
            disabled={loading || (!ticker && agent.key !== 'portfolio')}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
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

      <hr className="divider" />

      {/* Result Area */}
      {(result || error) && (
        <div className="px-5 py-4">
          {error && (
            <div
              className="flex items-start space-x-2 text-xs p-3 rounded-xl"
              style={{
                background: 'rgba(251, 113, 133, 0.08)',
                border: '1px solid rgba(251, 113, 133, 0.2)',
                color: 'var(--accent-rose)',
              }}
            >
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {result && (
            <>
              <div
                className={`${!expanded ? 'max-h-36 overflow-hidden' : ''}`}
                style={{
                  color: 'var(--text-secondary)',
                  maskImage: !expanded ? 'linear-gradient(to bottom, black 60%, transparent 100%)' : 'none',
                  WebkitMaskImage: !expanded ? 'linear-gradient(to bottom, black 60%, transparent 100%)' : 'none',
                }}
              >
                <Markdown content={result} />
              </div>
              <button
                onClick={() => setExpanded(e => !e)}
                className="mt-2.5 flex items-center space-x-1 text-xs font-semibold transition-colors cursor-pointer"
                style={{ color }}
              >
                {expanded
                  ? <><ChevronUp className="w-3.5 h-3.5" /><span>Show less</span></>
                  : <><ChevronDown className="w-3.5 h-3.5" /><span>Show full output</span></>
                }
              </button>
            </>
          )}
        </div>
      )}

      {/* Idle State */}
      {!result && !error && !loading && (
        <div className="px-5 py-5 text-center">
          <p className="text-xs italic" style={{ color: 'var(--text-muted)' }}>
            No output yet. Press <strong style={{ color: 'var(--text-tertiary)' }}>Run Agent</strong> to start.
          </p>
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
          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Agent is reasoning…</span>
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
  const recBadge = rec === 'BUY' ? 'badge-green' : rec === 'SELL' ? 'badge-red' : 'badge-amber';

  return (
    <div
      className="card rounded-2xl overflow-hidden transition-all duration-300"
      style={{
        background: 'var(--bg-card)',
        borderImage: result
          ? 'linear-gradient(135deg, rgba(79,139,255,0.5), rgba(124,58,237,0.4)) 1'
          : 'none',
        border: result ? undefined : '1px solid var(--border-subtle)',
        boxShadow: result ? 'var(--shadow-card-hover), var(--shadow-glow-blue)' : 'var(--shadow-card)',
      }}
    >
      {/* Gradient top accent */}
      <div
        className="h-1"
        style={{ background: 'var(--gradient-primary)' }}
      />

      <div
        className="px-6 py-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{ borderBottom: '1px solid var(--border-subtle)' }}
      >
        <div className="flex items-center space-x-4">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{
              background: 'rgba(79, 139, 255, 0.1)',
              border: '1px solid rgba(79, 139, 255, 0.2)',
            }}
          >
            <Users className="w-6 h-6" style={{ color: 'var(--accent-blue)' }} />
          </div>
          <div>
            <p className="text-base font-bold" style={{ color: 'var(--text-primary)' }}>Full Multi-Agent Crew</p>
            <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>
              News → Technical → Risk → Fundamental → Portfolio → CIO recommendation
            </p>
          </div>
        </div>
        <div className="flex items-center justify-between md:justify-end space-x-3 mt-2 md:mt-0">
          {rec && (
            <span className={`badge ${recBadge} text-sm font-black px-4 py-1.5`}>
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
          <p className="text-sm italic text-center py-4" style={{ color: 'var(--text-muted)' }}>
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
              ].map(({ icon: AgIcon, color: c, d }, i) => (
                <div key={i} className="flex flex-col items-center space-y-2">
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center animate-pulse"
                    style={{ background: `${c}12`, border: `1px solid ${c}25`, animationDelay: d }}>
                    <AgIcon className="w-4.5 h-4.5 sm:w-5 sm:h-5" style={{ color: c }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              All 6 agents are deliberating… this may take 60–120s
            </p>
            <div className="flex space-x-1.5">
              {[0,1,2,3,4].map(i => (
                <div key={i} className="w-2 h-2 rounded-full animate-bounce"
                  style={{ background: 'var(--accent-blue)', animationDelay: `${i*100}ms` }} />
              ))}
            </div>
          </div>
        )}
        {error && (
          <div
            className="flex items-start space-x-2 text-xs p-4 rounded-xl"
            style={{
              background: 'rgba(251, 113, 133, 0.08)',
              border: '1px solid rgba(251, 113, 133, 0.2)',
              color: 'var(--accent-rose)',
            }}
          >
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" /><span>{error}</span>
          </div>
        )}
        {result && (
          <>
            <div
              className={`${!expanded ? 'max-h-60 overflow-hidden' : ''}`}
              style={{
                color: 'var(--text-secondary)',
                maskImage: !expanded ? 'linear-gradient(to bottom, black 50%, transparent 100%)' : 'none',
                WebkitMaskImage: !expanded ? 'linear-gradient(to bottom, black 50%, transparent 100%)' : 'none',
              }}
            >
              <Markdown content={result} />
            </div>
            <button
              onClick={() => setExpanded(e => !e)}
              className="mt-3 flex items-center space-x-1.5 text-sm font-semibold transition-colors cursor-pointer"
              style={{ color: 'var(--accent-blue)' }}
            >
              {expanded
                ? <><ChevronUp className="w-4 h-4" /><span>Collapse</span></>
                : <><ChevronDown className="w-4 h-4" /><span>Expand full recommendation</span></>
              }
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
  const { isDark } = useTheme();
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
    <div className="p-4 sm:p-6 md:p-8 space-y-8 animate-fade-up">

      {/* ── Page Header ─────────────────────────────────────────────────────── */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
          Stock <span className="gradient-text">Analysis</span>
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-tertiary)' }}>
          Run AI-powered agents individually or as a coordinated crew for comprehensive insights.
        </p>
      </div>

      {/* ── Configure Analysis Card ─────────────────────────────────────────── */}
      <div className="card p-6">
        <div className="flex items-center space-x-2.5 mb-5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'rgba(79, 139, 255, 0.1)' }}
          >
            <BarChart3 className="w-4 h-4" style={{ color: 'var(--accent-blue)' }} />
          </div>
          <h2 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>Configure Analysis</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="label" htmlFor="ticker-input">Stock Ticker *</label>
            <input
              id="ticker-input"
              className="input-field"
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
          </div>
          <div>
            <label className="label" htmlFor="company-input">Company Name</label>
            <input
              id="company-input"
              className="input-field"
              value={companyName}
              onChange={e => setCompanyName(e.target.value)}
              placeholder="Apple Inc."
            />
          </div>
        </div>

        <hr className="divider mt-5" />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-5">
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Run agents individually or launch the full crew at once
          </p>
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

      {/* ── Individual Agents ───────────────────────────────────────────────── */}
      <div>
        <h3 className="label mb-4">Individual Agents</h3>
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

      {/* ── Full Crew ───────────────────────────────────────────────────────── */}
      <div>
        <h3 className="label mb-4">Full Multi-Agent Crew</h3>
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
