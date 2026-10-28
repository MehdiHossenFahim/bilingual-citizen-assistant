import React, { useState, useEffect, useRef } from 'react';
import { Send, ArrowDown, Landmark } from 'lucide-react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatMessage from './components/ChatMessage';
import ExampleQuestions from './components/ExampleQuestions';
import SystemStatusModal from './components/SystemStatusModal';
import { translations } from './i18n';
import { useTypewriterPlaceholder } from './hooks/useTypewriterPlaceholder';

const getBackendUrl = () => {
  if (import.meta.env.VITE_BACKEND_URL) {
    return import.meta.env.VITE_BACKEND_URL.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') {
      return 'http://localhost:8000';
    }
  }
  return 'https://bilingual-citizen-assistant.onrender.com';
};

const BACKEND_URL = getBackendUrl();
const CHAT_ENDPOINT = `${BACKEND_URL}/api/v1/chat`;
const FEEDBACK_ENDPOINT = `${BACKEND_URL}/api/v1/feedback`;
const HEALTH_ENDPOINT = `${BACKEND_URL}/health`;
const READY_ENDPOINT = `${BACKEND_URL}/ready`;

// Resilient API client: tries relative path first (Vercel edge proxy / Vite dev proxy)
// and seamlessly falls back to direct BACKEND_URL if needed.
const apiFetch = async (path, options = {}) => {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return fetch(path, options);
  }

  // 1. Try relative path (same-origin, avoids CORS & mobile tracker blocking on Vercel)
  try {
    const res = await fetch(path, options);
    // If the proxy handled it (even 4xx/5xx from API), return it
    if (res.status !== 404) {
      return res;
    }
  } catch (err) {
    // If network or relative fetch failed, proceed to direct URL fallback
  }

  // 2. Direct backend fallback
  const directUrl = `${BACKEND_URL}${path.startsWith('/') ? path : '/' + path}`;
  return fetch(directUrl, options);
};

export default function App() {
  const [messages, setMessages] = useState(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('app_chat_messages');
        if (saved) return JSON.parse(saved);
      } catch (err) {
        // Fallback to empty if parse fails
      }
    }
    return [];
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');

  // Persist messages across page reloads
  useEffect(() => {
    try {
      if (messages && messages.length > 0) {
        localStorage.setItem('app_chat_messages', JSON.stringify(messages));
      } else {
        localStorage.removeItem('app_chat_messages');
      }
    } catch (err) {
      // Ignore storage quota errors
    }
  }, [messages]);
  // Website UI Language (Bangla <-> English)
  const [uiLang, setUiLang] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('app_ui_lang') || 'bn';
    }
    return 'bn';
  });

  useEffect(() => {
    localStorage.setItem('app_ui_lang', uiLang);
  }, [uiLang]);

  const handleToggleUiLang = () => {
    setUiLang((prev) => (prev === 'bn' ? 'en' : 'bn'));
  };

  const t = translations[uiLang] || translations.bn;

  // Animated rotating placeholder for the input box
  const animatedPlaceholder = useTypewriterPlaceholder(t.placeholderPhrases, {
    enabled: !loading && input.length === 0,
    typingSpeed: 45,
    deletingSpeed: 25,
    pauseDuration: 2200,
  });

  // Model response generation language preference (auto / bn / en)
  const [language, setLanguage] = useState('auto');
  const [sessionId] = useState(() => 'sess_' + Math.random().toString(36).substring(2, 12));
  // Full-screen chat by default, matching Gemini / ChatGPT UX
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('app_theme') || 'light';
    }
    return 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app_theme', theme);
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };
  const [statusData, setStatusData] = useState({
    online: false,
    ready: false,
    checking: false,
    latency_ms: null,
    checks: {},
    error: null,
    backendUrl: BACKEND_URL || 'http://localhost:8000',
  });

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom on messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Poll backend health on mount
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    setStatusData((prev) => ({ ...prev, checking: true }));
    const t0 = performance.now();
    try {
      // 45s timeout: comfortably allows Render free tier to wake up from cold start (~45-60s)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 45000);
      const resHealth = await apiFetch('/health', { method: 'GET', signal: controller.signal });
      clearTimeout(timeoutId);
      const latency = Math.round(performance.now() - t0);

      if (resHealth.ok) {
        let ready = true;
        let checks = { bm25_index: 'ok', dense_index: 'ok', workflow: 'ok' };
        try {
          const rController = new AbortController();
          const rTimeoutId = setTimeout(() => rController.abort(), 12000);
          const resReady = await apiFetch('/ready', { method: 'GET', signal: rController.signal });
          clearTimeout(rTimeoutId);
          if (resReady.ok) {
            const dataReady = await resReady.json();
            ready = dataReady.ready;
            checks = dataReady.checks || checks;
          }
        } catch {
          // If /ready has transient latency, /health is already confirmed ok
        }

        setStatusData({
          online: true,
          ready,
          checking: false,
          latency_ms: latency,
          checks,
          error: null,
          backendUrl: BACKEND_URL || 'http://localhost:8000',
        });
      } else {
        setStatusData((prev) => ({
          ...prev,
          online: false,
          ready: false,
          checking: false,
          error: `Health check returned HTTP ${resHealth.status}`,
        }));
      }
    } catch (err) {
      setStatusData((prev) => {
        if (prev.online && err.name === 'AbortError') {
          return { ...prev, checking: false };
        }
        return {
          ...prev,
          online: false,
          ready: false,
          checking: false,
          error: err.name === 'AbortError' 
            ? 'Ping timed out (Render free tier waking up, please wait ~45s)' 
            : (err.message || 'Cannot connect to backend'),
        };
      });
    }
  };

  const handleSendMessage = async (queryText) => {
    const query = (queryText || input).trim();
    if (!query || loading) return;

    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Append user message
    const userMsg = {
      id: 'msg_' + Date.now(),
      role: 'user',
      content: query,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setLoadingStatus('সরকারি তথ্যভাণ্ডার অনুসন্ধান ও প্রাসঙ্গিক প্রমাণ যাচাই করা হচ্ছে...');

    const tStart = performance.now();

    // 300s timeout controller for CPU model inference
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000);

    try {
      setLoadingStatus('ভাষাগত বিশ্লেষণ ও হাইব্রিড সার্চ (BM25 + BGE-M3 Dense)...');

      const response = await apiFetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          query,
          language,
          session_id: sessionId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const elapsed = Math.round(performance.now() - tStart);

      if (response.ok) {
        const data = await response.json();
        const latency = data.latency_ms || elapsed;
        const assistantMsg = {
          id: 'msg_' + Date.now(),
          role: 'assistant',
          content: data.answer || '',
          citations: data.citations || [],
          limitations: data.limitations || [],
          status: data.status || 'answered',
          latency_ms: latency,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        // Sync live connection state: a successful chat response proves the backend is online and ready
        setStatusData((prev) => ({
          ...prev,
          online: true,
          ready: true,
          latency_ms: Math.round(latency),
          checks: { bm25_index: 'ok', dense_index: 'ok', workflow: 'ok' },
          error: null,
          backendUrl: BACKEND_URL || 'http://localhost:8000',
        }));
      } else {
        let errDetails = null;
        try {
          errDetails = await response.json();
        } catch {
          errDetails = { raw_body: await response.text() };
        }

        let userFriendlyError = `সার্ভার থেকে ত্রুটি এসেছে (HTTP ${response.status})`;
        if (response.status === 503) {
          userFriendlyError = 'সার্ভার এখনো প্রস্তুত নয় (Service Not Ready)। ব্যাকএন্ডের নলেজ বেস ইনডেক্স লোড হচ্ছে, অনুগ্রহ করে কয়েক সেকেন্ড পর আবার চেষ্টা করুন।';
        } else if (response.status === 422) {
          userFriendlyError = 'অনুরোধের তথ্য সঠিক নয় (Validation Error)। অনুগ্রহ করে আপনার প্রশ্নটি যাচাই করুন।';
        }

        const errorMsg = {
          id: 'msg_' + Date.now(),
          role: 'assistant',
          content: userFriendlyError,
          status: 'error',
          latency_ms: elapsed,
          error_details: {
            http_status: response.status,
            endpoint: CHAT_ENDPOINT,
            details: errDetails,
          },
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    } catch (err) {
      clearTimeout(timeoutId);
      const elapsed = Math.round(performance.now() - tStart);

      let errorText = `একটি কারিগরি ত্রুটি ঘটেছে: ${err.message}`;
      let errorDetails = { error_name: err.name, message: err.message };

      if (err.name === 'AbortError') {
        errorText = 'অনুরোধটির সময় শেষ হয়েছে (Request Timed Out after 300s)। ব্যাকএন্ডে প্রথমবার BGE মডেল ডাউনলোড বা CPU ইনফারেন্সে সময় লাগতে পারে। মডেল এখন মেমোরিতে রয়েছে, অনুগ্রহ করে পুনরায় প্রশ্নটি পাঠান।';
        errorDetails = {
          reason: 'Client-side 300s timeout reached',
          tip: 'First query initiates model weights. Retry now for faster response.',
        };
      } else if (err.message && err.message.includes('Failed to fetch')) {
        errorText = `সার্ভারের সাথে সংযোগ করা যায়নি (${BACKEND_URL || 'http://localhost:8000'})। ব্যাকএন্ড কন্টেইনার বা সার্ভিস চালু আছে কি না পরীক্ষা করুন।`;
        errorDetails = {
          endpoint: CHAT_ENDPOINT,
          hint: 'Ensure FastAPI backend is running and reachable.',
        };
      }

      const errorMsg = {
        id: 'msg_' + Date.now(),
        role: 'assistant',
        content: errorText,
        status: 'error',
        latency_ms: elapsed,
        error_details: errorDetails,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      setLoadingStatus('');
    }
  };

  const handleFeedback = async (message, rating) => {
    // Optimistic UI update
    setMessages((prev) =>
      prev.map((m) => (m.id === message.id ? { ...m, feedback: rating } : m))
    );

    try {
      // Calculate simple hash of message content or query
      const queryHash = btoa(encodeURIComponent(message.content.substring(0, 60))).substring(0, 32);

      await apiFetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          query_hash: queryHash,
          rating,
          comment: `Client rating: ${rating}`,
        }),
      });
    } catch {
      // feedback failure is silent
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTextareaInput = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
  };

  const handleNewChat = () => {
    setMessages([]);
    setInput('');
    try {
      localStorage.removeItem('app_chat_messages');
    } catch (err) {
      // Ignore storage errors
    }
  };

  return (
    <div className="app-container">
      {/* Mobile Backdrop */}
      <div
        className={`sidebar-backdrop ${sidebarOpen ? 'active' : ''}`}
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />

      {/* Left Sidebar */}
      <Sidebar
        t={t}
        theme={theme}
        selectedLanguage={language}
        onLanguageChange={setLanguage}
        statusData={statusData}
        onOpenStatusModal={() => setStatusModalOpen(true)}
        onNewChat={handleNewChat}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Chat Workspace */}
      <main className="chat-main">
        <Header
          t={t}
          uiLang={uiLang}
          onToggleUiLang={handleToggleUiLang}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          statusData={statusData}
          onOpenStatusModal={() => setStatusModalOpen(true)}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
          onNewChat={handleNewChat}
        />

        {/* Outer scroll container spanning full width (100%) so the scrollbar sits at the far right edge of the viewport like ChatGPT */}
        <div className="messages-scroll-area">
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="welcome-container">
                <div className="welcome-icon">
                  <Landmark size={36} color={theme === 'dark' ? '#10b981' : '#006a4e'} />
                </div>
                <h2 className="welcome-heading">{t.welcomeHeading}</h2>
                <p className="welcome-subtext">{t.welcomeSubtext}</p>

                <div style={{ width: '100%', marginTop: '16px' }}>
                  <div className="section-label" style={{ textAlign: 'center' }}>
                    {t.examplesHeading}
                  </div>
                  <ExampleQuestions examples={t.examples} onSelect={(q) => handleSendMessage(q)} />
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onFeedback={handleFeedback}
                  t={t}
                  theme={theme}
                />
              ))
            )}

            {/* Loading Shimmer / Typing Indicator */}
            {loading && (
              <div className="message-row assistant">
                <div className="avatar bot-avatar">
                  <Landmark size={18} color={theme === 'dark' ? '#10b981' : '#006a4e'} />
                </div>
                <div className="loading-box">
                  <div className="spinner" />
                  <span>{loadingStatus || t.loadingAnswer}</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Sticky Bottom Input Bar */}
        <div className="input-area-wrapper">
          <div className="input-box-container">
            <textarea
              ref={textareaRef}
              rows={1}
              className="chat-textarea"
              placeholder={animatedPlaceholder || t.inputPlaceholder}
              value={input}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button
              className="send-button"
              onClick={() => handleSendMessage()}
              disabled={!input.trim() || loading}
              title={t.sendTitle}
              aria-label="Send query"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="input-disclaimer">{t.inputDisclaimer}</p>
        </div>
      </main>

      {/* Diagnostics Modal */}
      <SystemStatusModal
        isOpen={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        statusData={statusData}
        onRefresh={checkHealth}
        t={t}
        theme={theme}
      />
    </div>
  );
}

