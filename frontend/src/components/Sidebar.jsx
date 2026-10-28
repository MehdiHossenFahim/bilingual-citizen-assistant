import React from 'react';
import { PlusCircle, Globe, ShieldCheck, ExternalLink, User, Landmark, Code, Server } from 'lucide-react';

export default function Sidebar({
  t,
  theme,
  selectedLanguage,
  onLanguageChange,
  statusData,
  onOpenStatusModal,
  onNewChat,
  isOpen,
  onClose,
}) {
  const languages = [
    { code: 'auto', label: t.langAuto },
    { code: 'bn', label: t.langBn },
    { code: 'en', label: t.langEn },
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
  const primaryIconColor = theme === 'dark' ? '#10b981' : '#006a4e';

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'collapsed'}`}>
      {/* Sidebar Header */}
      <div className="sidebar-header">
        <div
          className="sidebar-header-brand"
          onClick={handleNewChatClick}
          role="button"
          tabIndex={0}
          title={t.newChat}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleNewChatClick();
            }
          }}
        >
          <div className="logo-badge">
            <Landmark size={20} color={primaryIconColor} />
          </div>
          <div className="sidebar-title">
            <h1>{t.brandTitle}</h1>
            <p>{t.brandSubtitle}</p>
          </div>
        </div>
      </div>

      <div className="sidebar-content">
        {/* New Chat Primary Action */}
        <div>
          <button className="btn-new-chat" onClick={handleNewChatClick}>
            <PlusCircle size={18} />
            <span>{t.newChat}</span>
          </button>
        </div>

        {/* Model Response Language Preference */}
        <div>
          <div className="section-label">{t.responseLangLabel}</div>
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
                {selectedLanguage === lang.code && <Globe size={16} color={primaryIconColor} />}
              </div>
            ))}
          </div>
        </div>

        {/* Developer & Technical Documentation */}
        <div>
          <div className="section-label">{t.devSectionLabel}</div>
          <div className="sidebar-menu-links">
            <a
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="sidebar-menu-item"
              title="FastAPI Swagger Documentation"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Code size={16} color={primaryIconColor} />
                <span>{t.swaggerDocs}</span>
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
              title={t.systemDiagnostics}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Server size={16} color={primaryIconColor} />
                <span>{t.systemDiagnostics}</span>
              </div>
              <span className={`dot ${statusData.online ? 'online' : 'offline'}`} />
            </div>
          </div>
        </div>

        {/* Verified Knowledge Base Notice */}
        <div className="sidebar-trust-box">
          <ShieldCheck size={16} color={primaryIconColor} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong>{t.trustBoxTitle}</strong> {t.trustBoxDesc}
          </div>
        </div>
      </div>

      {/* Developer Attribution Footer with link to Portfolio */}
      <div className="sidebar-footer">
        <a
          href="https://portfolio-mehedi-hossen-fahim.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
          className="sidebar-dev-credit"
          title="Mehedi Hossen Fahim — Portfolio"
        >
          <User size={13} color={primaryIconColor} />
          <span>Developed by: <strong>Mehedi Hossen Fahim</strong></span>
          <ExternalLink size={12} className="credit-ext-icon" />
        </a>
      </div>
    </aside>
  );
}
