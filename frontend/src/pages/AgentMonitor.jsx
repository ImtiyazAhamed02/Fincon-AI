import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Newspaper, TrendingUp, ShieldAlert, Briefcase, Users,
  CheckCircle2, Clock, AlertCircle, Cpu, Activity,
  Zap, MessageSquare, BookOpen, RefreshCw
} from 'lucide-react';
import { GEMINI_MODEL } from '../config/gemini';
import { useTheme } from '../context/ThemeContext';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const AGENT_COLOR_MAP = {
  'News Agent': 'var(--accent-blue)',
  'Technical Agent': 'var(--accent-purple)',
  'Risk Agent': 'var(--accent-amber)',
  'Fundamental Agent': 'var(--accent-rose)',
  'Portfolio Agent': 'var(--accent-emerald)',
  'Manager Agent': 'var(--accent-blue)',
};

const AGENTS = [
  {
    key: 'news',
    label: 'News Analyst',
    fullLabel: 'Senior Market News Analyst',
    description: 'Fetches financial headlines, analyzes sentiment, detects bullish/bearish market signals.',
    icon: Newspaper,
    color: 'var(--accent-blue)',
    rawColor: '#3b82f6',
    capability: ['Sentiment Analysis', 'News Aggregation', 'Signal Detection'],
    model: GEMINI_MODEL,
    tools: ['get_stock_news'],
  },
  {
    key: 'technical',
    label: 'Technical Analyst',
    fullLabel: 'Expert Technical Analysis Validator',
    description: 'Multi-timeframe analysis with RSI, MACD, Bollinger Bands, signal conflict detection, and trend scoring.',
    icon: TrendingUp,
    color: 'var(--accent-purple)',
    rawColor: '#8b5cf6',
    capability: ['RSI / MACD', 'Bollinger Bands', 'Signal Conflicts'],
    model: GEMINI_MODEL,
    tools: ['get_stock_technical_data'],
  },
  {
    key: 'risk',
    label: 'Risk Officer',
    fullLabel: 'Financial Risk Assessment Agent',
    description: 'Risk attribution, scenario analysis, stress testing, compliant VaR interpretation, and historical comparison.',
    icon: ShieldAlert,
    color: 'var(--accent-amber)',
    rawColor: '#f59e0b',
    capability: ['VaR / CVaR', 'Stress Testing', 'Scenario Analysis'],
    model: GEMINI_MODEL,
    tools: ['get_risk_metrics'],
  },
  {
    key: 'fundamental',
    label: 'Fundamental Analyst',
    fullLabel: 'Lead Fundamental Analyst',
    description: 'Evaluates growth metrics, margins, financial health, valuation multiples, and competitive positioning.',
    icon: BookOpen,
    color: 'var(--accent-rose)',
    rawColor: '#ec4899',
    capability: ['Valuation Multiples', 'Growth Metrics', 'Financial Health'],
    model: GEMINI_MODEL,
    tools: ['get_stock_fundamental_data'],
  },
  {
    key: 'portfolio',
    label: 'Portfolio Manager',
    fullLabel: 'Portfolio Manager',
    description: 'Reviews portfolio allocation, assesses diversification quality, issues rebalancing recommendations.',
    icon: Briefcase,
    color: 'var(--accent-emerald)',
    rawColor: '#10b981',
    capability: ['Allocation Review', 'Diversification Analysis', 'Rebalancing'],
    model: GEMINI_MODEL,
    tools: ['get_portfolio_data'],
  },
  {
    key: 'cio',
    label: 'CIO',
    fullLabel: 'Chief Investment Officer',
    description: 'Aggregates all agent outputs, resolves conflicts, and generates the final explainable recommendation.',
    icon: Users,
    color: 'var(--accent-blue)',
    rawColor: '#3b82f6',
    capability: ['Multi-Agent Synthesis', 'Conflict Resolution', 'Final Recommendation'],
    model: GEMINI_MODEL,
    tools: ['Delegation to sub-agents'],
  },
];

function AgentStatusCard({ agent }) {
  const { icon: Icon, label, fullLabel, description, color, rawColor, capability, model, tools } = agent;

  return (
    <div
      className="card card-hover overflow-hidden transition-all duration-200"
      style={{
        borderTop: `3px solid ${color}`,
      }}
    >
      {/* Header */}
      <div
        className="px-5 py-4 flex items-start justify-between"
        style={{
          borderBottom: '1px solid var(--border-subtle)',
          background: `${rawColor}06`,
        }}
      >
        <div className="flex items-center space-x-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              background: `${rawColor}12`,
              border: `1px solid ${rawColor}25`,
            }}
          >
            <Icon className="w-5 h-5" style={{ color }} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>{label}</p>
              <span className="status-dot status-dot-online" style={{ width: 6, height: 6 }} />
            </div>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{fullLabel}</p>
          </div>
        </div>
        <span className="badge-green">Online</span>
      </div>

      {/* Body */}
      <div className="px-5 py-4 space-y-4">
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{description}</p>

        <div>
          <p className="label text-[10px] mb-2">Capabilities</p>
          <div className="flex flex-wrap gap-1.5">
            {capability.map(c => (
              <span
                key={c}
                className="px-2 py-0.5 rounded-lg text-[10px] font-semibold"
                style={{
                  background: `${rawColor}12`,
                  color,
                  border: `1px solid ${rawColor}25`,
                }}
              >
                {c}
              </span>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs pt-2" style={{ borderTop: '1px solid var(--border-subtle)' }}>
          <div>
            <p className="mb-0.5" style={{ color: 'var(--text-muted)' }}>Model</p>
            <p className="font-mono font-semibold" style={{ color: 'var(--text-secondary)' }}>{model}</p>
          </div>
          <div className="text-right">
            <p className="mb-0.5" style={{ color: 'var(--text-muted)' }}>Tools</p>
            <p className="font-mono" style={{ color: 'var(--text-secondary)' }}>{tools[0]}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AgentMonitor() {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [agentRuns, setAgentRuns] = useState([]);
  const [totalRuns, setTotalRuns] = useState(0);
  const [sessionCount, setSessionCount] = useState(0);
  const [loadingLogs, setLoadingLogs] = useState(true);

  useEffect(() => {
    // Fetch real agent run logs from SQLite
    axios.get(`${API}/api/history/agent-runs`)
      .then(res => {
        setAgentRuns(res.data.runs || []);
        setTotalRuns(res.data.total_runs || 0);
        // Count unique sessions
        const uniqueSessions = new Set((res.data.runs || []).map(r => r.session_id));
        setSessionCount(uniqueSessions.size);
        setLoadingLogs(false);
      })
      .catch(err => {
        console.error("Failed to load agent runs", err);
        setLoadingLogs(false);
      });
  }, []);

  return (
    <div className="p-4 sm:p-6 md:p-8 space-y-6 sm:space-y-8 animate-fade-up">

      {/* System Status Banner */}
      <div
        className="card p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{
          border: '1px solid rgba(16, 185, 129, 0.2)',
          background: 'rgba(16, 185, 129, 0.04)',
        }}
      >
        <div className="flex items-center space-x-4">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
            }}
          >
            <Cpu className="w-5 h-5" style={{ color: 'var(--accent-emerald)' }} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>Multi-Agent System</p>
              <span className="status-dot status-dot-online" />
            </div>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
              6 agents active · Gemini 2.5 Flash · CrewAI · SQLite
            </p>
          </div>
        </div>
        <div className="flex items-center justify-between sm:justify-start w-full md:w-auto sm:space-x-8 text-center px-2">
          {[
            { label: 'Agents', value: '6', color: 'var(--accent-emerald)' },
            { label: 'Sessions', value: String(sessionCount), color: 'var(--accent-blue)' },
            { label: 'Total Runs', value: String(totalRuns), color: 'var(--accent-purple)' },
          ].map(s => (
            <div key={s.label} className="flex-1 sm:flex-initial">
              <p className="text-lg font-black" style={{ color: s.color }}>{s.value}</p>
              <p className="text-[10px] uppercase tracking-widest font-semibold" style={{ color: 'var(--text-muted)' }}>{s.label}</p>
            </div>
          ))}
        </div>
        <button onClick={() => navigate('/analysis')} className="btn-primary flex items-center justify-center space-x-2 w-full md:w-auto">
          <Zap className="w-4 h-4" /><span>Launch Crew</span>
        </button>
      </div>

      {/* Agent Cards Grid */}
      <section>
        <h3 className="label mb-4">Agent Roster</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {AGENTS.map(a => <AgentStatusCard key={a.key} agent={a} />)}
        </div>
      </section>

      {/* Live Activity Log */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="label">Agent Activity Log</h3>
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{totalRuns} runs logged</span>
        </div>
        <div className="card overflow-hidden">
          {loadingLogs ? (
            <div className="p-8 text-center">
              <RefreshCw className="w-6 h-6 mx-auto mb-2 animate-spin" style={{ color: 'var(--text-muted)' }} />
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Loading agent logs…</p>
            </div>
          ) : agentRuns.length === 0 ? (
            <div className="p-8 text-center">
              <Activity className="w-8 h-8 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>No agent runs yet</p>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Run an analysis to see agent activity here</p>
            </div>
          ) : (
            <div className="divide-y" style={{ borderColor: 'var(--border-subtle)' }}>
              {agentRuns.slice(0, 30).map((run, i) => {
                const agentColor = AGENT_COLOR_MAP[run.agent_name] || 'var(--accent-blue)';
                return (
                  <div key={run.id || i} className="flex items-start px-6 py-3.5 hover:bg-white/[0.02] transition-colors">
                    <div
                      className="w-1.5 h-1.5 rounded-full mt-1.5 mr-3 flex-shrink-0 animate-pulse"
                      style={{
                        background: agentColor,
                        boxShadow: `0 0 6px ${agentColor}`,
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-bold mr-2" style={{ color: agentColor }}>{run.agent_name}</span>
                      <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Analyzed </span>
                      <span className="text-xs font-semibold" style={{ color: 'var(--text-secondary)' }}>{run.input_data}</span>
                      {run.output_preview && (
                        <p className="text-[10px] mt-1 truncate max-w-lg" style={{ color: 'var(--text-muted)' }}>{run.output_preview}</p>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 ml-4 flex-shrink-0">
                      <CheckCircle2 className="w-3.5 h-3.5" style={{ color: 'var(--accent-emerald)' }} />
                      <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{run.time}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* Architecture Diagram */}
      <section>
        <h3 className="label mb-4">Agent Architecture</h3>
        <div className="card p-6">
          <div className="flex items-center justify-center space-x-4 flex-wrap gap-y-6">
            {[
              { icon: Newspaper,  label: 'News Analyst',       color: 'var(--accent-blue)', raw: '#3b82f6' },
              { icon: TrendingUp, label: 'Tech Analyst',       color: 'var(--accent-purple)', raw: '#8b5cf6' },
              { icon: ShieldAlert,label: 'Risk Officer',       color: 'var(--accent-amber)', raw: '#f59e0b' },
              { icon: BookOpen,   label: 'Fundamental',        color: 'var(--accent-rose)', raw: '#ec4899' },
              { icon: Briefcase,  label: 'Portfolio Mgr',      color: 'var(--accent-emerald)', raw: '#10b981' },
            ].map(({ icon: Icon, label, color, raw }) => (
              <React.Fragment key={label}>
                <div className="flex flex-col items-center space-y-2">
                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-200 hover:scale-105"
                    style={{
                      background: `${raw}12`,
                      border: `1px solid ${raw}30`,
                    }}
                  >
                    <Icon className="w-6 h-6" style={{ color }} />
                  </div>
                  <span className="text-xs text-center whitespace-nowrap" style={{ color: 'var(--text-secondary)' }}>{label}</span>
                </div>
                <div className="hidden md:flex flex-col items-center justify-center opacity-40">
                  <div className="flex space-x-0.5">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="w-1 h-1 rounded-full"
                        style={{
                          background: 'var(--text-tertiary)',
                          animation: 'pulse-glow 1.5s infinite',
                          animationDelay: `${i * 200}ms`,
                        }}
                      />
                    ))}
                  </div>
                  <div className="w-8 h-0.5 mt-1" style={{ background: 'var(--border-default)' }} />
                </div>
              </React.Fragment>
            ))}
            <div className="flex flex-col items-center space-y-2">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-200 hover:scale-105"
                style={{
                  background: 'rgba(79, 139, 255, 0.12)',
                  border: '2px solid var(--accent-blue)',
                  boxShadow: 'var(--shadow-glow-blue)',
                }}
              >
                <Users className="w-7 h-7" style={{ color: 'var(--accent-blue)' }} />
              </div>
              <span className="text-xs font-semibold text-center" style={{ color: 'var(--accent-blue)' }}>CIO</span>
            </div>
          </div>
          <p className="text-xs text-center mt-6" style={{ color: 'var(--text-muted)' }}>
            Sequential process: all 5 sub-agents report to the CIO who generates the final recommendation
          </p>
        </div>
      </section>

    </div>
  );
}
