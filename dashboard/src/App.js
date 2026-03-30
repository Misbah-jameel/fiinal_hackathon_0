import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5000';

function App() {
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [approvals, setApprovals] = useState([]);
  const [needsAction, setNeedsAction] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeTab, setActiveTab] = useState('approvals');

  // Fetch data
  const fetchData = async () => {
    try {
      const [statusRes, approvalsRes, needsActionRes] = await Promise.all([
        axios.get(`${API_BASE}/api/status`),
        axios.get(`${API_BASE}/api/approvals`),
        axios.get(`${API_BASE}/api/needs-action`),
      ]);

      setStatus(statusRes.data);
      setApprovals(approvalsRes.data);
      setNeedsAction(needsActionRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Handle approval
  const handleApprove = async (fileId) => {
    if (!window.confirm(`Approve this action?`)) return;
    
    try {
      await axios.post(`${API_BASE}/api/approve/${fileId}`);
      fetchData();
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to approve');
    }
  };

  // Handle rejection
  const handleReject = async (fileId) => {
    if (!window.confirm(`Reject this action?`)) return;
    
    try {
      await axios.post(`${API_BASE}/api/reject/${fileId}`);
      fetchData();
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to reject');
    }
  };

  // View file
  const viewFile = async (filename, folder) => {
    try {
      const res = await axios.get(`${API_BASE}/api/file/${folder}/${filename}`);
      setSelectedFile(res.data);
    } catch (error) {
      alert('Failed to load file');
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="spinner"></div>
          Loading Dashboard...
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>
          🤖 <span>AI Employee Dashboard</span>
        </h1>
        <div className="header-status">
          <span className={`dry-run-badge ${status?.dry_run ? 'active' : ''}`}>
            {status?.dry_run ? '🛡️ DRY RUN' : '⚡ LIVE'}
          </span>
          <button className="refresh-btn" onClick={fetchData}>
            🔄 Refresh
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card needs-action">
            <h3>Needs Action</h3>
            <div className="value">{status?.vault?.Needs_Action || 0}</div>
          </div>
          <div className="stat-card pending">
            <h3>Pending Approval</h3>
            <div className="value">{status?.vault?.Pending_Approval || 0}</div>
          </div>
          <div className="stat-card approved">
            <h3>Approved</h3>
            <div className="value">{status?.vault?.Approved || 0}</div>
          </div>
          <div className="stat-card done">
            <h3>Done</h3>
            <div className="value">{status?.vault?.Done || 0}</div>
          </div>
          <div className="stat-card audit">
            <h3>Audit (Today)</h3>
            <div className="value">{status?.audit?.today || 0}</div>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="dashboard-grid">
          {/* Left Column - Approvals & Needs Action */}
          <div className="panel">
            <div className="tabs">
              <button
                className={`tab ${activeTab === 'approvals' ? 'active' : ''}`}
                onClick={() => setActiveTab('approvals')}
              >
                ⏳ Pending Approvals ({approvals.length})
              </button>
              <button
                className={`tab ${activeTab === 'needs-action' ? 'active' : ''}`}
                onClick={() => setActiveTab('needs-action')}
              >
                📋 Needs Action ({needsAction.length})
              </button>
            </div>

            {activeTab === 'approvals' && (
              <div className="approval-list">
                {approvals.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">✅</div>
                    <p>No pending approvals</p>
                  </div>
                ) : (
                  approvals.map((item) => (
                    <div key={item.id} className="approval-item">
                      <h3>📄 {item.filename}</h3>
                      <p>{item.preview}</p>
                      <div className="approval-actions">
                        <button
                          className="btn btn-view"
                          onClick={() => viewFile(item.filename, 'Pending_Approval')}
                        >
                          👁️ View
                        </button>
                        <button
                          className="btn btn-approve"
                          onClick={() => handleApprove(item.id)}
                          disabled={status?.dry_run}
                        >
                          ✅ Approve
                        </button>
                        <button
                          className="btn btn-reject"
                          onClick={() => handleReject(item.id)}
                          disabled={status?.dry_run}
                        >
                          ❌ Reject
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}

            {activeTab === 'needs-action' && (
              <div className="approval-list">
                {needsAction.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-state-icon">🎉</div>
                    <p>All caught up!</p>
                  </div>
                ) : (
                  needsAction.map((item) => (
                    <div key={item.id} className="approval-item">
                      <h3>📄 {item.filename}</h3>
                      <p>{item.preview}</p>
                      <div className="approval-actions">
                        <button
                          className="btn btn-view"
                          onClick={() => viewFile(item.filename, 'Needs_Action')}
                        >
                          👁️ View
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Right Column - Watcher Health */}
          <div>
            <div className="panel" style={{ marginBottom: '1.5rem' }}>
              <h2>🔍 Watcher Health</h2>
              <div className="watcher-list">
                {Object.entries(status?.watchers || {}).map(([name, data]) => (
                  <div key={name} className="watcher-item">
                    <span style={{ textTransform: 'capitalize' }}>{name}</span>
                    <div className="watcher-status">
                      <span
                        className={`status-dot ${
                          data.status === 'online'
                            ? 'online'
                            : data.status === 'offline'
                            ? 'offline'
                            : 'unknown'
                        }`}
                      ></span>
                      <span style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.7)' }}>
                        {data.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <h2>📊 Quick Stats</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Inbox</span>
                  <span style={{ fontWeight: 'bold' }}>{status?.vault?.Inbox || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>In Progress</span>
                  <span style={{ fontWeight: 'bold' }}>{status?.vault?.In_Progress || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Plans</span>
                  <span style={{ fontWeight: 'bold' }}>{status?.vault?.Plans || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Rejected</span>
                  <span style={{ fontWeight: 'bold' }}>{status?.vault?.Rejected || 0}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Total Audit</span>
                  <span style={{ fontWeight: 'bold' }}>{status?.audit?.total || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* File View Modal */}
      {selectedFile && (
        <div className="modal-overlay" onClick={() => setSelectedFile(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>📄 {selectedFile.filename}</h2>
            <div className="modal-content">{selectedFile.content}</div>
            <button
              className="btn btn-view modal-close"
              onClick={() => setSelectedFile(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
