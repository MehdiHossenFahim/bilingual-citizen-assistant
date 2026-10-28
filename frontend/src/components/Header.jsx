import React from 'react';
import { PanelLeft, PanelLeftClose, Activity, Landmark, Globe, Sun, Moon } from 'lucide-react';

export default function Header({
  t,
  uiLang,
  onToggleUiLang,
  theme,
  onToggleTheme,
  statusData,
  onOpenStatusModal,
  sidebarOpen,
  onToggleSidebar,
}) {
  return (
    <header className="top-navbar">
      <div className="top-navbar-left">
        <button
          className="sidebar-toggle-btn"
          onClick={onToggleSidebar}
          title={sidebarOpen ? t.sidebarToggleClose : t.sidebarToggleOpen}
          aria-label="Toggle Sidebar"
        >
          {sidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeft size={20} />}
        </button>

        <div className="top-navbar-brand">
          <div className="brand-badge">
            <Landmark size={20} color={theme === 'dark' ? '#10b981' : '#006a4e'} />
          </div>
          <div className="brand-text">
            <div className="brand-title">
              <h1>{t.brandTitle}</h1>
              <span className="badge-tag">{t.versionBadge}</span>
            </div>
            <p className="brand-subtitle">{t.brandSubtitle}</p>
          </div>
        </div>
      </div>

      <div className="top-navbar-right">
        {/* Website Language Switcher (Bangla <-> English) */}
        <button
          className="nav-btn nav-lang-btn"
          onClick={onToggleUiLang}
          title={t.navLangBtnTitle}
          aria-label="Switch website language"
        >
          <Globe size={15} />
          <span className="nav-btn-text">{uiLang === 'bn' ? 'English' : 'বাংলা'}</span>
        </button>

        {/* Theme Toggle (Dark / Light) */}
        <button
          className="nav-btn nav-theme-btn"
          onClick={onToggleTheme}
          title={theme === 'dark' ? t.themeLightTitle : t.themeDarkTitle}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* Live System Health Indicator */}
        <button
          onClick={onOpenStatusModal}
          className="health-badge-btn"
          style={{
            background: statusData.online
              ? (theme === 'dark' ? 'rgba(16, 185, 129, 0.15)' : '#f0fdf4')
              : (theme === 'dark' ? 'rgba(239, 68, 68, 0.15)' : '#fef2f2'),
            borderColor: statusData.online
              ? (theme === 'dark' ? '#059669' : '#bbf7d0')
              : (theme === 'dark' ? '#b91c1c' : '#fecaca'),
            color: statusData.online
              ? (theme === 'dark' ? '#34d399' : '#15803d')
              : (theme === 'dark' ? '#f87171' : '#b91c1c'),
          }}
          title={t.systemStatusTitle}
        >
          <span className={`dot ${statusData.online ? (statusData.ready ? 'online' : 'warning') : 'offline'}`} />
          <span className="status-text">
            {statusData.online ? (statusData.ready ? t.systemOnline : t.systemLoading) : t.systemOffline}
          </span>
          {statusData.latency_ms && statusData.online && (
            <span className="ping-text">{statusData.latency_ms}ms</span>
          )}
          <Activity size={13} style={{ marginLeft: '2px', opacity: 0.8 }} />
        </button>
      </div>
    </header>
  );
}
