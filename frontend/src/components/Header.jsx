import React from 'react';
import { PanelLeft, PanelLeftClose, Activity, Landmark, Globe, Sun, Moon } from 'lucide-react';

export default function Header({
  statusData,
  onOpenStatusModal,
  sidebarOpen,
  onToggleSidebar,
  language,
  onToggleLanguage,
  theme,
  onToggleTheme,
}) {
  const getLanguageLabel = () => {
    if (language === 'bn') return 'বাংলা';
    if (language === 'en') return 'English';
    return 'স্বয়ংক্রিয়';
  };

  return (
    <header className="top-navbar">
      <div className="top-navbar-left">
        <button
          className="sidebar-toggle-btn"
          onClick={onToggleSidebar}
          title={sidebarOpen ? "সাইডবার লুকান (Collapse sidebar)" : "মেনু ও সেটিংস খুলুন (Open sidebar)"}
          aria-label="Toggle Sidebar"
        >
          {sidebarOpen ? <PanelLeftClose size={20} /> : <PanelLeft size={20} />}
        </button>

        <div className="top-navbar-brand">
          <div className="brand-badge">
            <Landmark size={20} color="#006a4e" />
          </div>
          <div className="brand-text">
            <div className="brand-title">
              <h1>বাংলাদেশ নাগরিক সেবা সহকারী</h1>
              <span className="badge-tag">v1.0 • Agentic RAG</span>
            </div>
            <p className="brand-subtitle">Bilingual Citizen Services AI • Passport, NID & e-TIN</p>
          </div>
        </div>
      </div>

      <div className="top-navbar-right">
        {/* Language Quick Toggle */}
        <button
          className="nav-btn nav-lang-btn"
          onClick={onToggleLanguage}
          title={`বর্তমান ভাষা: ${getLanguageLabel()} (ক্লিক করে পরিবর্তন করুন)`}
          aria-label="Toggle language"
        >
          <Globe size={15} />
          <span className="nav-btn-text">{getLanguageLabel()}</span>
        </button>

        {/* Theme Toggle (Dark / Light) */}
        <button
          className="nav-btn nav-theme-btn"
          onClick={onToggleTheme}
          title={theme === 'dark' ? "লাইট মোডে ফিরুন (Switch to Light Mode)" : "ডার্ক মোড চালু করুন (Switch to Dark Mode)"}
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
          title="সিস্টেম স্ট্যাটাস ও লাইভ ডায়াগনস্টিকস দেখুন"
        >
          <span className={`dot ${statusData.online ? (statusData.ready ? 'online' : 'warning') : 'offline'}`} />
          <span className="status-text">
            {statusData.online ? (statusData.ready ? 'সিস্টেম সক্রিয়' : 'লোড হচ্ছে') : 'সংযোগ বিচ্ছিন্ন'}
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
