// Bilingual Citizen Services AI - UI Internationalization (i18n)
// Clean translations without any emojis.

export const translations = {
  bn: {
    // Header
    brandTitle: 'বাংলাদেশ নাগরিক সেবা সহকারী',
    brandSubtitle: 'Bilingual Citizen Services AI • Passport, NID & e-TIN',
    versionBadge: 'v1.0 • Agentic RAG',
    navLangBtnTitle: 'Switch website to English',
    navLangBtnLabel: 'EN',
    themeLightTitle: 'লাইট মোডে ফিরুন (Switch to Light Mode)',
    themeDarkTitle: 'ডার্ক মোড চালু করুন (Switch to Dark Mode)',
    systemOnline: 'সিস্টেম সক্রিয়',
    systemLoading: 'লোড হচ্ছে',
    systemOffline: 'সংযোগ বিচ্ছিন্ন',
    systemStatusTitle: 'সিস্টেম স্ট্যাটাস ও লাইভ ডায়াগনস্টিকস দেখুন',
    sidebarToggleOpen: 'মেনু ও সেটিংস খুলুন (Open sidebar)',
    sidebarToggleClose: 'সাইডবার লুকান (Collapse sidebar)',

    // Sidebar
    newChat: 'নতুন কথোপকথন শুরু করুন',
    responseLangLabel: 'উত্তর দেওয়ার ভাষা (Response Language)',
    langAuto: 'স্বয়ংক্রিয় (Auto-detect)',
    langBn: 'বাংলা (Bangla)',
    langEn: 'English',
    devSectionLabel: 'কারিগরি ও এপিআই রিসোর্স (Developer)',
    swaggerDocs: 'FastAPI Swagger Docs',
    systemDiagnostics: 'সিস্টেম ডায়াগনস্টিকস',
    trustBoxTitle: 'যাচাইকৃত তথ্যভাণ্ডার:',
    trustBoxDesc: 'DIP (পাসপোর্ট), নির্বাচন কমিশন (NID) ও এনবিআর (TIN) এর সরকারি প্রকাশনা থেকে সংগৃহীত।',
    developedBy: 'Developed by: Mehedi Hossen Fahim',

    // Welcome Screen
    welcomeHeading: 'বাংলাদেশ নাগরিক সেবা সহকারী',
    welcomeSubtext: 'পাসপোর্ট, জাতীয় পরিচয়পত্র (NID) অথবা ই-টিন (TIN) সংক্রান্ত যেকোনো সরকারি সেবা সম্পর্কে নির্ভরযোগ্য নির্দেশনা পান।',
    examplesHeading: 'উদাহরণ প্রশ্নসমূহ (সরাসরি ক্লিক করে জানতে পারেন)',

    // Chat & Input
    inputPlaceholder: 'আপনার প্রশ্ন লিখুন... (Enter চাপলে পাঠানো হবে, e.g. পাসপোর্ট করতে কী কী কাগজ লাগে?)',
    sendTitle: 'পাঠান (Send)',
    inputDisclaimer: 'নাগরিক সেবা এআই ভুল করতে পারে। গুরুত্বপূর্ণ তথ্যে সংশ্লিষ্ট সরকারি কর্তৃপক্ষ থেকে যাচাই করুন।',
    loadingAnswer: 'সরকারি তথ্য অনুসন্ধান ও উত্তর তৈরি করা হচ্ছে...',
    insufficientEvidence: 'অপ্রতুল তথ্য (Insufficient Evidence)',
    errorTitle: 'ত্রুটি ঘটেছে (Error)',
    diagnosticsBtn: 'কারিগরি বিবরণ (Diagnostics)',
    sourcesHeader: 'তথ্যসূত্র ও উদ্ধৃতি (Verified Sources)',
    openSourceLink: 'অফিসিয়াল সোর্স দেখুন',
    feedbackHelpful: 'সহায়ক (Helpful)',
    feedbackNotHelpful: 'সহায়ক নয় (Not Helpful)',

    // Diagnostics Modal
    modalTitle: 'সিস্টেম ডায়াগনস্টিকস (System Status)',
    modalServerStatus: 'API সার্ভার অবস্থা (Backend Server)',
    modalServerConnected: 'অনলাইন (Connected)',
    modalServerDisconnected: 'সংযোগ বিচ্ছিন্ন (Offline)',
    modalError: 'ত্রুটি:',
    modalChecksTitle: 'নলেজ বেস ও ওয়ার্কফ্লো (Readiness Checks)',
    modalCheckBM25: 'BM25 স্পার্স ইনডেক্স (BM25 Index):',
    modalCheckDense: 'ChromaDB ডেনস ভেক্টর (Dense Vectors):',
    modalCheckWorkflow: 'LangGraph RAG পাইপলাইন (Workflow):',
    modalEndpointsTitle: 'এন্ডপয়েন্ট কনফিগারেশন (Target Endpoints)',
    modalOpenSwagger: 'Swagger API Docs খুলুন',
    modalRecheck: 'পুনরায় পরীক্ষা',
    modalRechecking: 'যাচাই করা হচ্ছে...',

    // Examples
    examples: [
      {
        title: 'পাসপোর্ট করতে কী কী কাগজ লাগে?',
        category: 'পাসপোর্ট',
        query: 'পাসপোর্ট করতে কী কী কাগজ লাগে?',
      },
      {
        title: 'How do I apply for an NID correction?',
        category: 'NID',
        query: 'How do I apply for an NID correction?',
      },
      {
        title: 'TIN certificate করতে কী করতে হবে?',
        category: 'e-TIN',
        query: 'TIN certificate করতে কী করতে হবে?',
      },
      {
        title: 'পাসপোর্ট নবায়নের জরুরি ফি কত?',
        category: 'পাসপোর্ট',
        query: 'পাসপোর্ট নবায়নের জরুরি ফি কত?',
      },
      {
        title: 'NID card হারিয়ে গেলে কী করব?',
        category: 'NID',
        query: 'NID card হারিয়ে গেলে কী করব?',
      },
      {
        title: 'What is the tax-free income threshold?',
        category: 'কর / Tax',
        query: 'What is the tax-free income threshold in Bangladesh?',
      },
    ],
  },
  en: {
    // Header
    brandTitle: 'Bangladesh Citizen Services Assistant',
    brandSubtitle: 'Bilingual Citizen Services AI • Passport, NID & e-TIN',
    versionBadge: 'v1.0 • Agentic RAG',
    navLangBtnTitle: 'ওয়েবসাইট বাংলায় পরিবর্তন করুন (Switch to Bangla)',
    navLangBtnLabel: 'বাংলা',
    themeLightTitle: 'Switch to Light Mode',
    themeDarkTitle: 'Switch to Dark Mode',
    systemOnline: 'System Online',
    systemLoading: 'Connecting...',
    systemOffline: 'Disconnected',
    systemStatusTitle: 'View System Status & Live Diagnostics',
    sidebarToggleOpen: 'Open sidebar & settings',
    sidebarToggleClose: 'Collapse sidebar',

    // Sidebar
    newChat: 'Start New Conversation',
    responseLangLabel: 'Model Response Language',
    langAuto: 'Auto-detect (Recommended)',
    langBn: 'Bangla (বাংলা)',
    langEn: 'English',
    devSectionLabel: 'Developer & API Resources',
    swaggerDocs: 'FastAPI Swagger Docs',
    systemDiagnostics: 'System Diagnostics',
    trustBoxTitle: 'Verified Knowledge Base:',
    trustBoxDesc: 'Compiled from official gazettes and portals of DIP (Passport), Election Commission (NID), and NBR (e-TIN).',
    developedBy: 'Developed by: Mehedi Hossen Fahim',

    // Welcome Screen
    welcomeHeading: 'Bangladesh Citizen Services Assistant',
    welcomeSubtext: 'Get accurate procedural guidance and required document checklists for Passport, National ID (NID), or e-TIN government services.',
    examplesHeading: 'Example Inquiries (Click to ask directly)',

    // Chat & Input
    inputPlaceholder: 'Ask a question... (Press Enter to send, e.g. What documents are required for passport?)',
    sendTitle: 'Send query',
    inputDisclaimer: 'Citizen Services AI may make mistakes. Please verify critical information with official government authorities.',
    loadingAnswer: 'Searching official gazettes & formulating response...',
    insufficientEvidence: 'Insufficient Evidence',
    errorTitle: 'System Error',
    diagnosticsBtn: 'Technical Diagnostics',
    sourcesHeader: 'Official Sources & Citations',
    openSourceLink: 'View Official Source',
    feedbackHelpful: 'Helpful',
    feedbackNotHelpful: 'Not Helpful',

    // Diagnostics Modal
    modalTitle: 'System Diagnostics',
    modalServerStatus: 'Backend API Server Status',
    modalServerConnected: 'Connected (Online)',
    modalServerDisconnected: 'Disconnected (Offline)',
    modalError: 'Error:',
    modalChecksTitle: 'Knowledge Base & Workflow Readiness',
    modalCheckBM25: 'BM25 Sparse Lexical Index:',
    modalCheckDense: 'ChromaDB Dense Vector Store:',
    modalCheckWorkflow: 'LangGraph RAG Agent Workflow:',
    modalEndpointsTitle: 'Active Endpoint Configuration',
    modalOpenSwagger: 'Open Swagger API Documentation',
    modalRecheck: 'Run Re-check',
    modalRechecking: 'Checking...',

    // Examples
    examples: [
      {
        title: 'What documents are required for a new passport?',
        category: 'Passport',
        query: 'What documents are required for a new passport application in Bangladesh?',
      },
      {
        title: 'How do I apply for an NID correction online?',
        category: 'NID',
        query: 'How do I apply for an NID correction online?',
      },
      {
        title: 'How do I obtain an e-TIN certificate?',
        category: 'e-TIN',
        query: 'What is the procedure for obtaining an e-TIN certificate?',
      },
      {
        title: 'What are the urgent passport renewal fees?',
        category: 'Passport',
        query: 'What are the emergency passport renewal fees and delivery times?',
      },
      {
        title: 'What is the procedure if my NID card is lost?',
        category: 'NID',
        query: 'What should I do if my NID card is lost?',
      },
      {
        title: 'What is the tax-free income threshold in Bangladesh?',
        category: 'Tax / TIN',
        query: 'What is the tax-free income threshold for individuals in Bangladesh?',
      },
    ],
  },
};
