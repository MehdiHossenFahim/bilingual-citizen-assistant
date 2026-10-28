import React from 'react';
import { X, RefreshCw, CheckCircle2, AlertCircle, ExternalLink, Activity } from 'lucide-react';

export default function SystemStatusModal({ isOpen, onClose, statusData, onRefresh, t, theme }) {
  if (!isOpen) return null;

  const primaryIconColor = theme === 'dark' ? '#10b981' : '#006a4e';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color={primaryIconColor} />
            <h3 className="modal-title">{t.modalTitle}</h3>
          </div>
          <button className="btn-close" onClick={onClose} aria-label="Close modal">
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.9rem' }}>
          <div>
            <div className="section-label">{t.modalServerStatus}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              {statusData.online ? (
                <>
                  <CheckCircle2 size={18} color={theme === 'dark' ? '#34d399' : '#22c55e'} />
                  <span className="status-text-ok">{t.modalServerConnected}</span>
                  <span className="status-text-muted">({statusData.latency_ms} ms ping)</span>
                </>
              ) : (
                <>
                  <AlertCircle size={18} color="#ef4444" />
                  <span className="status-text-err">{t.modalServerDisconnected}</span>
                </>
              )}
            </div>
            {statusData.error && (
              <div className="status-text-err" style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                {t.modalError} {statusData.error}
              </div>
            )}
          </div>

          <div>
            <div className="section-label">{t.modalChecksTitle}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
              <div className="service-item">
                <span>{t.modalCheckBM25}</span>
                <strong className={statusData.checks?.bm25_index === 'ok' ? 'status-text-ok' : 'status-text-warn'}>
                  {statusData.checks?.bm25_index || 'checking...'}
                </strong>
              </div>
              <div className="service-item">
                <span>{t.modalCheckDense}</span>
                <strong className={statusData.checks?.dense_index === 'ok' ? 'status-text-ok' : 'status-text-warn'}>
                  {statusData.checks?.dense_index || 'checking...'}
                </strong>
              </div>
              <div className="service-item">
                <span>{t.modalCheckWorkflow}</span>
                <strong className={statusData.checks?.workflow === 'ok' ? 'status-text-ok' : 'status-text-warn'}>
                  {statusData.checks?.workflow || 'checking...'}
                </strong>
              </div>
            </div>
          </div>

          <div>
            <div className="section-label">{t.modalEndpointsTitle}</div>
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
              className="modal-doc-link"
            >
              <span>{t.modalOpenSwagger}</span>
              <ExternalLink size={14} />
            </a>

            <button
              onClick={onRefresh}
              disabled={statusData.checking}
              className="modal-refresh-btn"
            >
              <RefreshCw size={14} className={statusData.checking ? "spinner" : ""} />
              <span>{statusData.checking ? t.modalRechecking : t.modalRecheck}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
