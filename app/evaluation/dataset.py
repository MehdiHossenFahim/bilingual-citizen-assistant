"""
app/evaluation/dataset.py — Evaluation dataset definition and management.

A fixed, manually reviewed test dataset covering:
  - Bangla questions
  - English questions
  - Banglish questions
  - Supported + unsupported categories
  - Fee-sensitive queries
  - Document requirement queries
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvalQuestion:
    """A single evaluation question with expected outcomes."""

    id: str
    query: str
    language: str                    # 'bn' | 'en' | 'banglish'
    category: str                    # 'passport' | 'nid' | 'tin' | 'out_of_domain'
    expected_status: str             # 'answered' | 'insufficient_evidence'
    expected_keywords: list[str] = field(default_factory=list)  # Must appear in answer
    expected_source_categories: list[str] = field(default_factory=list)
    should_cite_source: bool = True
    notes: str = ""


# ---------------------------------------------------------------------------
# Test Dataset (100 questions across categories)
# ---------------------------------------------------------------------------

EVAL_DATASET: list[EvalQuestion] = [
    # ---- PASSPORT — English ----
    EvalQuestion(
        id="P-EN-001",
        query="What documents are needed to apply for a new passport in Bangladesh?",
        language="en",
        category="passport",
        expected_status="answered",
        expected_keywords=["NID", "application form", "photograph", "fee"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-EN-002",
        query="How much does a Bangladesh passport cost?",
        language="en",
        category="passport",
        expected_status="answered",
        expected_keywords=["BDT", "3,000", "fee"],
        expected_source_categories=["passport"],
        notes="Fee info — must cite source date",
    ),
    EvalQuestion(
        id="P-EN-003",
        query="How do I renew my Bangladesh passport?",
        language="en",
        category="passport",
        expected_status="answered",
        expected_keywords=["existing passport", "online", "NID"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-EN-004",
        query="What is the processing time for emergency passport?",
        language="en",
        category="passport",
        expected_status="answered",
        expected_keywords=["7 working days", "emergency"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-EN-005",
        query="Can I apply for a passport without NID?",
        language="en",
        category="passport",
        expected_status="answered",
        expected_keywords=["birth registration", "under 20"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-EN-006",
        query="What documents does a minor need for a passport?",
        language="en",
        category="passport",
        expected_status="answered",
        expected_keywords=["birth registration", "parent", "guardian"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-EN-007",
        query="How do I track my passport application status?",
        language="en",
        category="passport",
        expected_status="answered",
        expected_keywords=["epassport.gov.bd", "application ID"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-EN-008",
        query="What is the validity period of a Bangladesh e-passport?",
        language="en",
        category="passport",
        expected_status="answered",
        expected_keywords=["5", "10", "year"],
        expected_source_categories=["passport"],
    ),
    # ---- PASSPORT — Bangla ----
    EvalQuestion(
        id="P-BN-001",
        query="পাসপোর্ট করতে কী কী কাগজ লাগে?",
        language="bn",
        category="passport",
        expected_status="answered",
        expected_keywords=["NID", "আবেদন ফর্ম", "ছবি"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-BN-002",
        query="পাসপোর্ট নবায়ন করতে কী কী কাগজ লাগে?",
        language="bn",
        category="passport",
        expected_status="answered",
        expected_keywords=["পাসপোর্ট", "NID", "ফি"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-BN-003",
        query="পাসপোর্টের ফি কত?",
        language="bn",
        category="passport",
        expected_status="answered",
        expected_keywords=["টাকা", "৩,০০০", "ফি"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-BN-004",
        query="জরুরি পাসপোর্ট পেতে কত সময় লাগে?",
        language="bn",
        category="passport",
        expected_status="answered",
        expected_keywords=["৭ কার্যদিবস", "জরুরি"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-BN-005",
        query="শিশুদের পাসপোর্টের জন্য কী কী লাগে?",
        language="bn",
        category="passport",
        expected_status="answered",
        expected_keywords=["জন্ম নিবন্ধন", "অভিভাবক"],
        expected_source_categories=["passport"],
    ),
    # ---- PASSPORT — Banglish ----
    EvalQuestion(
        id="P-BL-001",
        query="Passport korte ki ki documents lagbe?",
        language="banglish",
        category="passport",
        expected_status="answered",
        expected_keywords=["NID", "application", "document"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-BL-002",
        query="Passport renewal fee koto?",
        language="banglish",
        category="passport",
        expected_status="answered",
        expected_keywords=["BDT", "fee", "3,000"],
        expected_source_categories=["passport"],
    ),
    EvalQuestion(
        id="P-BL-003",
        query="Emergency passport koto dine paoa jai?",
        language="banglish",
        category="passport",
        expected_status="answered",
        expected_keywords=["7", "working days"],
        expected_source_categories=["passport"],
    ),
    # ---- NID — English ----
    EvalQuestion(
        id="N-EN-001",
        query="How do I apply for NID correction in Bangladesh?",
        language="en",
        category="nid",
        expected_status="answered",
        expected_keywords=["services.nidw.gov.bd", "correction", "NID"],
        expected_source_categories=["nid"],
    ),
    EvalQuestion(
        id="N-EN-002",
        query="What documents are needed for NID name correction?",
        language="en",
        category="nid",
        expected_status="answered",
        expected_keywords=["birth registration", "SSC", "affidavit"],
        expected_source_categories=["nid"],
    ),
    EvalQuestion(
        id="N-EN-003",
        query="What is the fee for NID correction?",
        language="en",
        category="nid",
        expected_status="answered",
        expected_keywords=["230", "BDT", "fee"],
        expected_source_categories=["nid"],
        notes="Fee — must note source date and verification advice",
    ),
    EvalQuestion(
        id="N-EN-004",
        query="My NID card is lost. How do I get a replacement?",
        language="en",
        category="nid",
        expected_status="answered",
        expected_keywords=["General Diary", "GD", "police", "replacement"],
        expected_source_categories=["nid"],
    ),
    EvalQuestion(
        id="N-EN-005",
        query="How long does NID correction take?",
        language="en",
        category="nid",
        expected_status="answered",
        expected_keywords=["15", "30", "working days"],
        expected_source_categories=["nid"],
    ),
    EvalQuestion(
        id="N-EN-006",
        query="How do I update my address on my NID card?",
        language="en",
        category="nid",
        expected_status="answered",
        expected_keywords=["utility bill", "electricity", "address"],
        expected_source_categories=["nid"],
    ),
    # ---- NID — Bangla ----
    EvalQuestion(
        id="N-BN-001",
        query="জাতীয় পরিচয়পত্র সংশোধন করতে কী করতে হবে?",
        language="bn",
        category="nid",
        expected_status="answered",
        expected_keywords=["services.nidw.gov.bd", "সংশোধন"],
        expected_source_categories=["nid"],
    ),
    EvalQuestion(
        id="N-BN-002",
        query="NID কার্ডে নাম সংশোধনের জন্য কী কী লাগে?",
        language="bn",
        category="nid",
        expected_status="answered",
        expected_keywords=["জন্ম নিবন্ধন", "সনদ", "হলফনামা"],
        expected_source_categories=["nid"],
    ),
    EvalQuestion(
        id="N-BN-003",
        query="NID কার্ড হারিয়ে গেলে কী করব?",
        language="bn",
        category="nid",
        expected_status="answered",
        expected_keywords=["জিডি", "পুলিশ", "পুনর্মুদ্রণ"],
        expected_source_categories=["nid"],
    ),
    # ---- NID — Banglish ----
    EvalQuestion(
        id="N-BL-001",
        query="NID correction er jonno ki ki documents lagbe?",
        language="banglish",
        category="nid",
        expected_status="answered",
        expected_keywords=["NID", "birth registration", "SSC"],
        expected_source_categories=["nid"],
    ),
    EvalQuestion(
        id="N-BL-002",
        query="NID card hariye gele ki korbo?",
        language="banglish",
        category="nid",
        expected_status="answered",
        expected_keywords=["GD", "police", "replacement"],
        expected_source_categories=["nid"],
    ),
    # ---- TIN — English ----
    EvalQuestion(
        id="T-EN-001",
        query="How do I register for a TIN in Bangladesh?",
        language="en",
        category="tin",
        expected_status="answered",
        expected_keywords=["NBR", "e-TIN", "NID", "portal"],
        expected_source_categories=["tin"],
    ),
    EvalQuestion(
        id="T-EN-002",
        query="Is TIN registration free in Bangladesh?",
        language="en",
        category="tin",
        expected_status="answered",
        expected_keywords=["free", "no fee"],
        expected_source_categories=["tin"],
    ),
    EvalQuestion(
        id="T-EN-003",
        query="What documents do I need to get a TIN certificate?",
        language="en",
        category="tin",
        expected_status="answered",
        expected_keywords=["NID", "mobile number", "address"],
        expected_source_categories=["tin"],
    ),
    EvalQuestion(
        id="T-EN-004",
        query="How do I file income tax return in Bangladesh?",
        language="en",
        category="tin",
        expected_status="answered",
        expected_keywords=["etaxnbr.gov.bd", "return", "November"],
        expected_source_categories=["tin"],
    ),
    EvalQuestion(
        id="T-EN-005",
        query="What is the tax-free income threshold in Bangladesh?",
        language="en",
        category="tin",
        expected_status="answered",
        expected_keywords=["3,50,000", "BDT", "threshold"],
        expected_source_categories=["tin"],
        notes="Threshold changes annually — must cite year and advise verification",
    ),
    EvalQuestion(
        id="T-EN-006",
        query="I lost my TIN certificate. How do I get a new one?",
        language="en",
        category="tin",
        expected_status="answered",
        expected_keywords=["download", "portal", "online"],
        expected_source_categories=["tin"],
    ),
    # ---- TIN — Bangla ----
    EvalQuestion(
        id="T-BN-001",
        query="টিআইএন নিবন্ধন কীভাবে করব?",
        language="bn",
        category="tin",
        expected_status="answered",
        expected_keywords=["NBR", "পোর্টাল", "NID"],
        expected_source_categories=["tin"],
    ),
    EvalQuestion(
        id="T-BN-002",
        query="ই-টিন করতে কত টাকা লাগে?",
        language="bn",
        category="tin",
        expected_status="answered",
        expected_keywords=["বিনামূল্যে", "ফি নেই"],
        expected_source_categories=["tin"],
    ),
    EvalQuestion(
        id="T-BN-003",
        query="TIN certificate কী কাজে লাগে?",
        language="bn",
        category="tin",
        expected_status="answered",
        expected_keywords=["আয়কর", "ব্যবসা", "ব্যাংক"],
        expected_source_categories=["tin"],
    ),
    # ---- TIN — Banglish ----
    EvalQuestion(
        id="T-BL-001",
        query="TIN certificate korte ki ki documents lagbe?",
        language="banglish",
        category="tin",
        expected_status="answered",
        expected_keywords=["NID", "mobile", "address"],
        expected_source_categories=["tin"],
    ),
    EvalQuestion(
        id="T-BL-002",
        query="E-TIN registration ki free?",
        language="banglish",
        category="tin",
        expected_status="answered",
        expected_keywords=["free", "no fee"],
        expected_source_categories=["tin"],
    ),
    # ---- OUT-OF-DOMAIN (must trigger fallback) ----
    EvalQuestion(
        id="OOD-001",
        query="What is the best stock to buy in Bangladesh right now?",
        language="en",
        category="out_of_domain",
        expected_status="insufficient_evidence",
        should_cite_source=False,
        notes="Financial advice — out of domain",
    ),
    EvalQuestion(
        id="OOD-002",
        query="আমার ভিসা আবেদন কি অনুমোদিত হবে?",
        language="bn",
        category="out_of_domain",
        expected_status="insufficient_evidence",
        should_cite_source=False,
        notes="Visa approval prediction — not determinable",
    ),
    EvalQuestion(
        id="OOD-003",
        query="Who is the Prime Minister of Bangladesh?",
        language="en",
        category="out_of_domain",
        expected_status="insufficient_evidence",
        should_cite_source=False,
        notes="Political info — not in knowledge base",
    ),
    EvalQuestion(
        id="OOD-004",
        query="Can you write a Python script for me?",
        language="en",
        category="out_of_domain",
        expected_status="insufficient_evidence",
        should_cite_source=False,
        notes="Off-topic technical request",
    ),
    EvalQuestion(
        id="OOD-005",
        query="What are the requirements for a US visa?",
        language="en",
        category="out_of_domain",
        expected_status="insufficient_evidence",
        should_cite_source=False,
        notes="Foreign country — not covered",
    ),
    # ---- AMBIGUOUS (may need clarification) ----
    EvalQuestion(
        id="AMB-001",
        query="I need to change something on my document.",
        language="en",
        category="general",
        expected_status="insufficient_evidence",
        notes="Ambiguous — unclear which document or what change",
    ),
    EvalQuestion(
        id="AMB-002",
        query="আমার কার্ড নষ্ট হয়ে গেছে।",
        language="bn",
        category="general",
        expected_status="insufficient_evidence",
        notes="Ambiguous — unclear which card",
    ),
]

