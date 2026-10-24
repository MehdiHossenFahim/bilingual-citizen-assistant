import React from 'react';
import { PlusCircle, Globe, ShieldCheck, Activity, ChevronLeft, User } from 'lucide-react';

export default function Sidebar({
  selectedLanguage,
  onLanguageChange,
  statusData,
  onOpenStatusModal,
  onNewChat,
  isOpen,
  onClose,
}) {
  const languages = [
    { code: 'auto', label: 'স্বয়ংক্রিয় (Auto-detect)' },
    { code: 'bn', label: 'বাংলা (Bangla)' },
    { code: 'en', label: 'English' },
  ];

  const handleLanguageSelect = (code) => {
    onLanguageChange(code);
    if (window.innerWidth <= 900 && onClose) {
      onClose();
    }
  };

  const handleNewChatClick = () => {
    onNewChat();
    if (window.innerWidth <= 900 && onClose) {
      onClose();
    }
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'collapsed'}`}>
      <div className="sidebar-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="logo-badge">🏛️</div>
          <div className="sidebar-title">
            <h1>নাগরিক সেবা সহকারী</h1>
            <p>Bilingual Public Services AI</p>
          </div>
        </div>

        <button
          className="sidebar-close-btn"
          onClick={onClose}
          title="সাইডবার লুকান (Collapse sidebar)"
          aria-label="Collapse sidebar"
        >
          <ChevronLeft size={20} />
        </button>
      </div>

      <div className="sidebar-content">
        {/* Language Selection */}
        <div>
          <div className="section-label">উত্তর দেওয়ার ভাষা (Language)</div>
          <div className="lang-select-group">
            {languages.map((lang) => (
              <div
                key={lang.code}
                className={`lang-option ${selectedLanguage === lang.code ? 'active' : ''}`}
                onClick={() => handleLanguageSelect(lang.code)}
              >
                <span>{lang.label}</span>
                {selectedLanguage === lang.code && <Globe size={16} color="#006a4e" />}
              </div>
            ))}
          </div>
        </div>

        {/* Covered Services */}
        <div>
          <div className="section-label">অন্তর্ভুক্ত সরকারি সেবা (Services)</div>
          <div className="services-list">
            <div className="service-item">
              <span>🛂</span>
              <div>
                <strong>পাসপোর্ট (Passport)</strong>
                <div style={{ fontSize: '0.72rem', color: '#64748b' }}>ই-পাসপোর্ট, নবায়ন ও ফি নির্দেশিকা</div>
              </div>
            </div>
            <div className="service-item">
              <span>🪪</span>
              <div>
                <strong>জাতীয় পরিচয়পত্র (NID)</strong>
                <div style={{ fontSize: '0.72rem', color: '#64748b' }}>সংশোধন, হারিয়ে যাওয়া ও নতুন ভোটার</div>
              </div>
            </div>
            <div className="service-item">
              <span>📑</span>
              <div>
                <strong>ই-টিন (e-TIN)</strong>
                <div style={{ fontSize: '0.72rem', color: '#64748b' }}>কর সনদ নিবন্ধন ও তথ্য পুনরুদ্ধার</div>
              </div>
            </div>
          </div>
        </div>

        {/* Live System Status Card */}
        <div>
          <div className="section-label">সার্ভার সংযোগ অবস্থা</div>
          <div className="status-card" onClick={onOpenStatusModal} style={{ cursor: 'pointer' }}>
            <div className="status-indicator">
              <span className={`dot ${statusData.online ? (statusData.ready ? 'online' : 'warning') : 'offline'}`} />
              <span style={{ fontWeight: 600 }}>
                {statusData.online
                  ? statusData.ready
                    ? 'অনলাইন ও সক্রিয়'
                    : 'প্রস্তুত হচ্ছে...'
                  : 'সংযোগ বিচ্ছিন্ন (Offline)'}
              </span>
            </div>

            <div className="status-details">
              <div>BM25 ইনডেক্স: {statusData.checks?.bm25_index || 'checking...'}</div>
              <div>ChromaDB ভেক্টর: {statusData.checks?.dense_index || 'checking...'}</div>
              <div>LangGraph পাইপলাইন: {statusData.checks?.workflow || 'checking...'}</div>
            </div>

            <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#006a4e', fontWeight: 600 }}>
              ডায়াগনস্টিকস ও পিং বিস্তারিত দেখুন →
            </div>
          </div>
        </div>

        {/* Authority Trust Badge */}
        <div style={{
          marginTop: 'auto',
          padding: '12px',
          background: '#f8fafc',
          borderRadius: '8px',
          border: '1px solid #e2e8f0',
          fontSize: '0.75rem',
          color: '#475569',
          display: 'flex',
          gap: '8px',
          alignItems: 'flex-start'
        }}>
          <ShieldCheck size={18} color="#006a4e" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong>যাচাইকৃত সরকারি তথ্যভাণ্ডার:</strong> DIP, নির্বাচন কমিশন (EC) এবং এনবিআর (NBR) এর অফিসিয়াল পোর্টাল থেকে সংগৃহীত।
          </div>
        </div>
      </div>

      <div className="sidebar-footer">
        <button className="btn-new-chat" onClick={handleNewChatClick}>
          <PlusCircle size={18} />
          <span>নতুন চ্যাট শুরু করুন</span>
        </button>

        {/* Developer Attribution */}
        <div className="sidebar-dev-credit">
          <User size={13} color="#006a4e" />
          <span>Developed by: <strong>Mehedi Hossen Fahim</strong></span>
        </div>
      </div>
    </aside>
  );
}
