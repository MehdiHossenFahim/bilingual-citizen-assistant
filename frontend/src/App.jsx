import React, { useState, useEffect, useRef } from 'react';
import { Send, ArrowDown } from 'lucide-react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatMessage from './components/ChatMessage';
import ExampleQuestions from './components/ExampleQuestions';
import SystemStatusModal from './components/SystemStatusModal';

const BACKEND_URL = (import.meta.env.VITE_BACKEND_URL || '').replace(/\/$/, '');
const CHAT_ENDPOINT = `${BACKEND_URL}/api/v1/chat`;
const FEEDBACK_ENDPOINT = `${BACKEND_URL}/api/v1/feedback`;
const HEALTH_ENDPOINT = `${BACKEND_URL}/health`;
const READY_ENDPOINT = `${BACKEND_URL}/ready`;

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [language, setLanguage] = useState('auto');
  const [sessionId] = useState(() => 'sess_' + Math.random().toString(36).substring(2, 12));
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth > 960;
    }
    return true;
  });
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [statusData, setStatusData] = useState({
    online: false,
    ready: false,
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
    const t0 = performance.now();
    try {
      const resHealth = await fetch(HEALTH_ENDPOINT, { method: 'GET' });
      const latency = Math.round(performance.now() - t0);

      if (resHealth.ok) {
        let ready = false;
        let checks = {};
        try {
          const resReady = await fetch(READY_ENDPOINT, { method: 'GET' });
          if (resReady.ok) {
            const dataReady = await resReady.json();
            ready = dataReady.ready;
            checks = dataReady.checks || {};
          }
        } catch {
          // ready endpoint error
        }

        setStatusData({
          online: true,
          ready,
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
          error: `Health check returned HTTP ${resHealth.status}`,
        }));
      }
    } catch (err) {
      setStatusData((prev) => ({
        ...prev,
        online: false,
        ready: false,
        error: err.message || 'Cannot connect to backend',
      }));
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

      const response = await fetch(CHAT_ENDPOINT, {
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
        const assistantMsg = {
          id: 'msg_' + Date.now(),
          role: 'assistant',
          content: data.answer || '',
          citations: data.citations || [],
          limitations: data.limitations || [],
          status: data.status || 'answered',
          latency_ms: data.latency_ms || elapsed,
        };
        setMessages((prev) => [...prev, assistantMsg]);
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

      await fetch(FEEDBACK_ENDPOINT, {
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
          statusData={statusData}
          onOpenStatusModal={() => setStatusModalOpen(true)}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        />

        {/* Messages Stream */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-container">
              <div className="welcome-icon">🏛️</div>
              <h2 className="welcome-heading">বাংলাদেশ নাগরিক সেবা সহকারী</h2>
              <p className="welcome-subtext">
                পাসপোর্ট, জাতীয় পরিচয়পত্র (NID) অথবা ই-টিন (TIN) সংক্রান্ত যেকোনো সরকারি সেবা সম্পর্কে নির্ভরযোগ্য নির্দেশনা পান।
              </p>

              <div style={{ width: '100%', marginTop: '16px' }}>
                <div className="section-label" style={{ textAlign: 'center' }}>
                  💡 উদাহরণ প্রশ্নসমূহ (সরাসরি ক্লিক করে জানতে পারেন)
                </div>
                <ExampleQuestions onSelect={(q) => handleSendMessage(q)} />
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onFeedback={handleFeedback}
              />
            ))
          )}

          {/* Loading Shimmer / Typing Indicator */}
          {loading && (
            <div className="message-row assistant">
              <div className="avatar bot-avatar">🏛️</div>
              <div className="loading-box">
                <div className="spinner" />
                <span>{loadingStatus || 'সরকারি তথ্য অনুসন্ধান ও উত্তর তৈরি করা হচ্ছে...'}</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Sticky Input Bar */}
        <div className="input-area-wrapper">
          <div className="input-box-container">
            <textarea
              ref={textareaRef}
              rows={1}
              className="chat-textarea"
              placeholder="আপনার প্রশ্ন লিখুন... (Enter চাপলে পাঠানো হবে, e.g. পাসপোর্ট করতে কী কী কাগজ লাগে?)"
              value={input}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button
              className="send-button"
              onClick={() => handleSendMessage()}
              disabled={!input.trim() || loading}
              title="পাঠান (Send)"
            >
              <Send size={18} />
            </button>
          </div>
          <div className="input-disclaimer">
            * এটি একটি এআই পরিচালিত নাগরিক সেবা সহকারী। গুরুত্বপূর্ণ লেনদেনের পূর্বে সংশ্লিষ্ট সরকারি কর্তৃপক্ষ থেকে তথ্য যাচাই করার পরামর্শ দেওয়া হচ্ছে।
          </div>
          <footer className="workspace-footer">
            <span>© 2026 Bilingual Citizen Services AI Assistant • Developed by <strong>Mehedi Hossen Fahim</strong></span>
          </footer>
        </div>
      </main>

      {/* Diagnostics Modal */}
      <SystemStatusModal
        isOpen={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        statusData={statusData}
        onRefresh={checkHealth}
      />
    </div>
  );
}

