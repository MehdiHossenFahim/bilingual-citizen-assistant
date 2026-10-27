import React from "react";

/**
 * Parses inline formatting:
 * - Bold: **text** or __text__
 * - Italic: *text* or _text_
 * - Citation markers: [src-1], [src-1, src-2]
 * - Bare & markdown URLs: www.example.com, https://...
 * - Inline code: `code`
 */
function renderInline(text, onCitationClick) {
  if (!text) return null;

  // Regex tokens to match:
  // 1. Markdown link: [text](url)
  // 2. Citation: \[src-(\d+)\] or combined \[src-(\d+)(?:,\s*src-(\d+))*\]
  // 3. Bold: \*\*(.*?)\*\*
  // 4. Italic: \*(.*?)\*
  // 5. Code: `(.*?)`
  // 6. Bare URL: (https?:\/\/[^\s\)]+|www\.[^\s\)]+)
  const combinedRegex =
    /(\[[^\]]+\]\([^\)]+\)|\[src-[\d,\s\-src]+\]|\*\*.*?\*\*|\*.*?\*|`.*?`|https?:\/\/[^\s\)]+|www\.[^\s\)]+)/g;

  const parts = text.split(combinedRegex);

  return parts.map((part, index) => {
    if (!part) return null;

    // Markdown link: [text](url)
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^\)]+)\)$/);
    if (linkMatch) {
      const href = linkMatch[2].startsWith("http")
        ? linkMatch[2]
        : `https://${linkMatch[2]}`;
      return (
        <a
          key={index}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="msg-link"
        >
          {linkMatch[1]}
        </a>
      );
    }

    // Citation badge: e.g. [src-1] or [src-1, src-2]
    if (part.startsWith("[src-") && part.endsWith("]")) {
      const srcNumbers = Array.from(part.matchAll(/src-(\d+)/g)).map((m) =>
        parseInt(m[1], 10),
      );
      return (
        <span key={index} className="citation-pill-group">
          {srcNumbers.map((num) => (
            <button
              type="button"
              key={num}
              className="citation-pill"
              title={`যাচাইকৃত তথ্যসূত্র ${num} দেখুন`}
              onClick={(e) => {
                e.preventDefault();
                if (onCitationClick) onCitationClick(num);
              }}
            >
              src-{num}
            </button>
          ))}
        </span>
      );
    }

    // Bold: **text**
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      return (
        <strong key={index} className="msg-strong">
          {part.slice(2, -2)}
        </strong>
      );
    }

    // Italic: *text*
    if (
      part.startsWith("*") &&
      part.endsWith("*") &&
      part.length >= 2 &&
      !part.startsWith("**")
    ) {
      return (
        <em key={index} className="msg-italic">
          {part.slice(1, -1)}
        </em>
      );
    }

    // Code: `code`
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return (
        <code key={index} className="msg-code">
          {part.slice(1, -1)}
        </code>
      );
    }

    // Bare URL: https://... or www....
    if (/^(https?:\/\/|www\.)[^\s\)]+$/.test(part)) {
      const href = part.startsWith("http") ? part : `https://${part}`;
      return (
        <a
          key={index}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="msg-link"
        >
          {part}
        </a>
      );
    }

    return part;
  });
}

/**
 * MarkdownView Component
 * Formats structured LLM responses with:
 * - Proper headings (#, ##, ###, and standalone **Title:**)
 * - Grouped bullet lists (-, *, •) with custom bullet styling
 * - Grouped numbered lists (1., ১.)
 * - Inline bold, italic, links, and clickable citation pills
 */
export default function MarkdownView({ content, onCitationClick }) {
  if (!content) return null;

  const rawLines = content.split("\n");
  const blocks = [];
  let currentList = null; // { type: 'ul' | 'ol', items: [] }

  const flushList = () => {
    if (currentList) {
      blocks.push(currentList);
      currentList = null;
    }
  };

  for (let i = 0; i < rawLines.length; i++) {
    const rawLine = rawLines[i];
    const trimmed = rawLine.trim();

    // Blank line
    if (!trimmed) {
      flushList();
      continue;
    }

    // Markdown Headers
    if (trimmed.startsWith("### ")) {
      flushList();
      blocks.push({
        type: "h3",
        content: trimmed.replace(/^###\s+/, ""),
      });
      continue;
    }

    if (trimmed.startsWith("## ")) {
      flushList();
      blocks.push({
        type: "h2",
        content: trimmed.replace(/^##\s+/, ""),
      });
      continue;
    }

    if (trimmed.startsWith("# ")) {
      flushList();
      blocks.push({
        type: "h1",
        content: trimmed.replace(/^#\s+/, ""),
      });
      continue;
    }

    // Standalone bold header: e.g. **প্রয়োজনীয় কাগজপত্র:** or **অন্যান্য গুরুত্বপূর্ণ তথ্য:**
    const boldHeaderMatch = trimmed.match(/^\*\*(.+?)\*\*:?$/);
    if (boldHeaderMatch) {
      flushList();
      blocks.push({
        type: "section-heading",
        content: boldHeaderMatch[1],
      });
      continue;
    }

    // Unordered List Items: •, -, *, +
    const ulMatch = trimmed.match(/^[•\-\*\+]\s+(.*)$/);
    if (ulMatch) {
      if (!currentList || currentList.type !== "ul") {
        flushList();
        currentList = { type: "ul", items: [] };
      }
      currentList.items.push(ulMatch[1]);
      continue;
    }

    // Ordered List Items: 1. or ১. or 1) or ১)
    const olMatch = trimmed.match(/^(\d+|[০-৯]+)[\.\)]\s+(.*)$/);
    if (olMatch) {
      if (!currentList || currentList.type !== "ol") {
        flushList();
        currentList = { type: "ol", items: [] };
      }
      currentList.items.push(olMatch[2]);
      continue;
    }

    // Regular paragraph
    flushList();
    blocks.push({
      type: "p",
      content: trimmed,
    });
  }

  flushList();

  return (
    <div className="markdown-body">
      {blocks.map((block, idx) => {
        switch (block.type) {
          case "h1":
            return (
              <h2 key={idx} className="msg-h1">
                {renderInline(block.content, onCitationClick)}
              </h2>
            );
          case "h2":
            return (
              <h3 key={idx} className="msg-h2">
                {renderInline(block.content, onCitationClick)}
              </h3>
            );
          case "h3":
            return (
              <h4 key={idx} className="msg-h3">
                {renderInline(block.content, onCitationClick)}
              </h4>
            );
          case "section-heading":
            return (
              <div key={idx} className="msg-section-heading">
                <span className="msg-section-title">
                  {renderInline(block.content, onCitationClick)}
                </span>
              </div>
            );
          case "ul":
            return (
              <ul key={idx} className="msg-ul">
                {block.items.map((item, liIdx) => (
                  <li key={liIdx} className="msg-li">
                    {renderInline(item, onCitationClick)}
                  </li>
                ))}
              </ul>
            );
          case "ol":
            return (
              <ol key={idx} className="msg-ol">
                {block.items.map((item, liIdx) => (
                  <li key={liIdx} className="msg-li">
                    {renderInline(item, onCitationClick)}
                  </li>
                ))}
              </ol>
            );
          case "p":
          default:
            return (
              <p key={idx} className="msg-p">
                {renderInline(block.content, onCitationClick)}
              </p>
            );
        }
      })}
    </div>
  );
}
