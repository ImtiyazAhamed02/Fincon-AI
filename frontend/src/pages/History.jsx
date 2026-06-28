import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import {
  Clock, Search, Filter, TrendingUp, TrendingDown,
  Minus, ChevronRight, Calendar, Bot, BarChart2,
  Download, RefreshCw, Eye
} from 'lucide-react';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const REC_CONFIG = {
  BUY:  { badge: 'badge-green',  icon: TrendingUp,   label: 'BUY'  },
  HOLD: { badge: 'badge-amber',  icon: Minus,        label: 'HOLD' },
  SELL: { badge: 'badge-red',    icon: TrendingDown, label: 'SELL' },
};

export default function History() {
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

  return (
    <div className="p-4 sm:p-6 md:p-8 space-y-6 animate-fade-up">

      {/* Header Controls */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center space-x-3 flex-1 min-w-[280px] max-w-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              className="fincon-input pl-10"
              placeholder="Search ticker or company…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 max-w-full">
          {['ALL', 'BUY', 'HOLD', 'SELL'].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                filter === f
                  ? 'text-white'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
              style={filter === f ? {
                background: f === 'BUY' ? 'rgba(16,185,129,0.2)' : f === 'SELL' ? 'rgba(239,68,68,0.2)' : f === 'HOLD' ? 'rgba(245,158,11,0.2)' : 'rgba(59,130,246,0.2)',
                border: `1px solid ${f === 'BUY' ? 'rgba(16,185,129,0.4)' : f === 'SELL' ? 'rgba(239,68,68,0.4)' : f === 'HOLD' ? 'rgba(245,158,11,0.4)' : 'rgba(59,130,246,0.4)'}`,
                color: f === 'BUY' ? '#34d399' : f === 'SELL' ? '#f87171' : f === 'HOLD' ? '#fbbf24' : '#60a5fa',
              } : { background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.06)' }}
            >{f}</button>
          ))}
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Sessions', value: sessions.length, color: '#3b82f6' },
          { label: 'BUY Signals',   value: sessions.filter(s => s.rec === 'BUY').length,  color: '#10b981' },
          { label: 'HOLD Signals',  value: sessions.filter(s => s.rec === 'HOLD').length, color: '#f59e0b' },
          { label: 'SELL Signals',  value: sessions.filter(s => s.rec === 'SELL').length, color: '#ef4444' },
        ].map(s => (
          <div key={s.label} className="glass rounded-2xl p-4 text-center">
            <p className="text-2xl font-black" style={{ color: s.color }}>{s.value}</p>
            <p className="text-xs text-slate-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Sessions List */}
        <div className="xl:col-span-2 space-y-3">
          {loading && (
            <div className="glass rounded-2xl p-12 text-center">
              <RefreshCw className="w-10 h-10 text-slate-700 mx-auto mb-3 animate-spin" />
              <p className="text-slate-500 text-sm">Loading history...</p>
            </div>
          )}
          {!loading && filtered.length === 0 && (
            <div className="glass rounded-2xl p-12 text-center">
              <Clock className="w-10 h-10 text-slate-700 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No sessions found</p>
            </div>
          )}
          {!loading && filtered.map(s => {
            const cfg = REC_CONFIG[s.rec];
            const RecIcon = cfg.icon;
            const isSelected = selected?.id === s.id;
            return (
              <div key={s.id}
                onClick={() => setSelected(isSelected ? null : s)}
                className="glass rounded-2xl p-5 cursor-pointer transition-all duration-200"
                style={{
                  border: `1px solid ${isSelected ? 'rgba(59,130,246,0.4)' : 'rgba(255,255,255,0.06)'}`,
                  background: isSelected ? 'rgba(59,130,246,0.05)' : undefined,
                }}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-black text-xs text-white"
                      style={{ background: 'rgba(30,41,59,0.8)', border: '1px solid rgba(255,255,255,0.08)' }}>
                      {s.ticker.slice(0, 2)}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <p className="text-sm font-bold text-white">{s.ticker}</p>
                        <p className="text-xs text-slate-500">{s.company}</p>
                      </div>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed max-w-lg">{s.summary}</p>
                      <div className="flex items-center space-x-3 mt-2">
                        <span className="flex items-center space-x-1 text-[10px] text-slate-600">
                          <Calendar className="w-3 h-3" /><span>{s.date} · {s.time}</span>
                        </span>
                        <span className="flex items-center space-x-1 text-[10px] text-slate-600">
                          <Bot className="w-3 h-3" /><span>{s.agents.length} agents</span>
                        </span>
                        <span className="flex items-center space-x-1 text-[10px] text-slate-600">
                          <Clock className="w-3 h-3" /><span>{s.duration}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end space-y-2 flex-shrink-0">
                    <span className={cfg.badge + ' flex items-center space-x-1'}>
                      <RecIcon className="w-3 h-3" /><span>{cfg.label}</span>
                    </span>
                    <div className="flex items-center space-x-1.5">
                      <div className="w-16 h-1.5 rounded-full bg-slate-800">
                        <div className="h-full rounded-full"
                          style={{ width: `${s.score}%`, background: s.score > 80 ? '#10b981' : s.score > 60 ? '#f59e0b' : '#ef4444' }} />
                      </div>
                      <span className="text-[10px] text-slate-500">{s.score}%</span>
                    </div>
                    <button onClick={e => { e.stopPropagation(); navigate('/analysis'); }}
                      className="flex items-center space-x-1 text-[10px] text-blue-400 hover:text-blue-300 transition-colors">
                      <RefreshCw className="w-3 h-3" /><span>Re-run</span>
                    </button>
                  </div>
                </div>

                {/* Agents used */}
                <div className="flex items-center space-x-2 mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                  <span className="text-[10px] text-slate-600 uppercase tracking-widest">Agents:</span>
                  {s.agents.map(a => (
                    <span key={a} className="px-2 py-0.5 rounded-lg text-[10px] font-semibold text-slate-400"
                      style={{ background: 'rgba(30,41,59,0.8)', border: '1px solid rgba(255,255,255,0.06)' }}>
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Detail Panel */}
        <div className="xl:col-span-1">
          <div className="glass rounded-2xl overflow-hidden sticky top-4">
            <div className="px-5 py-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <h3 className="text-sm font-bold text-white">Session Detail</h3>
            </div>
            {selected ? (
              <div className="p-5 space-y-4">
                <div>
                  <p className="text-xs text-slate-500 mb-1">Ticker</p>
                  <p className="text-lg font-black text-white">{selected.ticker}
                    <span className="text-xs font-normal text-slate-500 ml-2">{selected.company}</span>
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Recommendation', value: selected.rec, color: selected.rec === 'BUY' ? '#10b981' : selected.rec === 'SELL' ? '#ef4444' : '#f59e0b' },
                    { label: 'Confidence', value: `${selected.score}%`, color: selected.score > 80 ? '#10b981' : '#f59e0b' },
                    { label: 'Duration', value: selected.duration, color: '#3b82f6' },
                    { label: 'Agents Used', value: selected.agents.length, color: '#8b5cf6' },
                  ].map(item => (
                    <div key={item.label} className="rounded-xl p-3"
                      style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <p className="text-[10px] text-slate-500 mb-1">{item.label}</p>
                      <p className="text-base font-black" style={{ color: item.color }}>{item.value}</p>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-2">Summary</p>
                  <p className="text-xs text-slate-300 leading-relaxed">{selected.summary}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-2">Agents Involved</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selected.agents.map(a => (
                      <span key={a} className="badge-blue text-[10px]">{a}</span>
                    ))}
                  </div>
                </div>
                <button onClick={() => navigate('/analysis')} className="btn-primary w-full flex items-center justify-center space-x-2">
                  <RefreshCw className="w-4 h-4" /><span>Re-run Analysis</span>
                </button>
              </div>
            ) : (
              <div className="p-8 text-center">
                <Eye className="w-8 h-8 text-slate-700 mx-auto mb-3" />
                <p className="text-xs text-slate-600">Click a session to see details</p>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
