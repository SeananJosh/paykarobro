import React, { useState, useEffect } from 'react';
import api from './api';
import './index.css';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import { 
  LayoutDashboard, 
  Bot, 
  TrendingUp, 
  Settings, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  MessageSquare,
  CreditCard,
  Upload,
  FileText,
  Mic,
  MicOff,
  Globe,
  Zap
} from 'lucide-react';

function App() {
  const [lang, setLang] = useState('en');
  const [obligations, setObligations] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      // Seed first
      await api.post('/seed_demo');
      
      // Run AI agents
      const [rankRes, forecastRes, digestRes] = await Promise.all([
        api.post('/agents/priority/rank'),
        api.get('/agents/cashflow/forecast'),
        api.get(`/agents/insight/digest?lang=${lang}`)
      ]);
      
      // Load resulting data
      setObligations(rankRes.data.ranked_obligations);
      setForecast(forecastRes.data.forecast);
      setDigest(digestRes.data);
    } catch (err) {
      console.error("Failed to load dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [lang]);

  const handleApproveManager = async (id) => {
    try {
      await api.patch(`/obligations/${id}/approve`);
      setObligations(prev => prev.map(ob => ob.id === id ? { ...ob, is_manager_approved: 1 } : ob));
    } catch (err) {
      console.error("Failed to sign off", err);
    }
  };

  const [negotiationStrategies, setNegotiationStrategies] = useState([]);
  const [selectedStrategyIndex, setSelectedStrategyIndex] = useState(0);

  const handleNegotiate = async (ob) => {
    try {
      const res = await api.get(`/agents/negotiation/strategies?vendor_name=${ob.vendor_name}&amount=${ob.amount}&due_date=${ob.due_date}`);
      setNegotiationStrategies(res.data.strategies);
      setSelectedStrategyIndex(0);
    } catch (err) {
      console.error("Negotiation strategy failed", err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setIsUploading(true);
      await api.post('/expenses/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert('Expenses imported successfully!');
      loadDashboardData(); // Refresh
    } catch (err) {
      alert('Import failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsUploading(false);
    }
  };

  const handleExecutePayment = async (ob) => {
    if (!window.confirm(`Authorize payment of ₹${ob.amount.toLocaleString()} to ${ob.vendor_name}?`)) return;
    
    try {
      const res = await api.post(`/payments/execute/${ob.id}`);
      if (res.data.status === 'success') {
        alert(`Payment Success! Ref: ${res.data.gateway_ref}`);
        setObligations(prev => prev.map(o => o.id === ob.id ? { ...o, status: 'paid' } : o));
      }
    } catch (err) {
      alert('Payment failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const [isListening, setIsListening] = useState(false);

  const startVoiceCommand = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice recognition not supported in this browser.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    
    recognition.onresult = (event) => {
      const command = event.results[0][0].transcript.toLowerCase();
      console.log("Voice Command:", command);
      
      if (command.includes("approve all")) {
        const highPri = obligations.filter(o => o.priority === 'High' && o.status === 'pending');
        highPri.forEach(o => handleExecutePayment(o));
      } else if (command.includes("re-analyze") || command.includes("refresh")) {
        loadDashboardData();
      } else if (command.includes("import")) {
        document.querySelector('input[type="file"]').click();
      } else {
        alert(`You said: "${command}". I don't recognize that command yet.`);
      }
    };
    
    recognition.start();
  };

  const [isUploading, setIsUploading] = useState(false);

  // ... (keeping other handlers)

  if (loading || !digest) return <div className="loading-state">Initializing PaykaroBRO AI Engine...</div>;

  return (
    <div className="dashboard-container">
      {negotiationStrategies.length > 0 && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '800px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3>AI Negotiation Strategies</h3>
              <button className="btn btn-outline" onClick={() => setNegotiationStrategies([])}>×</button>
            </div>
            
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
              {negotiationStrategies.map((s, idx) => (
                <button 
                  key={idx}
                  className={`btn ${selectedStrategyIndex === idx ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => setSelectedStrategyIndex(idx)}
                  style={{ whiteSpace: 'nowrap' }}
                >
                  {s.tone} <span style={{ fontSize: '0.65rem', opacity: 0.7 }}>({s.risk} Risk)</span>
                </button>
              ))}
            </div>

            <pre className="glass-card" style={{ whiteSpace: 'pre-wrap', padding: '1.5rem', borderRadius: '1rem', margin: '1rem 0', fontSize: '0.9rem', color: 'var(--text-primary)', border: '1px solid rgba(255,255,255,0.1)' }}>
              {negotiationStrategies[selectedStrategyIndex].draft}
            </pre>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button className="btn btn-success" onClick={() => { navigator.clipboard.writeText(negotiationStrategies[selectedStrategyIndex].draft); alert('Copied Strategy!'); }}>
                Copy to Clipboard
              </button>
              <button className="btn btn-outline" onClick={() => setNegotiationStrategies([])}>Close</button>
            </div>
          </div>
        </div>
      )}
      <aside className="sidebar">
        <h1>PaykaroBRO</h1>
        <nav>
          <a href="#" className="nav-link active"><LayoutDashboard size={20} /> Dashboard</a>
          <a href="#" className="nav-link"><Bot size={20} /> AI Agents</a>
          <a href="#" className="nav-link"><TrendingUp size={20} /> Cash Flow</a>
          <a href="#" className="nav-link"><Settings size={20} /> Settings</a>
        </nav>
        
        <div style={{ marginTop: 'auto', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '0.75rem' }}>
          <small style={{ color: 'var(--text-secondary)' }}>Status</small>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--success)' }}></div>
            <span style={{ fontSize: '0.875rem' }}>AI Model: GPT-4o Online</span>
          </div>
        </div>
      </aside>
      
      <main className="main-content">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
          <div>
            <h2>Dashboard Overview</h2>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              Ravi's Cloud Kitchen • Last updated: Just now
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button 
              className="btn btn-outline"
              onClick={() => setLang(l => l === 'en' ? 'hi' : 'en')}
              title="Toggle Language"
            >
              <Globe size={16} /> {lang === 'en' ? 'English' : 'हिंदी'}
            </button>
            <button 
              className={`btn ${isListening ? 'btn-danger' : 'btn-outline'}`} 
              onClick={startVoiceCommand}
              title="Voice Commands"
              style={{ padding: '0.5rem' }}
            >
              {isListening ? <MicOff size={20} className="pulse" /> : <Mic size={20} />}
            </button>
            <label className="btn btn-outline" style={{ cursor: 'pointer' }}>
              <Upload size={16} /> {isUploading ? 'Uploading...' : 'Import Expenses'}
              <input type="file" accept=".csv" onChange={handleFileUpload} style={{ display: 'none' }} disabled={isUploading} />
            </label>
            <button className="btn btn-primary" style={{ background: 'var(--accent-primary)', color: 'var(--bg-primary)' }}>
              <CreditCard size={16} /> Quick Pay
            </button>
          </div>
        </header>
        
        <div className="kpi-grid">
          <div className="kpi-card glass-card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3>Projected Runway</h3>
              <Zap size={18} color="var(--accent-primary)" />
            </div>
            <p className="value">{digest.kpis.days_cash_on_hand}</p>
            <small style={{ color: 'var(--text-secondary)' }}>Based on avg. daily burn</small>
          </div>
          <div className="kpi-card">
            <h3>Monthly Burn</h3>
            <p className="value">{digest.kpis.burn_rate_monthly}</p>
          </div>
          <div className="kpi-card">
            <h3>Pending Payables</h3>
            <p className="value">{digest.kpis.pending_payables}</p>
          </div>
        </div>

        <div className="grid-2-1" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
          <div className="panel">
            <h2>30-Day Cash Flow Projection</h2>
            <div style={{ height: 300, width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecast}>
                  <defs>
                    <linearGradient id="colorBal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip 
                    contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: '8px' }}
                    itemStyle={{ color: 'var(--text-primary)' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="predicted_balance" 
                    stroke="var(--accent-primary)" 
                    fillOpacity={1} 
                    fill="url(#colorBal)" 
                    strokeWidth={2}
                  />
                  <XAxis dataKey="date" hide />
                  <YAxis hide domain={['auto', 'auto']} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel">
            <h2>Daily AI Digest</h2>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {digest.summary.map((line, i) => (
                <li key={i} style={{ 
                  marginBottom: '1rem', 
                  padding: '1rem', 
                  background: 'rgba(255,255,255,0.03)', 
                  borderRadius: '0.75rem',
                  fontSize: '0.875rem',
                  lineHeight: '1.4',
                  borderLeft: '2px solid var(--accent-secondary)'
                }}>
                  {line}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2>AI Priority Decision Board</h2>
            <button className="btn btn-outline" onClick={loadDashboardData}><Bot size={16} /> Re-analyze</button>
          </div>
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Amount</th>
                  <th>Due Date</th>
                  <th>AI Priority</th>
                  <th>Agent Reasoning</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {obligations.filter(o => o.status === 'pending').map((ob, idx) => (
                  <tr key={idx}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{ob.vendor_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Utility • GST Registered</div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>₹{ob.amount.toLocaleString()}</div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <Clock size={14} color="var(--text-secondary)" />
                        {ob.due_date}
                      </div>
                    </td>
                    <td><span className={`badge ${ob.priority.toLowerCase()}`}>{ob.priority}</span></td>
                    <td>
                      <div className="ai-reasoning-box">
                        {ob.ai_reasoning}
                        {ob.is_manager_approved ? (
                          <div style={{ color: 'var(--success)', fontSize: '0.7rem', marginTop: '0.4rem', display: 'flex', alignItems: 'center', gap: '3px' }}>
                            <CheckCircle2 size={12} /> Manager Approved
                          </div>
                        ) : (
                          <div style={{ color: 'var(--warning)', fontSize: '0.7rem', marginTop: '0.4rem' }}>
                            Pending Manager Sign-off
                          </div>
                        )}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {!ob.is_manager_approved ? (
                           <button className="btn btn-primary" onClick={() => handleApproveManager(ob.id)} style={{ padding: '0.4rem 0.6rem' }}>
                             Sign-off
                           </button>
                        ) : (
                          <button className="btn btn-success" onClick={() => handleExecutePayment(ob)}>
                            <CheckCircle2 size={16} /> Execute
                          </button>
                        )}
                        <button className="btn btn-outline" title="Launch Negotiation Agent" onClick={() => handleNegotiate(ob)}>
                          <MessageSquare size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2>Agent Execution & Payment Audit Log</h2>
            <FileText size={20} color="var(--text-secondary)" />
          </div>
          <table className="mini-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Agent/Action</th>
                <th>Description</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {obligations.filter(o => o.status === 'paid').map((ob, idx) => (
                <tr key={idx}>
                  <td><small>{new Date().toLocaleTimeString()}</small></td>
                  <td><strong>Payment Executed</strong></td>
                  <td>Paid ₹{ob.amount.toLocaleString()} to {ob.vendor_name}</td>
                  <td><span className="badge low">Success</span></td>
                </tr>
              ))}
              {obligations.filter(o => o.status === 'paid').length === 0 && (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No recent executions recorded.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}

export default App;

