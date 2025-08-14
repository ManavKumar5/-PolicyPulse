import os
import json
import re

try:
    import spacy  # falls back to naive splitter if missing

    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

from .ml_model import load_model

BASE_DIR = os.path.dirname(__file__)


def load_rules():
    path = os.path.join(BASE_DIR, "rules.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_pii_patterns():
    path = os.path.join(BASE_DIR, "pii_patterns.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sentence_segment(text):
    text = text.strip()
    if not text:
        return []
    if nlp:
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents]
    else:
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]


def match_rules(text):
    """Return a list of matched rules for `text` (a single sentence normally)."""
    rules = load_rules()
    pii = load_pii_patterns()
    matches = []
    for r in rules:
        rtype = r.get("type")
        rid = r.get("id")
        desc = r.get("description")
        if rtype == "term":
            pat = r.get("pattern", "")
            if pat and pat.lower() in text.lower():
                matches.append(
                    {
                        "rule_id": rid,
                        "description": desc,
                        "pattern": pat,
                        "severity": r.get("severity", "medium"),
                    }
                )
        elif rtype == "regex":
            pat = r.get("pattern")
            if pat:
                m = re.search(pat, text, flags=re.IGNORECASE)
                if m:
                    matches.append(
                        {
                            "rule_id": rid,
                            "description": desc,
                            "pattern": m.group(0),
                            "severity": r.get("severity", "medium"),
                        }
                    )
        elif rtype == "pii":
            key = r.get("pattern")
            pat = pii.get(key)
            if pat:
                m = re.search(pat, text)
                if m:
                    matches.append(
                        {
                            "rule_id": rid,
                            "description": desc,
                            "pattern": m.group(0),
                            "severity": r.get("severity", "high"),
                        }
                    )
        elif rtype == "ml":
            # ML-based check
            try:
                clf, vect = load_model()
                x = vect.transform([text])
                prob = float(clf.predict_proba(x)[0][1])
                threshold = float(r.get("threshold", 0.65))
                if prob >= threshold:
                    matches.append(
                        {
                            "rule_id": rid,
                            "description": desc,
                            "pattern": "ML:prob>=%.2f" % threshold,
                            "probability": prob,
                            "severity": r.get("severity", "low"),
                        }
                    )
            except Exception:
                # ML optional-> if it fails we skip silently
                continue

    return matches


def scan_text(full_text):
    """Segment text into sentences and return flagged sentences with matched rules."""
    sents = sentence_segment(full_text)
    flagged = []
    for i, s in enumerate(sents):
        ms = match_rules(s)
        if ms:
            flagged.append({"index": i, "sentence": s, "matches": ms})
    return flagged
