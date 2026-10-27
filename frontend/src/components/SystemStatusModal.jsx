import React from 'react';
import { X, RefreshCw, CheckCircle2, AlertCircle, ExternalLink, Activity } from 'lucide-react';

export default function SystemStatusModal({ isOpen, onClose, statusData, onRefresh }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color="#006a4e" />
            <h3 className="modal-title">সিস্টেম ডায়াগনস্টিকস (System Status)</h3>
          </div>
          <button className="btn-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.9rem' }}>
          <div>
            <div className="section-label">API সার্ভার অবস্থা (Backend Server)</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              {statusData.online ? (
                <>
                  <CheckCircle2 size={18} color="#22c55e" />
                  <span style={{ fontWeight: 600, color: '#15803d' }}>অনলাইন (Connected)</span>
                  <span style={{ color: '#64748b', fontSize: '0.8rem' }}>({statusData.latency_ms} ms ping)</span>
                </>
              ) : (
                <>
                  <AlertCircle size={18} color="#ef4444" />
                  <span style={{ fontWeight: 600, color: '#b91c1c' }}>সংযোগ বিচ্ছিন্ন (Offline)</span>
                </>
              )}
            </div>
            {statusData.error && (
              <div style={{ color: '#b91c1c', fontSize: '0.8rem', marginTop: '4px' }}>
                ত্রুটি: {statusData.error}
              </div>
            )}
          </div>

          <div>
            <div className="section-label">নলেজ বেস ও ওয়ার্কফ্লো (Readiness Checks)</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
              <div className="service-item">
                <span>BM25 স্পার্স ইনডেক্স (BM25 Index):</span>
                <strong style={{ marginLeft: 'auto', color: statusData.checks?.bm25_index === 'ok' ? '#15803d' : '#f59e0b' }}>
                  {statusData.checks?.bm25_index || 'checking...'}
                </strong>
              </div>
              <div className="service-item">
                <span>ChromaDB ডেনস ভেক্টর (Dense Vectors):</span>
                <strong style={{ marginLeft: 'auto', color: statusData.checks?.dense_index === 'ok' ? '#15803d' : '#f59e0b' }}>
                  {statusData.checks?.dense_index || 'checking...'}
                </strong>
              </div>
              <div className="service-item">
                <span>LangGraph RAG পাইপলাইন (Workflow):</span>
                <strong style={{ marginLeft: 'auto', color: statusData.checks?.workflow === 'ok' ? '#15803d' : '#f59e0b' }}>
                  {statusData.checks?.workflow || 'checking...'}
                </strong>
              </div>
            </div>
          </div>

          <div>
            <div className="section-label">এন্ডপয়েন্ট কনফিগারেশন (Target Endpoints)</div>
            <pre className="diag-box" style={{ marginTop: '4px' }}>
              Base API: {statusData.backendUrl || 'http://localhost:8000'}{'\n'}
              Chat:     /api/v1/chat{'\n'}
              Health:   /health{'\n'}
              Readiness:/ready
            </pre>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
            <a
              href={`${statusData.backendUrl || 'http://localhost:8000'}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#006a4e', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.85rem', fontWeight: 600 }}
            >
              <span>Swagger API Docs খুলুন</span>
              <ExternalLink size={14} />
            </a>

            <button
              onClick={onRefresh}
              disabled={statusData.checking}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                background: statusData.checking ? '#f1f5f9' : '#ffffff',
                cursor: statusData.checking ? 'not-allowed' : 'pointer',
                fontSize: '0.85rem',
              }}
            >
              <RefreshCw size={14} className={statusData.checking ? "spinner" : ""} />
              <span>{statusData.checking ? 'যাচাই করা হচ্ছে...' : 'পুনরায় পরীক্ষা'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

