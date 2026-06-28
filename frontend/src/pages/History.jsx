import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Clock, Search, Filter, TrendingUp, TrendingDown,
  Minus, ChevronRight, Calendar, Bot, BarChart2,
  Download, RefreshCw, Eye, X
} from 'lucide-react';
import Markdown from '../components/Markdown';
import { useTheme } from '../context/ThemeContext';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const REC_CONFIG = {
  BUY:  { badge: 'badge-green',  icon: TrendingUp,   label: 'BUY'  },
  HOLD: { badge: 'badge-amber',  icon: Minus,        label: 'HOLD' },
  SELL: { badge: 'badge-red',    icon: TrendingDown, label: 'SELL' },
};

const FILTER_COLORS = {
  ALL:  { bg: 'rgba(79, 139, 255, 0.12)', border: 'rgba(79, 139, 255, 0.35)', text: 'var(--accent-blue)' },
  BUY:  { bg: 'rgba(52, 211, 153, 0.12)', border: 'rgba(52, 211, 153, 0.35)', text: 'var(--accent-emerald)' },
  HOLD: { bg: 'rgba(251, 191, 36, 0.12)', border: 'rgba(251, 191, 36, 0.35)', text: 'var(--accent-amber)' },
  SELL: { bg: 'rgba(251, 113, 133, 0.12)', border: 'rgba(251, 113, 133, 0.35)', text: 'var(--accent-rose)' },
};

export default function History() {
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('ALL');
  const [selected, setSelected] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/api/history/sessions`)
      .then(res => {
        setSessions(res.data.sessions || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load history", err);
        setLoading(false);
      });
  }, []);

  const filtered = sessions.filter(s =>
    (filter === 'ALL' || s.rec === filter) &&
    (s.ticker.toLowerCase().includes(search.toLowerCase()) ||
     s.company.toLowerCase().includes(search.toLowerCase()))
  );

  const statCards = [
    { label: 'Total Sessions', value: sessions.length, accent: 'var(--accent-blue)', bg: 'rgba(79, 139, 255, 0.08)' },
    { label: 'BUY Signals',   value: sessions.filter(s => s.rec === 'BUY').length,  accent: 'var(--accent-emerald)', bg: 'rgba(52, 211, 153, 0.08)' },
    { label: 'HOLD Signals',  value: sessions.filter(s => s.rec === 'HOLD').length, accent: 'var(--accent-amber)', bg: 'rgba(251, 191, 36, 0.08)' },
    { label: 'SELL Signals',  value: sessions.filter(s => s.rec === 'SELL').length, accent: 'var(--accent-rose)', bg: 'rgba(251, 113, 133, 0.08)' },
  ];

  return (
    <div className="p-4 sm:p-6 md:p-8 space-y-6 animate-fade-up">

      {/* ── Filter Bar ── */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center flex-1 min-w-[260px] max-w-sm">
          <div className="relative flex-1">
            <Search
              className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
              style={{ color: 'var(--text-muted)' }}
            />
            <input
              className="input-field w-full pl-10"
              placeholder="Search ticker or company…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto pb-1 max-w-full">
          {['ALL', 'BUY', 'HOLD', 'SELL'].map(f => {
            const active = filter === f;
            const colors = FILTER_COLORS[f];
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className="btn-ghost px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap"
                style={active
                  ? { background: colors.bg, border: `1px solid ${colors.border}`, color: colors.text }
                  : { border: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }
                }
              >
                {f}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Stats Row ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map(s => (
          <div
            key={s.label}
            className="card rounded-2xl p-4 flex items-center space-x-3 transition-all duration-200"
            style={{ borderLeft: `3px solid ${s.accent}` }}
          >
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: s.bg }}
            >
              <BarChart2 className="w-4 h-4" style={{ color: s.accent }} />
            </div>
            <div>
              <p className="text-2xl font-black" style={{ color: s.accent }}>{s.value}</p>
              <p className="text-[11px] font-medium" style={{ color: 'var(--text-muted)' }}>{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Main Layout ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Sessions List */}
        <div className="xl:col-span-2 space-y-3">
          {loading && (
            <div className="card rounded-2xl p-12 text-center">
              <RefreshCw className="w-10 h-10 mx-auto mb-3 animate-spin" style={{ color: 'var(--text-muted)' }} />
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Loading history…</p>
            </div>
          )}

          {!loading && filtered.length === 0 && (
            <div className="card rounded-2xl p-12 text-center">
              <Clock className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No sessions found</p>
            </div>
          )}

          {!loading && filtered.map(s => {
            const cfg = REC_CONFIG[s.rec];
            const RecIcon = cfg.icon;
            const isSelected = selected?.id === s.id;
            return (
              <div
                key={s.id}
                onClick={() => setSelected(isSelected ? null : s)}
                className="card-interactive rounded-2xl p-5 cursor-pointer transition-all duration-200"
                style={{
                  border: isSelected
                    ? '1px solid var(--accent-blue)'
                    : '1px solid var(--border-subtle)',
                  background: isSelected ? 'rgba(79, 139, 255, 0.06)' : undefined,
                  boxShadow: isSelected ? '0 0 20px rgba(79, 139, 255, 0.08)' : undefined,
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    {/* Ticker avatar */}
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-black text-xs"
                      style={{
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        color: 'var(--text-primary)',
                      }}
                    >
                      {s.ticker.slice(0, 2)}
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center space-x-2 flex-wrap">
                        <span className="badge-blue text-xs font-bold">{s.ticker}</span>
                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{s.company}</span>
                      </div>
                      <p
                        className="text-xs mt-1.5 leading-relaxed max-w-lg line-clamp-2"
                        style={{ color: 'var(--text-tertiary)' }}
                      >
                        {s.summary}
                      </p>
                      <div className="flex items-center space-x-3 mt-2 flex-wrap">
                        <span className="flex items-center space-x-1 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                          <Calendar className="w-3 h-3" />
                          <span>{s.date} · {s.time}</span>
                        </span>
                        <span className="flex items-center space-x-1 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                          <Bot className="w-3 h-3" />
                          <span>{s.agents.length} agents</span>
                        </span>
                        <span className="flex items-center space-x-1 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                          <Clock className="w-3 h-3" />
                          <span>{s.duration}</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right side: badge + confidence + re-run */}
                  <div className="flex flex-col items-end space-y-2 flex-shrink-0 ml-3">
                    <span className={cfg.badge + ' flex items-center space-x-1'}>
                      <RecIcon className="w-3 h-3" /><span>{cfg.label}</span>
                    </span>
                    {/* Confidence bar */}
                    <div className="flex items-center space-x-1.5">
                      <div
                        className="w-16 h-1.5 rounded-full overflow-hidden"
                        style={{ background: 'var(--bg-elevated)' }}
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
                      <span className="text-[10px] font-semibold" style={{ color: 'var(--text-muted)' }}>
                        {s.score}%
                      </span>
                    </div>
                    <button
                      onClick={e => { e.stopPropagation(); navigate('/analysis'); }}
                      className="flex items-center space-x-1 text-[10px] font-medium transition-colors"
                      style={{ color: 'var(--accent-blue)' }}
                    >
                      <RefreshCw className="w-3 h-3" /><span>Re-run</span>
                    </button>
                  </div>
                </div>

                {/* Agents row */}
                <div
                  className="flex items-center space-x-2 mt-3 pt-3 flex-wrap gap-y-1"
                  style={{ borderTop: '1px solid var(--border-subtle)' }}
                >
                  <span
                    className="text-[10px] uppercase tracking-widest font-semibold"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Agents:
                  </span>
                  {s.agents.map(a => (
                    <span
                      key={a}
                      className="px-2 py-0.5 rounded-lg text-[10px] font-semibold"
                      style={{
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        color: 'var(--text-tertiary)',
                      }}
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* ── Mobile Backdrop Overlay ── */}
        {selected && (
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 xl:hidden"
            onClick={() => setSelected(null)}
          />
        )}

        {/* ── Detail Panel (Slide Drawer on mobile, Sticky on desktop) ── */}
        <div className={`
          fixed inset-y-0 right-0 z-50 w-full max-w-lg shadow-2xl p-0
          transform transition-transform duration-300 ease-in-out flex flex-col h-screen
          xl:relative xl:transform-none xl:transition-none xl:z-0 xl:w-auto xl:max-w-none xl:shadow-none xl:h-auto xl:col-span-1
          ${selected ? 'translate-x-0' : 'translate-x-full xl:translate-x-0'}
        `}
          style={{ background: isDark ? '#090d1f' : 'var(--bg-card)' }}
        >
          <div
            className="card rounded-none xl:rounded-2xl overflow-hidden flex flex-col h-full xl:h-auto xl:sticky xl:top-4"
          >
            {/* Panel header */}
            <div
              className="px-5 py-4 flex items-center justify-between"
              style={{ borderBottom: '1px solid var(--border-subtle)' }}
            >
              <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                Session Detail
              </h3>
              <button
                onClick={() => setSelected(null)}
                className="xl:hidden p-1.5 rounded-lg transition-colors"
                style={{ color: 'var(--text-muted)' }}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {selected ? (
              <div className="p-5 space-y-5 overflow-y-auto flex-1 xl:overflow-visible">
                {/* Ticker heading */}
                <div>
                  <p className="label text-[10px] mb-1">Ticker</p>
                  <p className="text-lg font-black" style={{ color: 'var(--text-primary)' }}>
                    {selected.ticker}
                    <span className="text-xs font-normal ml-2" style={{ color: 'var(--text-muted)' }}>
                      {selected.company}
                    </span>
                  </p>
                </div>

                {/* Metric cards */}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    {
                      label: 'Recommendation',
                      value: selected.rec,
                      accent: selected.rec === 'BUY'
                        ? 'var(--accent-emerald)'
                        : selected.rec === 'SELL'
                          ? 'var(--accent-rose)'
                          : 'var(--accent-amber)',
                    },
                    {
                      label: 'Confidence',
                      value: `${selected.score}%`,
                      accent: selected.score > 80 ? 'var(--accent-emerald)' : 'var(--accent-amber)',
                    },
                    {
                      label: 'Duration',
                      value: selected.duration,
                      accent: 'var(--accent-blue)',
                    },
                    {
                      label: 'Agents Used',
                      value: selected.agents.length,
                      accent: 'var(--accent-purple)',
                    },
                  ].map(item => (
                    <div
                      key={item.label}
                      className="rounded-xl p-3 transition-all duration-200"
                      style={{
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderLeft: `3px solid ${item.accent}`,
                      }}
                    >
                      <p className="text-[10px] font-medium mb-1" style={{ color: 'var(--text-muted)' }}>
                        {item.label}
                      </p>
                      <p className="text-base font-black" style={{ color: item.accent }}>
                        {item.value}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Summary */}
                <div>
                  <p className="label text-[10px] mb-2">Summary</p>
                  <div
                    className="rounded-xl p-4"
                    style={{
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <Markdown content={selected.summary} />
                  </div>
                </div>

                {/* Agents involved */}
                <div>
                  <p className="label text-[10px] mb-2">Agents Involved</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selected.agents.map(a => (
                      <span key={a} className="badge-blue text-[10px]">{a}</span>
                    ))}
                  </div>
                </div>

                {/* Re-run button */}
                <button
                  onClick={() => navigate('/analysis')}
                  className="btn-primary w-full flex items-center justify-center space-x-2"
                >
                  <RefreshCw className="w-4 h-4" /><span>Re-run Analysis</span>
                </button>
              </div>
            ) : (
              <div className="p-8 text-center">
                <Eye className="w-8 h-8 mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Click a session to see details
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
