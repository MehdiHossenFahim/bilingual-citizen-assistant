import React, { useState } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  BookOpen,
  Info,
  Check,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import CitationCard from './CitationCard';

export default function ChatMessage({ message, onFeedback }) {
  const {
    role,
    content,
    citations = [],
    limitations = [],
    status = 'answered',
    latency_ms,
    error_details,
    feedback,
  } = message;

  const [citationsOpen, setCitationsOpen] = useState(citations.length > 0 && citations.length <= 3);
  const [showErrorTech, setShowErrorTech] = useState(false);

  const isUser = role === 'user';

  // Format assistant text with clean paragraph and list layout
  const formatText = (text) => {
    if (!text) return '';
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Heading 3
      if (line.startsWith('### ')) {
        return <h3 key={idx}>{line.replace('### ', '')}</h3>;
      }
      // Heading 2
      if (line.startsWith('## ')) {
        return <h3 key={idx}>{line.replace('## ', '')}</h3>;
      }
      // Bullet items
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        return (
          <div key={idx} style={{ paddingLeft: '14px', marginBottom: '4px' }}>
            • {line.trim().substring(2)}
          </div>
        );
      }
      // Numbered items
      if (/^\d+[\.\)।]\s/.test(line.trim())) {
        return (
          <div key={idx} style={{ paddingLeft: '14px', marginBottom: '4px' }}>
            {line.trim()}
          </div>
        );
      }
      if (line.trim() === '') {
        return <div key={idx} style={{ height: '8px' }} />;
      }
      return <p key={idx} style={{ marginBottom: '6px' }}>{line}</p>;
    });
  };

  return (
    <div className={`message-row ${role}`}>
      {!isUser && (
        <div className="avatar bot-avatar" title="Citizen Services AI">
          🏛️
        </div>
      )}

      <div className="message-bubble">
        {isUser ? (
          <div>{content}</div>
        ) : (
          <div>
            {/* Fallback warning banner if insufficient evidence */}
            {status === 'insufficient_evidence' && (
              <div className="fallback-banner">
                <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <strong>অপ্রতুল তথ্য (Insufficient Evidence):</strong>
                  <div style={{ marginTop: '4px' }}>{content}</div>
                </div>
              </div>
            )}

            {/* Error banner if an error occurred */}
            {status === 'error' && (
              <div className="error-banner">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertCircle size={18} />
                  <strong>ত্রুটি ঘটেছে (Error):</strong>
                </div>
                <div style={{ marginTop: '6px' }}>{content}</div>

                {error_details && (
                  <div style={{ marginTop: '10px' }}>
                    <button
                      className="btn-icon"
                      style={{ fontSize: '0.8rem', color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '4px' }}
                      onClick={() => setShowErrorTech(!showErrorTech)}
                    >
                      <span>কারিগরি বিবরণ (Diagnostics)</span>
                      {showErrorTech ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                    {showErrorTech && (
                      <pre className="diag-box" style={{ marginTop: '6px', maxHeight: '160px', overflowY: 'auto' }}>
                        {JSON.stringify(error_details, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Standard Answer */}
            {status !== 'insufficient_evidence' && status !== 'error' && (
              <div className="answer-text">{formatText(content)}</div>
            )}

            {/* Limitations Callout */}
            {limitations && limitations.length > 0 && (
              <div>
                {limitations.map((lim, idx) => (
                  <div key={idx} className="limitation-box">
                    <Info size={14} style={{ display: 'inline', marginRight: '6px' }} />
                    <span><b>সতর্কবার্তা:</b> {lim}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Citations Section */}
            {citations && citations.length > 0 && (
              <div className="citations-section">
                <div
                  className="citations-header"
                  onClick={() => setCitationsOpen(!citationsOpen)}
                >
                  <BookOpen size={16} />
                  <span>যাচাইকৃত সরকারি তথ্যসূত্র ({citations.length}টি সূত্র)</span>
                  {citationsOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>

                {citationsOpen && (
                  <div className="citations-list">
                    {citations.map((cit, idx) => (
                      <CitationCard key={cit.source_id || idx} citation={cit} index={idx + 1} />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Footer with Latency and Helpful/Not Helpful feedback */}
            <div className="message-meta">
              <div>
                {latency_ms && (
                  <span>⏱️ {latency_ms >= 1000 ? `${(latency_ms / 1000).toFixed(1)}s` : `${Math.round(latency_ms)}ms`}</span>
                )}
              </div>

              {status === 'answered' && (
                <div className="feedback-actions">
                  <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>উত্তরটি কি সহায়ক ছিল?</span>
                  <button
                    className={`btn-icon ${feedback === 'helpful' ? 'active' : ''}`}
                    onClick={() => onFeedback && onFeedback(message, 'helpful')}
                    title="সহায়ক (Helpful)"
                  >
                    <ThumbsUp size={14} />
                  </button>
                  <button
                    className={`btn-icon ${feedback === 'not_helpful' ? 'active' : ''}`}
                    onClick={() => onFeedback && onFeedback(message, 'not_helpful')}
                    title="সহায়ক নয় (Not Helpful)"
                  >
                    <ThumbsDown size={14} />
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <div className="avatar user-avatar" title="You">
          👤
        </div>
      )}
    </div>
  );
}

