import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Briefcase, PieChart, TrendingUp, TrendingDown,
  Zap, AlertTriangle, ChevronDown, ChevronUp,
  Plus, Trash2, BarChart2, PlusCircle, Check, X, FolderPlus
} from 'lucide-react';
import { PieChart as RPieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import Markdown from '../components/Markdown';
import { useTheme } from '../context/ThemeContext';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#38bdf8', '#a855f7', '#14b8a6'];

const CUSTOM_TOOLTIP = ({ active, payload }) => {
  if (active && payload?.length) {
    const d = payload[0].payload;
    return (
      <div
        className="card px-3 py-2 text-xs"
        style={{ minWidth: 120 }}
      >
        <p className="font-bold" style={{ color: 'var(--text-primary)' }}>{d.ticker}</p>
        <p style={{ color: 'var(--text-tertiary)' }}>
          {d.weight}% · ${d.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </p>
      </div>
    );
  }
  return null;
};

export default function Portfolio() {
  const { isDark } = useTheme();

  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  
  // Holding Form State
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [costBasis, setCostBasis] = useState('');

  const [state, setState] = useState({ loading: false, result: null, error: null });
  const [expanded, setExpanded] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Load Portfolios on Mount
  useEffect(() => {
    fetchPortfolios();
  }, []);

  const fetchPortfolios = async (selectId = null) => {
    try {
      const res = await axios.get(`${API}/api/portfolios`);
      const list = res.data.portfolios || [];
      setPortfolios(list);
      
      if (list.length > 0) {
        // Find portfolio to select
        const toSelect = selectId ? list.find(p => p.id === selectId) : list[0];
        const selected = toSelect || list[0];
        setSelectedPortfolio(selected);
        fetchHoldings(selected.id);
      } else {
        setSelectedPortfolio(null);
        setHoldings([]);
      }
    } catch (err) {
      console.error("Error loading portfolios", err);
    }
  };

  const fetchHoldings = async (portfolioId) => {
    try {
      const res = await axios.get(`${API}/api/portfolios/${portfolioId}/holdings`);
      setHoldings(res.data.holdings || []);
    } catch (err) {
      console.error("Error loading holdings", err);
    }
  };

  const handleSelectPortfolio = (e) => {
    const id = e.target.value;
    const portfolio = portfolios.find(p => p.id === id);
    if (portfolio) {
      setSelectedPortfolio(portfolio);
      fetchHoldings(portfolio.id);
      setState({ loading: false, result: null, error: null });
    }
  };

  const handleCreatePortfolio = async (e) => {
    e.preventDefault();
    if (!newPortfolioName.trim()) return;
    try {
      const res = await axios.post(`${API}/api/portfolios`, { name: newPortfolioName });
      setNewPortfolioName('');
      setShowCreateForm(false);
      fetchPortfolios(res.data.id);
    } catch (err) {
      console.error("Failed to create portfolio", err);
    }
  };

  const handleDeletePortfolio = async () => {
    if (!selectedPortfolio || !window.confirm(`Are you sure you want to delete "${selectedPortfolio.name}"?`)) return;
    try {
      await axios.delete(`${API}/api/portfolios/${selectedPortfolio.id}`);
      fetchPortfolios();
    } catch (err) {
      console.error("Failed to delete portfolio", err);
    }
  };

  const handleAddHolding = async (e) => {
    e.preventDefault();
    if (!selectedPortfolio || !ticker.trim() || !shares || !costBasis) return;
    
    try {
      await axios.post(`${API}/api/portfolios/${selectedPortfolio.id}/holdings`, {
        ticker: ticker.toUpperCase().strip ? ticker.toUpperCase().strip() : ticker.toUpperCase().trim(),
        shares: parseFloat(shares),
        cost_basis: parseFloat(costBasis)
      });
      setTicker('');
      setShares('');
      setCostBasis('');
      fetchHoldings(selectedPortfolio.id);
    } catch (err) {
      console.error("Failed to add holding", err);
    }
  };

  const handleDeleteHolding = async (tickerToDelete) => {
    if (!selectedPortfolio) return;
    try {
      await axios.delete(`${API}/api/portfolios/${selectedPortfolio.id}/holdings/${tickerToDelete}`);
      fetchHoldings(selectedPortfolio.id);
    } catch (err) {
      console.error("Failed to delete holding", err);
    }
  };

  const runAnalysis = async () => {
    if (!selectedPortfolio) return;
    setState({ loading: true, result: null, error: null });
    try {
      const res = await axios.post(`${API}/api/analyze/portfolio`, { portfolio_id: selectedPortfolio.id });
      setState({ loading: false, result: res.data.result || JSON.stringify(res.data, null, 2) });
    } catch (err) {
      setState({ loading: false, error: err.response?.data?.detail || err.message });
    }
  };

  // Calculations for display
  const holdingsWithValues = holdings.map((h, i) => {
    // Current value proxy based on cost basis (in real app, multiply by current price)
    const val = h.shares * h.cost_basis;
    return {
      ticker: h.ticker,
      shares: h.shares,
      cost_basis: h.cost_basis,
      value: val,
      color: COLORS[i % COLORS.length]
    };
  });

  const totalValue = holdingsWithValues.reduce((sum, h) => sum + h.value, 0);

  const pieChartData = holdingsWithValues.map(h => ({
    ticker: h.ticker,
    value: h.value,
    weight: totalValue > 0 ? parseFloat(((h.value / totalValue) * 100).toFixed(1)) : 0,
    color: h.color
  }));

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-up">

      {/* ─── Portfolio Selector & Controls ─── */}
      <div
        className="card p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div className="flex flex-wrap items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{
              background: 'rgba(79, 139, 255, 0.12)',
              border: '1px solid rgba(79, 139, 255, 0.2)',
            }}
          >
            <Briefcase className="w-[17px] h-[17px]" style={{ color: 'var(--accent-blue)' }} />
          </div>
          <span className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
            Active Portfolio:
          </span>
          {portfolios.length > 0 ? (
            <select
              value={selectedPortfolio?.id || ''}
              onChange={handleSelectPortfolio}
              className="input-field !w-auto !py-2 !px-3 text-sm font-semibold"
              style={{ minWidth: 140 }}
            >
              {portfolios.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          ) : (
            <span className="text-xs italic" style={{ color: 'var(--text-muted)' }}>
              No portfolios exist. Please create one.
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
          <button 
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn-secondary !py-2 !px-3 !text-xs flex-1 sm:flex-initial"
          >
            <FolderPlus className="w-4 h-4" />
            <span>New Portfolio</span>
          </button>
          
          {selectedPortfolio && (
            <button 
              onClick={handleDeletePortfolio}
              className="btn-danger !py-2 !px-3 !text-xs flex-1 sm:flex-initial"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete</span>
            </button>
          )}
        </div>
      </div>

      {/* ─── Create Portfolio Form ─── */}
      {showCreateForm && (
        <form
          onSubmit={handleCreatePortfolio}
          className="card p-5 flex flex-col sm:flex-row items-stretch sm:items-center gap-3 max-w-lg animate-fade-up"
        >
          <input
            type="text"
            className="input-field !py-2 flex-1"
            placeholder="Portfolio Name (e.g. Growth)"
            value={newPortfolioName}
            onChange={e => setNewPortfolioName(e.target.value)}
            required
          />
          <div className="flex gap-2">
            <button type="submit" className="btn-primary !py-2 !px-4 !text-xs flex-1 sm:flex-initial">
              <Check className="w-4 h-4" />
              <span>Create</span>
            </button>
            <button 
              type="button" 
              onClick={() => setShowCreateForm(false)} 
              className="btn-secondary !py-2 !px-3 !text-xs"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </form>
      )}

      {selectedPortfolio ? (
        <>
          {/* ─── Summary Metric Cards ─── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Portfolio Value */}
            <div
              className="card p-5"
              style={{ borderLeft: '3px solid var(--accent-emerald)' }}
            >
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{
                    background: 'rgba(16, 185, 129, 0.12)',
                  }}
                >
                  <TrendingUp className="w-4 h-4" style={{ color: 'var(--accent-emerald)' }} />
                </div>
                <span className="label !mb-0">Portfolio Value</span>
              </div>
              <p className="text-2xl font-black" style={{ color: 'var(--accent-emerald)' }}>
                ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs mt-1.5" style={{ color: 'var(--text-tertiary)' }}>
                Based on purchase cost basis
              </p>
            </div>

            {/* Total Assets */}
            <div
              className="card p-5"
              style={{ borderLeft: '3px solid var(--accent-blue)' }}
            >
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{
                    background: 'rgba(79, 139, 255, 0.12)',
                  }}
                >
                  <BarChart2 className="w-4 h-4" style={{ color: 'var(--accent-blue)' }} />
                </div>
                <span className="label !mb-0">Total Assets</span>
              </div>
              <p className="text-2xl font-black" style={{ color: 'var(--accent-blue)' }}>
                {holdings.length} <span className="text-base font-semibold" style={{ color: 'var(--text-tertiary)' }}>positions</span>
              </p>
              <p className="text-xs mt-1.5" style={{ color: 'var(--text-tertiary)' }}>
                Directly stored in SQLite
              </p>
            </div>

            {/* Risk Assessment */}
            <div
              className="card p-5"
              style={{ borderLeft: '3px solid var(--accent-purple)' }}
            >
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{
                    background: 'rgba(167, 139, 250, 0.12)',
                  }}
                >
                  <AlertTriangle className="w-4 h-4" style={{ color: 'var(--accent-purple)' }} />
                </div>
                <span className="label !mb-0">Risk Assessment</span>
              </div>
              <p className="text-2xl font-black" style={{ color: 'var(--accent-purple)' }}>
                Dynamic Score
              </p>
              <p className="text-xs mt-1.5" style={{ color: 'var(--text-tertiary)' }}>
                Calculated via Portfolio Agent
              </p>
            </div>
          </div>

          {/* ─── Holdings & Allocation Charts ─── */}
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
            
            {/* Holdings Table */}
            <div className="xl:col-span-3 card overflow-hidden flex flex-col">
              <div
                className="px-5 sm:px-6 py-4 flex items-center justify-between"
                style={{ borderBottom: '1px solid var(--border-subtle)' }}
              >
                <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                  Holdings
                </h3>
                <span className="badge badge-blue">{holdings.length} positions</span>
              </div>
              
              <div className="flex-1 overflow-x-auto">
                <table className="table-pro">
                  <thead>
                    <tr>
                      <th className="!pl-6">Asset</th>
                      <th>Shares</th>
                      <th>Avg Cost</th>
                      <th>Value</th>
                      <th>Allocation</th>
                      <th className="!pr-6 !text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {holdingsWithValues.length === 0 ? (
                      <tr>
                        <td
                          colSpan="6"
                          className="!text-center italic !py-10"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          No holdings inside this portfolio. Add below to begin.
                        </td>
                      </tr>
                    ) : (
                      holdingsWithValues.map(h => {
                        const weight = totalValue > 0 ? ((h.value / totalValue) * 100).toFixed(1) : 0;
                        return (
                          <tr key={h.ticker}>
                            <td className="!pl-6">
                              <div className="flex items-center gap-3">
                                <div 
                                  className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold flex-shrink-0"
                                  style={{
                                    background: `${h.color}15`,
                                    border: `1px solid ${h.color}30`,
                                    color: h.color,
                                  }}
                                >
                                  {h.ticker.slice(0, 2)}
                                </div>
                                <div>
                                  <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                                    {h.ticker}
                                  </p>
                                </div>
                              </div>
                            </td>
                            <td>
                              <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                {h.shares}
                              </span>
                            </td>
                            <td>
                              <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>
                                ${h.cost_basis.toFixed(2)}
                              </span>
                            </td>
                            <td>
                              <span className="font-bold" style={{ color: 'var(--text-primary)' }}>
                                ${h.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </span>
                            </td>
                            <td style={{ minWidth: 120 }}>
                              <div className="flex items-center gap-2">
                                <div
                                  className="flex-1 h-2 rounded-full overflow-hidden"
                                  style={{ background: 'var(--border-subtle)' }}
                                >
                                  <div
                                    className="h-full rounded-full transition-all duration-500"
                                    style={{
                                      width: `${weight}%`,
                                      background: h.color,
                                      opacity: 0.85,
                                    }}
                                  />
                                </div>
                                <span className="text-xs font-semibold w-10 text-right" style={{ color: 'var(--text-tertiary)' }}>
                                  {weight}%
                                </span>
                              </div>
                            </td>
                            <td className="!pr-6 !text-right">
                              <button 
                                onClick={() => handleDeleteHolding(h.ticker)}
                                className="p-1.5 rounded-lg transition-all duration-200"
                                style={{
                                  color: 'var(--accent-rose)',
                                  background: 'transparent',
                                  border: 'none',
                                  cursor: 'pointer',
                                }}
                                onMouseEnter={e => {
                                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                                }}
                                onMouseLeave={e => {
                                  e.currentTarget.style.background = 'transparent';
                                }}
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>

              {/* Add Holding Form */}
              <div
                className="p-4 sm:p-5"
                style={{
                  borderTop: '1px solid var(--border-subtle)',
                  background: 'var(--bg-elevated)',
                }}
              >
                <p className="label mb-3">Add or Edit Asset Position</p>
                <form onSubmit={handleAddHolding} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <input
                    type="text"
                    className="input-field !py-2 !text-sm"
                    placeholder="Ticker (e.g. AAPL)"
                    value={ticker}
                    onChange={e => setTicker(e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    step="any"
                    className="input-field !py-2 !text-sm"
                    placeholder="Shares"
                    value={shares}
                    onChange={e => setShares(e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    step="any"
                    className="input-field !py-2 !text-sm"
                    placeholder="Avg Cost Basis"
                    value={costBasis}
                    onChange={e => setCostBasis(e.target.value)}
                    required
                  />
                  <button type="submit" className="btn-primary !py-2 !px-3 !text-xs">
                    <PlusCircle className="w-4 h-4" />
                    <span>Save Position</span>
                  </button>
                </form>
              </div>
            </div>

            {/* Allocation Chart */}
            <div className="xl:col-span-2 card p-5 sm:p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-5">
                  <PieChart className="w-4 h-4" style={{ color: 'var(--accent-purple)' }} />
                  <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                    Portfolio Allocation
                  </h3>
                </div>
                {pieChartData.length > 0 ? (
                  <div style={{ height: 210 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <RPieChart>
                        <Pie 
                          data={pieChartData} 
                          cx="50%" 
                          cy="50%" 
                          innerRadius={55} 
                          outerRadius={85}
                          dataKey="value" 
                          stroke="none"
                          paddingAngle={2}
                        >
                          {pieChartData.map((h, i) => (
                            <Cell key={i} fill={h.color} opacity={0.85} />
                          ))}
                        </Pie>
                        <Tooltip content={<CUSTOM_TOOLTIP />} />
                      </RPieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div
                    className="flex items-center justify-center text-xs italic"
                    style={{ height: 210, color: 'var(--text-muted)' }}
                  >
                    Add holdings to visualize allocation
                  </div>
                )}
              </div>
              
              {/* Legend */}
              <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 mt-5 max-h-[150px] overflow-y-auto">
                {pieChartData.map(h => (
                  <div key={h.ticker} className="flex items-center gap-2">
                    <div
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ background: h.color }}
                    />
                    <span className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>
                      {h.ticker}
                    </span>
                    <span className="text-xs ml-auto font-semibold" style={{ color: 'var(--text-tertiary)' }}>
                      {h.weight}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ─── AI Portfolio Manager Agent ─── */}
          <div className="card overflow-hidden">
            {/* Header */}
            <div
              className="px-5 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              style={{ borderBottom: '1px solid var(--border-subtle)' }}
            >
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{
                    background: 'rgba(16, 185, 129, 0.12)',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                  }}
                >
                  <Briefcase className="w-[18px] h-[18px]" style={{ color: 'var(--accent-emerald)' }} />
                </div>
                <div>
                  <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
                    Portfolio Manager Agent
                  </p>
                  <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                    AI-powered rebalancing and diversification analysis
                  </p>
                </div>
              </div>
              <button
                onClick={runAnalysis}
                disabled={holdings.length === 0 || state.loading}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                style={{
                  background: 'var(--gradient-success)',
                  boxShadow: 'var(--shadow-glow-emerald)',
                  whiteSpace: 'nowrap',
                  border: 'none',
                  cursor: holdings.length === 0 || state.loading ? 'not-allowed' : 'pointer',
                }}
              >
                {state.loading ? (
                  <>
                    <div
                      className="w-4 h-4 rounded-full animate-spin"
                      style={{
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTopColor: 'white',
                      }}
                    />
                    <span>Analyzing…</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    <span>Run Analysis</span>
                  </>
                )}
              </button>
            </div>
            
            {/* Body */}
            <div className="px-5 sm:px-6 py-5">
              {state.error && (
                <div 
                  className="flex items-start gap-2 text-xs p-3.5 rounded-xl"
                  style={{
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    color: 'var(--accent-rose)',
                  }}
                >
                  <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{state.error}</span>
                </div>
              )}
              {state.result && (
                <>
                  <div 
                    className={`text-sm leading-relaxed ${!expanded ? 'max-h-48 overflow-hidden' : ''}`}
                    style={{
                      color: 'var(--text-secondary)',
                      maskImage: !expanded ? 'linear-gradient(to bottom, black 50%, transparent 100%)' : 'none',
                      WebkitMaskImage: !expanded ? 'linear-gradient(to bottom, black 50%, transparent 100%)' : 'none',
                    }}
                  >
                    <Markdown content={state.result} />
                  </div>
                  <button 
                    onClick={() => setExpanded(e => !e)}
                    className="mt-3 flex items-center gap-1.5 text-xs font-semibold transition-colors"
                    style={{
                      color: 'var(--accent-emerald)',
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    {expanded ? (
                      <>
                        <ChevronUp className="w-3.5 h-3.5" />
                        <span>Collapse</span>
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-3.5 h-3.5" />
                        <span>Expand full report</span>
                      </>
                    )}
                  </button>
                </>
              )}
              {!state.result && !state.error && !state.loading && (
                <p className="text-sm italic" style={{ color: 'var(--text-muted)' }}>
                  {holdings.length === 0 
                    ? "Add asset positions above to activate Portfolio Agent analysis."
                    : "Run the agent to receive institutional-grade rebalancing advice."}
                </p>
              )}
            </div>
          </div>
        </>
      ) : (
        <div
          className="card p-12 text-center italic"
          style={{ color: 'var(--text-muted)' }}
        >
          No active portfolio available. Click "New Portfolio" above to create one.
        </div>
      )}

    </div>
  );
}
