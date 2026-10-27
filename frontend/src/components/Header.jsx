import React from 'react';
import { Activity, Menu, PanelLeftClose, PanelLeft, ExternalLink, ShieldCheck, Landmark } from 'lucide-react';

export default function Header({
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
          title={sidebarOpen ? "সাইডবার লুকান (Collapse sidebar)" : "সাইডবার খুলুন (Open sidebar)"}
          aria-label="Toggle Sidebar"
        >
          {sidebarOpen ? <PanelLeftClose size={19} /> : <PanelLeft size={19} />}
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
        <a
          href={`${statusData.backendUrl || 'http://localhost:8000'}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="nav-api-link"
          title="FastAPI Swagger Documentation"
        >
          <span>API Docs</span>
          <ExternalLink size={13} />
        </a>

        <button
          onClick={onOpenStatusModal}
          className="health-badge-btn"
          style={{
            background: statusData.online ? '#f0fdf4' : '#fef2f2',
            borderColor: statusData.online ? '#bbf7d0' : '#fecaca',
            color: statusData.online ? '#15803d' : '#b91c1c',
          }}
          title="সিস্টেম স্ট্যাটাস ও লাইভ ডায়াগনস্টিকস"
        >
          <span className={`dot ${statusData.online ? (statusData.ready ? 'online' : 'warning') : 'offline'}`} />
          <span className="status-text">
            {statusData.online ? (statusData.ready ? 'অনলাইন' : 'লোড হচ্ছে') : 'অফলাইন'}
          </span>
          {statusData.latency_ms && statusData.online && (
            <span className="ping-text">{statusData.latency_ms}ms</span>
          )}
          <Activity size={13} style={{ marginLeft: '2px' }} />
        </button>
      </div>
    </header>
  );
}
