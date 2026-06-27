import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Newspaper, TrendingUp, ShieldAlert, Briefcase, Users,
  CheckCircle2, Clock, AlertCircle, Cpu, Activity,
  Zap, MessageSquare, BookOpen, RefreshCw
} from 'lucide-react';
import { GEMINI_MODEL } from '../config/gemini';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const AGENT_COLOR_MAP = {
  'News Agent': '#3b82f6',
  'Technical Agent': '#8b5cf6',
  'Risk Agent': '#f59e0b',
  'Fundamental Agent': '#ec4899',
  'Portfolio Agent': '#10b981',
  'Manager Agent': '#60a5fa',
};

const AGENTS = [
  {
    key: 'news',
    label: 'News Analyst',
    fullLabel: 'Senior Market News Analyst',
    description: 'Fetches financial headlines, analyzes sentiment, detects bullish/bearish market signals.',
    icon: Newspaper,
    color: '#3b82f6',
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
    color: '#8b5cf6',
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
    color: '#f59e0b',
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
    color: '#ec4899',
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
    color: '#10b981',
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
    color: '#60a5fa',
    capability: ['Multi-Agent Synthesis', 'Conflict Resolution', 'Final Recommendation'],
    model: GEMINI_MODEL,
    tools: ['Delegation to sub-agents'],
  },
];

function AgentStatusCard({ agent }) {
  const { icon: Icon, label, fullLabel, description, color, capability, model, tools } = agent;

  return (
    <div className="glass rounded-2xl overflow-hidden hover:border-opacity-40 transition-all duration-200 glass-hover"
      style={{ border: `1px solid ${color}20` }}>
      {/* Header */}
      <div className="px-5 py-4 flex items-start justify-between"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: `${color}06` }}>
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
            <Icon className="w-5 h-5" style={{ color }} />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <p className="text-sm font-bold text-white">{label}</p>
              <span className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{ background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{fullLabel}</p>
          </div>
        </div>
        <span className="badge-green">Online</span>
      </div>

      {/* Body */}
      <div className="px-5 py-4 space-y-4">
        <p className="text-xs text-slate-400 leading-relaxed">{description}</p>

        <div>
          <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-2">Capabilities</p>
          <div className="flex flex-wrap gap-1.5">
            {capability.map(c => (
              <span key={c} className="px-2 py-0.5 rounded-lg text-[10px] font-semibold"
                style={{ background: `${color}12`, color, border: `1px solid ${color}25` }}>
                {c}
              </span>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs">
          <div>
            <p className="text-slate-600 mb-0.5">Model</p>
            <p className="text-slate-300 font-mono font-semibold">{model}</p>
          </div>
          <div className="text-right">
            <p className="text-slate-600 mb-0.5">Tools</p>
            <p className="text-slate-300 font-mono">{tools[0]}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AgentMonitor() {
  const navigate = useNavigate();
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
    <div className="p-8 space-y-8 animate-fade-up">

      {/* System Status Banner */}
      <div className="glass rounded-2xl p-5 flex items-center justify-between"
        style={{ border: '1px solid rgba(16,185,129,0.2)', background: 'rgba(16,185,129,0.04)' }}>
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }}>
            <Cpu className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <p className="text-sm font-bold text-white">Multi-Agent System</p>
              <span className="status-dot-green" />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">6 agents active · Gemini 2.5 Flash · CrewAI · SQLite</p>
          </div>
        </div>
        <div className="flex items-center space-x-6 text-center">
          {[
            { label: 'Agents', value: '6', color: '#10b981' },
            { label: 'Sessions', value: String(sessionCount), color: '#3b82f6' },
            { label: 'Total Runs', value: String(totalRuns), color: '#8b5cf6' },
          ].map(s => (
            <div key={s.label}>
              <p className="text-lg font-black" style={{ color: s.color }}>{s.value}</p>
              <p className="text-[10px] text-slate-600 uppercase tracking-widest">{s.label}</p>
            </div>
          ))}
        </div>
        <button onClick={() => navigate('/analysis')} className="btn-primary flex items-center space-x-2">
          <Zap className="w-4 h-4" /><span>Launch Crew</span>
        </button>
      </div>

      {/* Agent Cards Grid */}
      <section>
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Agent Roster</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {AGENTS.map(a => <AgentStatusCard key={a.key} agent={a} />)}
        </div>
      </section>

      {/* Live Activity Log */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Agent Activity Log</h3>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500">{totalRuns} runs logged</span>
          </div>
        </div>
        <div className="glass rounded-2xl overflow-hidden">
          {loadingLogs ? (
            <div className="p-8 text-center">
              <RefreshCw className="w-6 h-6 text-slate-600 mx-auto mb-2 animate-spin" />
              <p className="text-xs text-slate-500">Loading agent logs…</p>
            </div>
          ) : agentRuns.length === 0 ? (
            <div className="p-8 text-center">
              <Activity className="w-8 h-8 text-slate-700 mx-auto mb-3" />
              <p className="text-sm text-slate-500">No agent runs yet</p>
              <p className="text-xs text-slate-600 mt-1">Run an analysis to see agent activity here</p>
            </div>
          ) : (
            <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
              {agentRuns.slice(0, 30).map((run, i) => {
                const agentColor = AGENT_COLOR_MAP[run.agent_name] || '#60a5fa';
                return (
                  <div key={run.id || i} className="flex items-start px-6 py-3.5 hover:bg-white/[0.02] transition-colors">
                    <div className="w-1.5 h-1.5 rounded-full mt-1.5 mr-3 flex-shrink-0"
                      style={{ background: agentColor, boxShadow: `0 0 6px ${agentColor}` }} />
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-bold mr-2" style={{ color: agentColor }}>{run.agent_name}</span>
                      <span className="text-xs text-slate-400">Analyzed </span>
                      <span className="text-xs text-slate-300 font-semibold">{run.input_data}</span>
                      {run.output_preview && (
                        <p className="text-[10px] text-slate-600 mt-1 truncate max-w-lg">{run.output_preview}</p>
                      )}
                    </div>
                    <div className="flex items-center space-x-2 ml-4 flex-shrink-0">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      <span className="text-[10px] text-slate-600">{run.time}</span>
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
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Agent Architecture</h3>
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-center space-x-4 flex-wrap gap-4">
            {[
              { icon: Newspaper,  label: 'News Analyst',       color: '#3b82f6' },
              { icon: TrendingUp, label: 'Tech Analyst',       color: '#8b5cf6' },
              { icon: ShieldAlert,label: 'Risk Officer',       color: '#f59e0b' },
              { icon: BookOpen,   label: 'Fundamental',        color: '#ec4899' },
              { icon: Briefcase,  label: 'Portfolio Mgr',      color: '#10b981' },
            ].map(({ icon: Icon, label, color }) => (
              <React.Fragment key={label}>
                <div className="flex flex-col items-center space-y-2">
                  <div className="w-14 h-14 rounded-2xl flex items-center justify-center"
                    style={{ background: `${color}12`, border: `1px solid ${color}30` }}>
                    <Icon className="w-6 h-6" style={{ color }} />
                  </div>
                  <span className="text-xs text-slate-500 text-center whitespace-nowrap">{label}</span>
                </div>
                <div className="flex flex-col items-center justify-center">
                  <div className="flex space-x-0.5">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="w-1 h-1 rounded-full bg-slate-700"
                        style={{ animationDelay: `${i * 200}ms` }} />
                    ))}
                  </div>
                  <div className="w-8 h-0.5 bg-gradient-to-r from-slate-700 to-slate-600 mt-1" />
                </div>
              </React.Fragment>
            ))}
            <div className="flex flex-col items-center space-y-2">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{ background: 'rgba(59,130,246,0.15)', border: '2px solid rgba(59,130,246,0.4)', boxShadow: '0 0 20px rgba(59,130,246,0.2)' }}>
                <Users className="w-7 h-7 text-blue-400" />
              </div>
              <span className="text-xs text-blue-400 font-semibold text-center">CIO</span>
            </div>
          </div>
          <p className="text-xs text-slate-600 text-center mt-6">Sequential process: all 5 sub-agents report to the CIO who generates the final recommendation</p>
        </div>
      </section>

    </div>
  );
}
