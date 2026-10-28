import React from 'react';
import { ArrowUpRight } from 'lucide-react';

export default function ExampleQuestions({ examples = [], onSelect }) {
  return (
    <div className="example-grid">
      {examples.map((item, idx) => (
        <button
          key={idx}
          type="button"
          className="example-chip"
          onClick={() => onSelect(item.query)}
        >
          <div className="example-chip-content">
            <span className="example-category">{item.category}</span>
            <p className="example-title">{item.title}</p>
          </div>
          <ArrowUpRight size={16} className="example-icon" />
        </button>
      ))}
    </div>
  );
}
