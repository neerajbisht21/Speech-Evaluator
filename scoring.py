import re
import math
import pandas as pd

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
except Exception:
    _vader = None

try:
    import language_tool_python
    _lt_tool = language_tool_python.LanguageTool('en-US')
except Exception:
    _lt_tool = None

_sem_model = None
_sem_util = None
def _load_semantic_model():
    global _sem_model, _sem_util
    if _sem_model is None:
        try:
            from sentence_transformers import SentenceTransformer, util
            _sem_model = SentenceTransformer("all-MiniLM-L6-v2")
            _sem_util = util
        except Exception:
            _sem_model = None
            _sem_util = None
    return _sem_model, _sem_util

_FILLER_WORDS = set([
    "um","uh","like","you know","so","actually","basically","right","i mean",
    "well","kind of","sort of","okay","hmm","erm","ah","uhm","ahh"
])

_CONTENT_KEYWORDS_MUST = [
    "name","age","school","class","family","hobbies","interests",
    "ambition","goal","dream","fun fact","strength","achievement"
]

_KEYWORD_SYNONYMS = {
    "school/class":"school",
    "class/school":"school",
    "hobbies/interests":"hobbies",
    "what they do in free time":"hobbies",
    "ambition/goal/dream":"ambition",
    "strengths or achievements":"strength"
}

def _normalize_keywords(raw_list):
    out = []
    for s in raw_list:
        s = str(s).strip().lower()
        if not s:
            continue
        for k,v in _KEYWORD_SYNONYMS.items():
            if k in s:
                s = s.replace(k, v)
        out.append(s)
    return out

_CONTENT_KEYWORDS_MUST = _normalize_keywords(_CONTENT_KEYWORDS_MUST)

def _word_tokens(text):
    return re.findall(r"\b\w+\b", str(text).lower())

def _word_count(text):
    return len(_word_tokens(text))

def _unique_word_count(text):
    toks = _word_tokens(text)
    return len(set(toks))

def _ttr(text):
    toks = _word_tokens(text)
    if not toks:
        return 0.0
    return len(set(toks)) / len(toks)

def _detect_keywords(text, keywords):
    txt_lower = text.lower()
    tokens = set(_word_tokens(text))
    found = []
    for kw in keywords:
        kw_l = kw.lower()
        if kw_l in tokens or kw_l in txt_lower:
            found.append(kw)
    return found

def _compute_salutation_score(text):
    txt = text.lower()
    if "i am excited to introduce" in txt or "i'm excited to introduce" in txt:
        return 5, "Excellent salutation phrase found."
    for g in ["good morning", "good afternoon", "good evening", "good day"]:
        if g in txt:
            return 4, f"Found greeting '{g}'."
    for g in ["hi ", "hello ", "hi,", "hello,"]:
        if g in txt:
            return 2, f"Found greeting '{g.strip()}'."
    return 0, "No salutation detected."

def _compute_flow_score(text):
    txt = text.lower()
    idx_map = {}
    order_keys = {
        "salutation": ["hi","hello","good morning","good afternoon","good evening","good day","i am excited"],
        "name": ["name","i am","i'm","my name is"],
        "age": ["age","i am \d","i'm \d","years old"],
        "school": ["school","class","college"],
        "additional": ["hobbies","interest","hobby","fun fact","strength","achievement","ambition","goal","dream"],
        "closing": ["thank you","thanks for listening","thank you for listening","thankyou"]
    }
    for k, kws in order_keys.items():
        idx_map[k] = None
        for kw in kws:
            m = re.search(re.escape(kw), txt)
            if m:
                idx = m.start()
                if idx_map[k] is None or idx < idx_map[k]:
                    idx_map[k] = idx
    order_sequence = ["salutation","name","age","school","additional","closing"]
    prev_idx = -1
    satisfied = True
    for key in order_sequence:
        idx = idx_map.get(key)
        if idx is not None:
            if idx < prev_idx:
                satisfied = False
                break
            prev_idx = idx
    return (5 if satisfied else 0), ("Flow followed" if satisfied else "Flow not followed / out of order")

def _compute_wpm(word_count, duration_seconds):
    if duration_seconds and duration_seconds > 0:
        return word_count / (duration_seconds / 60.0)
    return word_count

def _score_speech_rate(wpm):
    if wpm >= 161:
        return 2, "Too fast"
    if 141 <= wpm < 161:
        return 6, "Fast"
    if 111 <= wpm < 141:
        return 10, "Ideal"
    if 81 <= wpm < 111:
        return 6, "Slow"
    return 0, "Too slow"

def _count_grammar_errors(text):
    wc = _word_count(text)
    if wc == 0:
        return 0.0, "No words"
    if _lt_tool is not None:
        matches = _lt_tool.check(text)
        errors = sum(1 for m in matches if getattr(m, "rule_id", None) != "WHITESPACE_RULE")
        per100 = (errors / wc) * 100.0
        return per100, f"{errors} grammar issues detected by language-tool"
    errors = len(re.findall(r"\b(\w+)\s+\1\b", text.lower()))
    errors += len(re.findall(r"\b(dont|doesnt|isnt|cant|wont|shouldnt|couldnt|wouldnt)\b", text.lower()))
    per100 = (errors / wc) * 100.0
    return per100, f"{errors} heuristic grammar issues (fallback)"

def _score_grammar_errors(per100):
    r = per100 / 100.0
    if r < 0.3: return 10
    if r < 0.5: return 8
    if r < 0.7: return 6
    if r < 0.9: return 4
    return 2

def _score_ttr(ttr_val):
    if ttr_val >= 0.9: return 10
    if ttr_val >= 0.7: return 8
    if ttr_val >= 0.5: return 6
    if ttr_val >= 0.3: return 4
    return 2

def _filler_rate(text):
    toks = _word_tokens(text)
    if not toks: return 0.0, 0
    count = sum(len(re.findall(r"\b" + re.escape(f) + r"\b", text.lower())) for f in _FILLER_WORDS)
    rate = (count / len(toks)) * 100.0
    return rate, count

def _score_filler_rate(filler_pct):
    if filler_pct <= 3.0: return 15
    if filler_pct <= 6.0: return 12
    if filler_pct <= 9.0: return 9
    if filler_pct <= 12.0: return 6
    return 3

def _score_sentiment(text):
    if _vader is None:
        val, note = 0.5, "VADER not available; using neutral fallback"
    else:
        vs = _vader.polarity_scores(text)
        val, note = (vs.get("compound", 0.0) + 1.0)/2.0, f"VADER compound={vs.get('compound',0.0)}"
    points = 15 if val >= 0.9 else 12 if val >= 0.7 else 9 if val >= 0.5 else 6 if val >= 0.3 else 3
    return val, points, note

def score_transcript(text, duration_seconds=None):
    txt = str(text).strip()
    wc = _word_count(txt)
    sentences = [s.strip() for s in re.split(r'[.!?]+', txt) if s.strip()]
    sentence_count = len(sentences)
    duration_used = float(duration_seconds) if duration_seconds else None

    sal_score, sal_msg = _compute_salutation_score(txt)
    must_keywords = _CONTENT_KEYWORDS_MUST
    found_keywords = _detect_keywords(txt, must_keywords)
    keyword_hits = len(found_keywords)
    keyword_score_total = min((keyword_hits * 4), 20)

    flow_score, flow_msg = _compute_flow_score(txt)

    sem_bonus = 0.0
    sem_note = "Semantic model not used"
    model, util = _load_semantic_model()
    if model is not None:
        try:
            from sentence_transformers import util
            emb1 = model.encode(txt, convert_to_tensor=True)
            emb2 = model.encode("Introduction/self introduction content expected", convert_to_tensor=True)
            sim = util.cos_sim(emb1, emb2).item()
            sem_bonus = max(0.0, min(1.0, (sim + 1.0)/2.0)) * 10.0
            sem_note = f"Semantic similarity={round(sem_bonus,3)}"
        except Exception:
            sem_bonus = min(10.0, (keyword_hits / len(must_keywords)) * 10.0)
    else:
        sem_bonus = min(10.0, (keyword_hits / len(must_keywords)) * 10.0) if must_keywords else 0.0

    content_structure_score = sal_score + keyword_score_total + flow_score + sem_bonus

    wpm = _compute_wpm(wc, duration_used)
    speech_points, speech_msg = _score_speech_rate(wpm)

    errors_per100, err_note = _count_grammar_errors(txt)
    grammar_points = _score_grammar_errors(errors_per100)
    ttr_val = _ttr(txt)
    ttr_points = _score_ttr(ttr_val)

    filler_pct, filler_count = _filler_rate(txt)
    clarity_points = _score_filler_rate(filler_pct)

    sentiment_val, engagement_points, sentiment_note = _score_sentiment(txt)

    per_criteria = []

    per_criteria.append({
        "criterion": "Content & Structure",
        "components": {"Salutation": sal_score, "Keywords": keyword_score_total, "Flow": flow_score, "Semantic": round(sem_bonus,3)},
        "score": round(content_structure_score,3),
        "max_score": 40,
        "feedback": f"{sal_msg}. Keywords found: {', '.join(found_keywords) if found_keywords else 'None'}. {flow_msg}. {sem_note}"
    })

    per_criteria.append({
        "criterion": "Speech Rate",
        "components": {"WPM": round(wpm,2), "band_message": speech_msg},
        "score": speech_points,
        "max_score": 10,
        "feedback": f"WPM={round(wpm,2)}. {speech_msg}"
    })

    per_criteria.append({
        "criterion": "Language & Grammar",
        "components": {"Grammar errors per100": round(errors_per100,3), "Grammar points": grammar_points, "TTR": round(ttr_val,3), "TTR points": ttr_points},
        "score": grammar_points + ttr_points,
        "max_score": 20,
        "feedback": f"{err_note}. TTR={round(ttr_val,3)}"
    })

    per_criteria.append({
        "criterion": "Clarity",
        "components": {"Filler %": round(filler_pct,3), "Filler count": filler_count},
        "score": clarity_points,
        "max_score": 15,
        "feedback": f"Filler words={filler_count}, filler_percent={round(filler_pct,2)}%"
    })

    per_criteria.append({
        "criterion": "Engagement",
        "components": {"Sentiment_normalized_0_1": round(sentiment_val,3)},
        "score": engagement_points,
        "max_score": 15,
        "feedback": f"{sentiment_note}"
    })

    total_score_attained = sum(p["score"] for p in per_criteria)
    total_possible = sum(p["max_score"] for p in per_criteria)
    overall_score = round((total_score_attained / total_possible) * 100.0, 2)

    out = {
        "overall_score": overall_score,
        "word_count": wc,
        "sentence_count": sentence_count,
        "duration_seconds_used": duration_used,
        "per_criterion": per_criteria,
        "totals": {"attained": total_score_attained, "possible": total_possible}
    }

    return out
