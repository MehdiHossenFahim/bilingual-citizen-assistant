import React, { useState } from 'react';
import { ExternalLink, ChevronDown, ChevronUp, FileText } from 'lucide-react';

export default function CitationCard({ citation, index }) {
  const [expanded, setExpanded] = useState(false);

  const { title, authority, url, page, section, excerpt, publication_date } = citation;

  return (
    <div className="citation-card">
      <div className="citation-title-row">
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <FileText size={15} color="#006a4e" />
          <span>[{index}] {title || 'সরকারি নথি (Official Document)'}</span>
        </span>
        {excerpt && (
          <button
            className="btn-icon"
            onClick={() => setExpanded(!expanded)}
            title={expanded ? 'সংক্ষিপ্ত করুন' : 'বিস্তারিত উদ্ধৃতি দেখুন'}
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        )}
      </div>

      <div className="citation-authority">
        {authority && <span>🏛️ {authority}</span>}
        {publication_date && <span> • 📅 {publication_date}</span>}
        {page && <span> • 📄 পৃষ্ঠা {page}</span>}
        {section && <span> • 🔖 {section}</span>}
      </div>

      {url && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="citation-link"
        >
          <span>সরকারি পোর্টালে যাচাই করুন</span>
          <ExternalLink size={12} />
        </a>
      )}

      {expanded && excerpt && (
        <div className="citation-excerpt">
          "{excerpt}"
        </div>
      )}
    </div>
  );
}

