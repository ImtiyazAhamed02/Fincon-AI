import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Briefcase, PieChart, TrendingUp, TrendingDown,
  Zap, AlertTriangle, ChevronDown, ChevronUp,
  Plus, Trash2, BarChart2, PlusCircle, Check, X, FolderPlus
} from 'lucide-react';
import { PieChart as RPieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#38bdf8', '#a855f7', '#14b8a6'];

const CUSTOM_TOOLTIP = ({ active, payload }) => {
  if (active && payload?.length) {
    const d = payload[0].payload;
    return (
      <div className="glass rounded-xl px-3 py-2 text-xs">
        <p className="font-bold text-white">{d.ticker}</p>
        <p className="text-slate-400">{d.weight}% · ${d.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
      </div>
    );
  }
  return null;
};

export default function Portfolio() {
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
    <div className="p-8 space-y-6 animate-fade-up">

      {/* Portfolio Selector & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass p-4 rounded-2xl">
        <div className="flex items-center space-x-3">
          <Briefcase className="w-5 h-5 text-blue-400" />
          <span className="text-sm font-bold text-white">Active Portfolio:</span>
          {portfolios.length > 0 ? (
            <select
              value={selectedPortfolio?.id || ''}
              onChange={handleSelectPortfolio}
              className="bg-slate-900 border border-slate-800 text-white rounded-xl px-3 py-1.5 text-sm font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {portfolios.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          ) : (
            <span className="text-xs text-slate-500 italic">No portfolios exist. Please create one.</span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button 
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn-secondary py-2 px-3 text-xs flex items-center space-x-1.5"
          >
            <FolderPlus className="w-4 h-4" />
            <span>New Portfolio</span>
          </button>
          
          {selectedPortfolio && (
            <button 
              onClick={handleDeletePortfolio}
              className="btn-secondary py-2 px-3 text-xs text-red-400 hover:text-red-300 border-red-500/20 flex items-center space-x-1.5"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete Portfolio</span>
            </button>
          )}
        </div>
      </div>

      {/* Create Portfolio Form */}
      {showCreateForm && (
        <form onSubmit={handleCreatePortfolio} className="glass p-5 rounded-2xl flex items-center space-x-3 max-w-md animate-fade-in">
          <input
            type="text"
            className="fincon-input flex-1 py-2"
            placeholder="Portfolio Name (e.g. Growth)"
            value={newPortfolioName}
            onChange={e => setNewPortfolioName(e.target.value)}
            required
          />
          <button type="submit" className="btn-primary py-2 px-4 text-xs flex items-center space-x-1">
            <Check className="w-4 h-4" />
            <span>Create</span>
          </button>
          <button 
            type="button" 
            onClick={() => setShowCreateForm(false)} 
            className="btn-secondary py-2 px-3 text-xs"
          >
            <X className="w-4 h-4" />
          </button>
        </form>
      )}

      {selectedPortfolio ? (
        <>
          {/* Summary Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="glass rounded-2xl p-5">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Portfolio Value</p>
              <p className="text-2xl font-black text-emerald-400">
                ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-slate-500 mt-1">Based on purchase cost basis</p>
            </div>
            <div className="glass rounded-2xl p-5">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Total Assets</p>
              <p className="text-2xl font-black text-blue-400">{holdings.length} positions</p>
              <p className="text-xs text-slate-500 mt-1">Directly stored in SQLite</p>
            </div>
            <div className="glass rounded-2xl p-5">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Risk Assessment</p>
              <p className="text-2xl font-black text-purple-400">Dynamic Score</p>
              <p className="text-xs text-slate-500 mt-1">Calculated via Portfolio Agent</p>
            </div>
          </div>

          {/* Holdings & Allocation Charts */}
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
            
            {/* Holdings Table */}
            <div className="xl:col-span-3 glass rounded-2xl overflow-hidden flex flex-col">
              <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <h3 className="text-sm font-bold text-white">Holdings</h3>
                <span className="badge-blue">{holdings.length} positions</span>
              </div>
              
              <div className="flex-1 overflow-x-auto">
                <table className="fincon-table">
                  <thead>
                    <tr>
                      <th className="pl-6">Asset</th>
                      <th>Shares</th>
                      <th>Avg Cost</th>
                      <th>Value</th>
                      <th className="pr-6 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {holdingsWithValues.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="text-center text-slate-500 italic py-8 text-xs">
                          No holdings inside this portfolio. Add below to begin.
                        </td>
                      </tr>
                    ) : (
                      holdingsWithValues.map(h => {
                        const weight = totalValue > 0 ? ((h.value / totalValue) * 100).toFixed(1) : 0;
                        return (
                          <tr key={h.ticker}>
                            <td className="pl-6">
                              <div className="flex items-center space-x-3">
                                <div 
                                  className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                                  style={{ background: `${h.color}20`, border: `1px solid ${h.color}30`, color: h.color }}
                                >
                                  {h.ticker.slice(0, 2)}
                                </div>
                                <div>
                                  <p className="text-sm font-bold text-white">{h.ticker}</p>
                                  <p className="text-[10px] text-slate-500">Allocation: {weight}%</p>
                                </div>
                              </div>
                            </td>
                            <td className="text-slate-300 text-sm font-semibold">{h.shares}</td>
                            <td className="text-slate-300 text-sm font-semibold">${h.cost_basis.toFixed(2)}</td>
                            <td className="text-slate-300 text-sm font-bold">${h.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                            <td className="pr-6 text-right">
                              <button 
                                onClick={() => handleDeleteHolding(h.ticker)}
                                className="text-red-400 hover:text-red-300 p-1.5 rounded-lg hover:bg-red-500/10 transition-colors"
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
              <div className="p-4 bg-slate-950/40 border-t border-slate-900">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Add or Edit Asset Position</p>
                <form onSubmit={handleAddHolding} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <input
                    type="text"
                    className="fincon-input text-xs py-2"
                    placeholder="Ticker (e.g. AAPL)"
                    value={ticker}
                    onChange={e => setTicker(e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    step="any"
                    className="fincon-input text-xs py-2"
                    placeholder="Shares"
                    value={shares}
                    onChange={e => setShares(e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    step="any"
                    className="fincon-input text-xs py-2"
                    placeholder="Avg Cost Basis"
                    value={costBasis}
                    onChange={e => setCostBasis(e.target.value)}
                    required
                  />
                  <button type="submit" className="btn-primary py-2 px-3 text-xs flex items-center justify-center space-x-1.5">
                    <PlusCircle className="w-4 h-4" />
                    <span>Save Position</span>
                  </button>
                </form>
              </div>
            </div>

            {/* Allocation Chart */}
            <div className="xl:col-span-2 glass rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-white mb-4">Portfolio Allocation</h3>
                {pieChartData.length > 0 ? (
                  <div style={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <RPieChart>
                        <Pie 
                          data={pieChartData} 
                          cx="50%" 
                          cy="50%" 
                          innerRadius={50} 
                          outerRadius={80}
                          dataKey="value" 
                          stroke="none"
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
                  <div className="h-[200px] flex items-center justify-center text-slate-500 text-xs italic">
                    Add holdings to visualize allocation
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-4 max-h-[140px] overflow-y-auto">
                {pieChartData.map(h => (
                  <div key={h.ticker} className="flex items-center space-x-2">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: h.color }} />
                    <span className="text-xs text-slate-400 truncate">{h.ticker}</span>
                    <span className="text-xs text-slate-600 ml-auto">{h.weight}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* AI Portfolio Rebalancing Analysis */}
          <div className="glass rounded-2xl overflow-hidden">
            <div className="px-6 py-4 flex items-center space-x-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <div 
                className="w-9 h-9 rounded-xl flex items-center justify-center"
                style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }}
              >
                <Briefcase className="w-4.5 h-4.5 text-emerald-400" style={{ width: 17, height: 17 }} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold text-white">Portfolio Manager Agent</p>
                <p className="text-xs text-slate-500">AI-powered rebalancing and diversification analysis</p>
              </div>
              <button
                onClick={runAnalysis}
                disabled={holdings.length === 0 || state.loading}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                style={{ background: 'linear-gradient(135deg,#059669,#0d9488)', boxShadow: '0 4px 15px rgba(5,150,105,0.3)', whiteSpace: 'nowrap' }}
              >
                {state.loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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
            
            <div className="px-6 py-5">
              {state.error && (
                <div 
                  className="flex items-start space-x-2 text-red-400 text-xs p-3 rounded-xl"
                  style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
                >
                  <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{state.error}</span>
                </div>
              )}
              {state.result && (
                <>
                  <div 
                    className={`text-sm text-slate-200 leading-relaxed whitespace-pre-wrap ${!expanded ? 'max-h-48 overflow-hidden' : ''}`}
                    style={{ maskImage: !expanded ? 'linear-gradient(to bottom, black 50%, transparent 100%)' : 'none' }}
                  >
                    {state.result}
                  </div>
                  <button 
                    onClick={() => setExpanded(e => !e)}
                    className="mt-3 flex items-center space-x-1 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
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
                <p className="text-sm text-slate-600 italic">
                  {holdings.length === 0 
                    ? "Add asset positions above to activate Portfolio Agent analysis."
                    : "Run the agent to receive institutional-grade rebalancing advice."}
                </p>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="glass rounded-2xl p-12 text-center text-slate-500 italic">
          No active portfolio available. Click "New Portfolio" above to create one.
        </div>
      )}

    </div>
  );
}
