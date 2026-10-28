import React from 'react';
import { PlusCircle, Globe, ShieldCheck, Activity, ExternalLink, User, Landmark, Code, Server } from 'lucide-react';

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

  const docsUrl = `${statusData.backendUrl || 'https://bilingual-citizen-assistant.onrender.com'}/docs`;

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'collapsed'}`}>
      {/* Sidebar Header */}
      <div className="sidebar-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="logo-badge">
            <Landmark size={20} color="#006a4e" />
          </div>
          <div className="sidebar-title">
            <h1>নাগরিক সেবা সহকারী</h1>
            <p>Bilingual Public Services AI</p>
          </div>
        </div>
      </div>

      <div className="sidebar-content">
        {/* New Chat Primary Action (Top of sidebar like ChatGPT/Gemini) */}
        <div>
          <button className="btn-new-chat" onClick={handleNewChatClick}>
            <PlusCircle size={18} />
            <span>নতুন কথোপকথন শুরু করুন</span>
          </button>
        </div>

        {/* Language Selection */}
        <div>
          <div className="section-label">উত্তর দেওয়ার ভাষা (Language)</div>
          <div className="lang-select-group">
            {languages.map((lang) => (
              <div
                key={lang.code}
                className={`lang-option ${selectedLanguage === lang.code ? 'active' : ''}`}
                onClick={() => handleLanguageSelect(lang.code)}
                role="button"
                tabIndex={0}
              >
                <span>{lang.label}</span>
                {selectedLanguage === lang.code && <Globe size={16} color="#006a4e" />}
              </div>
            ))}
          </div>
        </div>

        {/* Developer & Technical Documentation (Option 1) */}
        <div>
          <div className="section-label">কারিগরি ও এপিআই রিসোর্স (Developer)</div>
          <div className="sidebar-menu-links">
            <a
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="sidebar-menu-item"
              title="FastAPI Swagger Documentation"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Code size={16} color="#006a4e" />
                <span>FastAPI Swagger Docs</span>
              </div>
              <ExternalLink size={13} color="#94a3b8" />
            </a>

            <div
              className="sidebar-menu-item"
              onClick={() => {
                onOpenStatusModal();
                if (window.innerWidth <= 900 && onClose) onClose();
              }}
              role="button"
              tabIndex={0}
              title="সিস্টেম স্বাস্থ্য ও ডায়াগনস্টিকস"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Server size={16} color="#006a4e" />
                <span>সিস্টেম ডায়াগনস্টিকস</span>
              </div>
              <span className={`dot ${statusData.online ? 'online' : 'offline'}`} />
            </div>
          </div>
        </div>

        {/* Verified Knowledge Base Notice (Informative, non-clickable) */}
        <div className="sidebar-trust-box">
          <ShieldCheck size={16} color="#006a4e" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong>যাচাইকৃত তথ্যভাণ্ডার:</strong> DIP (পাসপোর্ট), নির্বাচন কমিশন (NID) ও এনবিআর (TIN) এর সরকারি প্রকাশনা থেকে সংগৃহীত।
          </div>
        </div>
      </div>

      {/* Developer Attribution Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-dev-credit">
          <User size={13} color="#006a4e" />
          <span>Developed by: <strong>Mehedi Hossen Fahim</strong></span>
        </div>
      </div>
    </aside>
  );
}
