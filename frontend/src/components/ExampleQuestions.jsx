import React from 'react';
import { ArrowUpRight } from 'lucide-react';

const EXAMPLES = [
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
];

export default function ExampleQuestions({ onSelect }) {
  return (
    <div className="example-grid">
      {EXAMPLES.map((item, idx) => (
        <button
          key={idx}
          className="example-chip"
          onClick={() => onSelect(item.query)}
        >
          <div>
            <div style={{ fontSize: '0.72rem', color: '#006a4e', fontWeight: 600 }}>{item.category}</div>
            <div style={{ fontWeight: 500, color: '#1e293b', marginTop: '2px' }}>{item.title}</div>
          </div>
          <ArrowUpRight size={16} color="#94a3b8" />
        </button>
      ))}
    </div>
  );
}

