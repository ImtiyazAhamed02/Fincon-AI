"""
app/services/sentiment_service.py
──────────────────────────────────────────────────────────────────────────────
Institutional-Grade Sentiment Analysis Service  — v3.0
──────────────────────────────────────────────────────────────────────────────

Relevance + Beneficiary Rules
──────────────────────────────
1.  Article MUST directly discuss the target company, its products, earnings,
    leadership, partnerships, regulatory issues, competitors, or stock price.
2.  Articles mentioning the company only in passing are excluded.
3.  Broad market / macro articles are excluded unless the company is the
    PRIMARY subject.
4.  No indirect industry inferences (gold rising ≠ good for Google).
5.  For each relevant article we identify:
        • Target Company   — always the requested ticker
        • Primary Beneficiary — who gains most from this news
        • Primary Risk Holder — who is hurt most by this news
6.  An article is classified Bullish for the target only if the target
    company IS the primary beneficiary.
7.  An article is classified Bearish for the target only if the target
    company IS the primary risk holder.
8.  If another company is the primary beneficiary/risk-holder the article
    scores as Neutral for the target (but is still shown so the reader
    understands the competitive context).
9.  Excluded articles are recorded with an explicit human-readable reason.

Output Keys
───────────
  relevant_articles_count   : int
  excluded_articles_count   : int
  excluded_articles         : list[{title, source, reason}]
  sentiment_scores          : {Bullish%, Bearish%, Neutral%}
  good_news                 : list[{headline, source, impact, beneficiary, risk_holder}]
  potential_concerns        : list[{headline, source, impact, beneficiary, risk_holder}]
  news_worth_watching       : list[{headline, source, impact, beneficiary, risk_holder}]
  bottom_line               : str   — plain-English summary for beginners
  confidence_score          : float (max 95%)
  confidence_explanation    : str
  key_events                : list
  financial_impacts         : list
  recent_articles           : list
"""

import re
import requests
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logger import logger


# ─────────────────────────────────────────────────────────────────────────────
# Company keyword catalogue
# ─────────────────────────────────────────────────────────────────────────────
COMPANY_CATALOGUE: dict = {
    "AAPL": {
        "name":       "Apple",
        "primary":    ["apple inc", "apple's", "aapl"],
        "secondary":  [
            "iphone", "macbook", "ipad", "ios", "macos", "watchos", "visionos",
            "tim cook", "app store", "vision pro", "airpods", "apple silicon",
            "m1", "m2", "m3", "m4", "apple intelligence", "siri", "apple tv",
            "apple pay", "apple card", "cupertino", "wwdc",
        ],
        "competitors": {
            "samsung":      "Samsung",
            "google pixel": "Google",
            "huawei":       "Huawei",
            "xiaomi":       "Xiaomi",
            "oneplus":      "OnePlus",
        },
    },
    "NVDA": {
        "name":       "Nvidia",
        "primary":    ["nvidia", "nvda"],
        "secondary":  [
            "h100", "h200", "a100", "blackwell", "hopper", "ampere", "geforce",
            "rtx", "jensen huang", "cuda", "nvlink", "mellanox", "dgx", "grace",
            "omniverse", "nemo", "nvidia ai", "gpu chip",
        ],
        "competitors": {
            "amd":          "AMD",
            "intel arc":    "Intel",
            "qualcomm ai":  "Qualcomm",
            "broadcom ai":  "Broadcom",
        },
    },
    "MSFT": {
        "name":       "Microsoft",
        "primary":    ["microsoft", "msft"],
        "secondary":  [
            "azure", "windows", "copilot", "satya nadella", "xbox", "office 365",
            "teams", "linkedin", "github", "bing", "surface", "dynamics",
        ],
        "competitors": {
            "google workspace": "Google",
            "amazon aws":       "Amazon",
            "salesforce":       "Salesforce",
            "oracle cloud":     "Oracle",
        },
    },
    "GOOG": {
        "name":       "Google / Alphabet",
        "primary":    ["google", "alphabet", "goog"],
        "secondary":  [
            "sundar pichai", "gemini", "youtube", "android", "deepmind",
            "waymo", "google cloud", "google ads", "pixel phone", "chrome",
            "google search", "bard", "google maps", "google pay",
        ],
        "competitors": {
            "microsoft bing":   "Microsoft",
            "openai chatgpt":   "OpenAI",
            "meta ai":          "Meta",
        },
    },
    "GOOGL": {
        "name":       "Google / Alphabet",
        "primary":    ["google", "alphabet", "googl"],
        "secondary":  [
            "sundar pichai", "gemini", "youtube", "android", "deepmind",
            "waymo", "google cloud", "google ads", "pixel phone", "chrome",
            "google search", "bard", "google maps", "google pay",
        ],
        "competitors": {
            "microsoft bing":   "Microsoft",
            "openai chatgpt":   "OpenAI",
            "meta ai":          "Meta",
        },
    },
    "AMZN": {
        "name":       "Amazon",
        "primary":    ["amazon", "amzn"],
        "secondary":  [
            "aws", "andy jassy", "prime video", "whole foods", "kindle",
            "alexa", "echo", "amazon fresh", "amazon web services",
            "amazon advertising",
        ],
        "competitors": {
            "walmart":   "Walmart",
            "alibaba":   "Alibaba",
            "shopify":   "Shopify",
            "microsoft": "Microsoft",
        },
    },
    "TSLA": {
        "name":       "Tesla",
        "primary":    ["tesla", "tsla"],
        "secondary":  [
            "elon musk", "model 3", "model y", "model s", "model x",
            "cybertruck", "cybercab", "fsd", "full self-driving",
            "gigafactory", "supercharger", "powerwall", "megapack",
            "autopilot", "robotaxi", "tesla energy", "optimus robot",
        ],
        "competitors": {
            "byd":          "BYD",
            "rivian":       "Rivian",
            "lucid motors": "Lucid",
            "nio":          "NIO",
        },
    },
    "META": {
        "name":       "Meta",
        "primary":    ["meta platforms", "meta inc", "meta"],
        "secondary":  [
            "mark zuckerberg", "instagram", "facebook", "whatsapp", "threads",
            "llama", "quest 3", "ray-ban glasses", "horizon worlds",
            "meta ai", "reels", "oculus",
        ],
        "competitors": {
            "tiktok":    "TikTok",
            "snapchat":  "Snapchat",
            "bytedance": "ByteDance",
            "pinterest": "Pinterest",
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Macro / commodity keywords  (article dominated by these → excluded)
# ─────────────────────────────────────────────────────────────────────────────
MACRO_KEYWORDS = [
    "gold prices", "oil prices", "crude oil", "brent crude", "wti crude",
    "commodity prices", "interest rates", "inflation rate", "cpi report",
    "federal reserve", "fed rate", "treasury yields", "bond yields",
    "gdp growth", "unemployment rate", "jobless claims", "retail sales data",
    "housing market", "manufacturing pmi", "consumer confidence index",
    "stock market today", "wall street today", "market rally", "market selloff",
    "s&p 500 today", "dow jones today", "nasdaq composite",
]

# Broad-market roundup patterns → excluded unless company is primary subject
BROAD_MARKET_PATTERNS = [
    r"(top|best|worst|biggest)\s+(gainers?|losers?|movers?|stocks?)\s+(today|this week|this month)",
    r"stocks?\s+to\s+(watch|buy|sell|avoid)",
    r"market\s+(recap|summary|wrap|overview|roundup)",
    r"(weekly|daily|monthly)\s+(market|stock)\s+(digest|recap|review)",
]

# Passing-mention patterns → excluded
PASSING_MENTION_PATTERNS = [
    r"\b(including|among others|such as|like|and other)\s.*?\b{company}\b",
    r"\b{company}\s*(and|,)\s*(other|several|multiple|many)\s+\w+\s+companies\b",
    r"\b(stocks?|shares?|equit(?:y|ies))\s+(?:such as|like|including)\b.*\b{company}\b",
]

# Positive signals → article helps the company mentioned
BULL_SIGNALS = [
    "beat", "beats", "record", "record high", "surged", "soared", "jumped",
    "growth", "profit", "upgrade", "upgraded", "outperform", "strong demand",
    "partnership", "deal", "contract", "expansion", "launch", "milestone",
    "award", "approved", "cleared", "rally", "bullish", "positive outlook",
    "boosts", "gains", "wins", "secures",
]

# Negative signals → article hurts the company mentioned
BEAR_SIGNALS = [
    "miss", "missed", "decline", "declined", "fell", "dropped", "cut",
    "downgrade", "downgraded", "underperform", "lawsuit", "sued",
    "investigation", "probe", "fine", "penalty", "recall", "warning",
    "layoff", "slowdown", "concern", "risk", "loss", "debt", "bearish",
    "negative outlook", "weaker", "struggles", "ban", "blocked",
]


class SentimentService:

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _catalogue(ticker: str) -> dict:
        return COMPANY_CATALOGUE.get(ticker.upper(), {
            "name":       ticker.upper(),
            "primary":    [ticker.lower()],
            "secondary":  [],
            "competitors": {},
        })

    @staticmethod
    def _has_any(text: str, keywords: list) -> bool:
        return any(re.search(r"\b" + re.escape(kw) + r"\b", text) for kw in keywords)

    # ─────────────────────────────────────────────────────────────────────────
    # Relevance classification
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def classify_relevance(
        cls, headline: str, summary: str, ticker: str
    ) -> tuple:
        """
        Returns (label, exclusion_reason | None)
        label: "RELEVANT" | "PARTIAL" | "NOT_RELEVANT"
        """
        text = (headline + " " + summary).lower()
        cat  = cls._catalogue(ticker)

        primary_kw   = cat.get("primary",   [])
        secondary_kw = cat.get("secondary", [])
        comp_dict    = cat.get("competitors", {})
        comp_kw      = list(comp_dict.keys())

        # Never exclude an article that directly mentions the target company or stock ticker in the headline
        headline_lower = headline.lower()
        direct_terms = [ticker.lower()]
        if "name" in cat:
            for part in cat["name"].split("/"):
                name_clean = part.strip().lower()
                if name_clean:
                    direct_terms.append(name_clean)
        for pk in primary_kw:
            direct_terms.append(pk.lower())

        simple_names = {
            "AAPL": ["apple"],
            "NVDA": ["nvidia"],
            "MSFT": ["microsoft"],
            "GOOG": ["google", "alphabet"],
            "GOOGL": ["google", "alphabet"],
            "AMZN": ["amazon"],
            "TSLA": ["tesla"],
            "META": ["meta"],
        }
        if ticker.upper() in simple_names:
            direct_terms.extend(simple_names[ticker.upper()])

        direct_terms = sorted(list(set(direct_terms)), key=len, reverse=True)
        has_headline_mention = False
        for term in direct_terms:
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, headline_lower):
                has_headline_mention = True
                break

        if has_headline_mention:
            return ("RELEVANT", None)


        has_primary   = cls._has_any(text, primary_kw)
        has_secondary = cls._has_any(text, secondary_kw)

        # ── Broad-market roundup check ─────────────────────────────────────
        is_broad = any(re.search(p, text, re.IGNORECASE) for p in BROAD_MARKET_PATTERNS)

        # ── Macro-dominated check ──────────────────────────────────────────
        macro_hits = sum(1 for kw in MACRO_KEYWORDS
                         if re.search(r"\b" + re.escape(kw) + r"\b", text))

        # ── Passing-mention check ──────────────────────────────────────────
        company_root = primary_kw[0] if primary_kw else ticker.lower()
        is_passing = any(
            re.search(
                p.replace("{company}", re.escape(company_root)),
                text, re.IGNORECASE
            )
            for p in PASSING_MENTION_PATTERNS
        )

        # ── Decision ──────────────────────────────────────────────────────
        if not has_primary and not has_secondary:
            if macro_hits >= 2:
                return ("NOT_RELEVANT",
                        "Macro/economic article — no mention of the company or its products")
            return ("NOT_RELEVANT",
                    "No direct mention of the company, its products, leadership, or stock")

        if is_broad and not (has_primary or has_secondary):
            return ("NOT_RELEVANT",
                    "Broad-market roundup — company is not the primary subject")

        if is_passing and not has_secondary:
            return ("NOT_RELEVANT",
                    "Company mentioned only in passing within an unrelated article")

        if macro_hits >= 3 and (has_primary or has_secondary):
            return ("PARTIAL", None)

        if has_secondary or has_primary:
            return ("RELEVANT", None)

        return ("NOT_RELEVANT",
                "Insufficient connection to the target company")

    # ─────────────────────────────────────────────────────────────────────────
    # Beneficiary & risk-holder detection
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def detect_beneficiary(
        cls, headline: str, summary: str, ticker: str
    ) -> dict:
        """
        Identifies:
          primary_beneficiary  : "Target Company" | "<Competitor Name>" | "Industry" | "Unknown"
          primary_risk_holder  : "Target Company" | "<Competitor Name>" | "Industry" | "Unknown"
          sentiment_for_target : "Bullish" | "Bearish" | "Neutral"
          beneficiary_note     : plain-English explanation
        """
        text = (headline + " " + summary).lower()
        headline_lower = headline.lower()
        cat  = cls._catalogue(ticker)
        company_name = cat.get("name", ticker.upper())
        comp_dict    = cat.get("competitors", {})

        # Does the headline/summary mention any competitor primarily?
        competitor_mentioned = None
        for kw, name in comp_dict.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                competitor_mentioned = name
                break

        # Negative category regex patterns
        neg_patterns = {
            "delays": r"\b(delay|delayed|delays|postpone|postponed|postponing|postponement|push(es)? back|pushed back|pushing back|reschedule|rescheduled|rescheduling|setback|setbacks|slowdown|held up|late|lateness|behind schedule)\b",
            "regulatory": r"\b(probe|probes|probing|antitrust|investigate|investigation|investigations|investigating|lawsuit|lawsuits|sued|suing|fine|fined|fines|fining|penalty|penalties|regulatory|regulation|regulations|sec|ftc|doj|court|judge|legal|compliance|non-compliance|crackdown|crackdowns|block|blocked|blocking|ban|banned|banning|patent dispute|infringement)\b",
            "disappointment": r"\b(disappoint|disappointed|disappoints|disappointing|disappointment|concern|concerns|skeptic|skeptical|skepticism|backlash|frustrate|frustrated|frustration|unimpressed|drop|drops|dropped|dropping|slide|slides|sliding|slump|slumps|slumping|tumble|tumbles|tumbled|tumbling|plunge|plunges|plunged|plunging|sell-off|selloff|selloffs|fall|falls|fell|falling|plummets?|plummeted|plummeting|losses|loss|lost|lose|losing)\b",
            "weak_demand": r"\b(weak demand|soft demand|declining demand|low demand|slowing sales|sluggish|sluggishness|cooling demand|cooling interest|lack of interest|falling demand|weaker demand|slow demand|drop in demand|decline in demand|lower demand)\b",
            "dilution": r"\b(dilution|dilute|dilutes|diluted|diluting|share offering|stock offering|secondary offering|equity offering|share issuance|issuing shares|issue shares|raises capital|raising capital|raise capital|capital raise|debt issuance)\b",
            "missed": r"\b(miss|missed|misses|missing|below estimate|below estimates|below expectation|below expectations|fell short|falls short|falling short|fail to meet|fails to meet|failed to meet|underwhelm|underwhelmed|underwhelming|missed forecast|missed forecasts|guidance cut|cut guidance|cuts guidance|lowered guidance|lower guidance|warns?|warning|warned)\b"
        }

        # Positive category regex patterns
        pos_patterns = {
            "growth": r"\b(growth|grow|grew|growing|grows|record high|record revenue|surge|surges|surged|surging|soar|soars|soared|soaring|jump|jumps|jumped|jumping|expand|expands|expanded|expanding|expansion|rise|rises|rising|rose|profit surge|profit jump|revenue rise|revenue jump)\b",
            "partnerships": r"\b(partnership|partnerships|partner|partnered|partnering|deal|deals|contract|contracts|alliance|alliances|collaboration|collaborations|joint venture|agreement|agreements|signed deal|team up|teams up|teamed up|teaming up)\b",
            "new_products": r"\b(launch|launched|launches|launching|new product|new products|unveil|unveils|unveiled|unveiling|announce|announces|announced|announcing|release|releases|released|releasing|introduce|introduces|introduced|introducing|new feature|new features|next-gen|next-generation|debut|debuts|debuted|debuting)\b",
            "user_growth": r"\b(user growth|subscriber growth|active users|subscriber addition|subscriber additions|new users|signups|signup|traffic surge|downloads|installs|active subscribers|mau|dau|mau growth|dau growth)\b",
            "earnings_beat": r"\b(beat|beats|beaten|beating|beat estimate|beat estimates|beat expectation|beat expectations|exceed|exceeds|exceeded|exceeding|surpass|surpasses|surpassed|surpassing|record earnings|earnings beat|profit beat|revenue beat)\b",
            "upgrades": r"\b(upgrade|upgraded|upgrades|upgrading|buy rating|outperform|outperforms|price target raised|raised target|raised price target|bullish call|top pick|overweight|strong buy)\b"
        }

        # Friendly names for categories
        neg_names = {
            "delays": "delays",
            "regulatory": "regulatory issues",
            "disappointment": "investor disappointment or stock declines",
            "weak_demand": "weak demand or slowing sales",
            "dilution": "stock dilution or capital offering",
            "missed": "missed expectations or lowered guidance"
        }
        pos_names = {
            "growth": "growth or expansion",
            "partnerships": "new partnerships or deals",
            "new_products": "new products or product launches",
            "user_growth": "user or subscriber growth",
            "earnings_beat": "earnings beats or exceeding expectations",
            "upgrades": "analyst upgrades or positive stock ratings"
        }

        # Check headline matches
        headline_neg_hits = {cat: bool(re.search(pat, headline_lower)) for cat, pat in neg_patterns.items()}
        headline_pos_hits = {cat: bool(re.search(pat, headline_lower)) for cat, pat in pos_patterns.items()}

        # Check text (headline + summary) matches
        text_neg_hits = {cat: bool(re.search(pat, text)) for cat, pat in neg_patterns.items()}
        text_pos_hits = {cat: bool(re.search(pat, text)) for cat, pat in pos_patterns.items()}

        # Check contrary/resolving evidence in the headline
        contrary_pat = r"\b(resolve|resolves|resolved|resolving|clear|clears|cleared|clearing|settle|settles|settled|settling|overcome|overcomes|overcame|overcoming|dismiss|dismisses|dismissed|dismissing|win|wins|won|winning|avoid|avoids|avoided|avoiding|unlikely|denies|denied|rejects|rejected|false|no dilution|no delays|no regulatory|no lawsuit)\b"
        has_contrary = bool(re.search(contrary_pat, headline_lower))

        # Check if headline contains negative or positive categories
        has_neg_headline = any(headline_neg_hits.values())
        has_pos_headline = any(headline_pos_hits.values())

        # Determine target/competitor relative position
        target_pos = min((text.find(kw) for kw in cat.get("primary", []) + cat.get("secondary", [])
                          if kw in text), default=9999)
        comp_pos = min((text.find(kw) for kw in comp_dict.keys() if kw in text), default=9999)
        target_first = target_pos <= comp_pos

        # Classify the general sentiment of the article (independent of target vs competitor)
        # Rule: Delays, regulatory, disappointment, weak demand, stock dilution, missed expectations
        # should be Potential Concern unless strong evidence suggests otherwise.
        is_neg = False
        is_pos = False
        neg_cat_matched = None
        pos_cat_matched = None

        # Determine matched negative category
        for c, hit in headline_neg_hits.items():
            if hit:
                neg_cat_matched = c
                break
        if not neg_cat_matched:
            for c, hit in text_neg_hits.items():
                if hit:
                    neg_cat_matched = c
                    break

        # Determine matched positive category
        for c, hit in headline_pos_hits.items():
            if hit:
                pos_cat_matched = c
                break
        if not pos_cat_matched:
            for c, hit in text_pos_hits.items():
                if hit:
                    pos_cat_matched = c
                    break

        if has_neg_headline and not has_contrary:
            is_neg = True
        elif any(text_neg_hits.values()) and not any(text_pos_hits.values()) and not has_contrary:
            is_neg = True
        elif has_pos_headline and not has_neg_headline:
            is_pos = True
        elif any(text_pos_hits.values()) and not any(text_neg_hits.values()):
            is_pos = True
        elif has_neg_headline and has_contrary:
            # Resolved negative is considered neutral or slightly positive
            is_pos = True if has_pos_headline else False
        else:
            # Uncertain / Mixed
            pass

        # ── Case 1: No competitor is mentioned ───────────────────
        if not competitor_mentioned:
            if is_neg:
                note = f"This news describes {neg_names[neg_cat_matched]} for {company_name}, presenting a potential concern." if neg_cat_matched else f"This news raises a potential concern for {company_name}."
                return {
                    "primary_beneficiary": "Unknown",
                    "primary_risk_holder": "Target Company",
                    "sentiment_for_target": "Bearish",
                    "beneficiary_note": note,
                }
            if is_pos:
                note = f"This news describes {pos_names[pos_cat_matched]} for {company_name}, which is good news." if pos_cat_matched else f"This news directly benefits {company_name}."
                return {
                    "primary_beneficiary": "Target Company",
                    "primary_risk_holder": "Unknown",
                    "sentiment_for_target": "Bullish",
                    "beneficiary_note": note,
                }

            # Uncertain / Neutral
            note = f"This news is about {company_name} but has mixed updates or no clear positive or negative signal."
            if has_contrary:
                note = f"This news mentions potential issues for {company_name} but suggests they may be resolved or avoided."
            return {
                "primary_beneficiary": "Unknown",
                "primary_risk_holder": "Unknown",
                "sentiment_for_target": "Neutral",
                "beneficiary_note": note,
            }

        # ── Case 2: Competitor is mentioned ─────────────────────────────
        # Positive news:
        if is_pos:
            if target_first:
                note = f"This news describes {pos_names[pos_cat_matched]} for {company_name}, which is good news and puts competitive pressure on {competitor_mentioned}." if pos_cat_matched else f"This positive news primarily benefits {company_name}, putting pressure on {competitor_mentioned}."
                return {
                    "primary_beneficiary": "Target Company",
                    "primary_risk_holder": competitor_mentioned,
                    "sentiment_for_target": "Bullish",
                    "beneficiary_note": note,
                }
            else:
                # Competitor wins -> Neutral for target (no indirect assumptions)
                note = f"This news describes {pos_names[pos_cat_matched]} for competitor {competitor_mentioned}. While it benefits them, we classify it as neutral for {company_name}." if pos_cat_matched else f"This news primarily benefits competitor {competitor_mentioned}. We do not assume indirect effects on {company_name}."
                return {
                    "primary_beneficiary": competitor_mentioned,
                    "primary_risk_holder": "Target Company",
                    "sentiment_for_target": "Neutral",
                    "beneficiary_note": note,
                }

        # Negative news:
        if is_neg:
            if target_first:
                note = f"This news describes {neg_names[neg_cat_matched]} for {company_name}, presenting a potential concern, which may benefit {competitor_mentioned}." if neg_cat_matched else f"This negative development primarily hurts {company_name} and may benefit {competitor_mentioned}."
                return {
                    "primary_beneficiary": competitor_mentioned,
                    "primary_risk_holder": "Target Company",
                    "sentiment_for_target": "Bearish",
                    "beneficiary_note": note,
                }
            else:
                # Competitor is hurt -> Neutral for target (no indirect assumptions)
                note = f"This news describes {neg_names[neg_cat_matched]} for competitor {competitor_mentioned}. While this affects them, we classify it as neutral for {company_name}." if neg_cat_matched else f"This negative news primarily affects competitor {competitor_mentioned}. We classify it as Neutral to avoid assumptions."
                return {
                    "primary_beneficiary": "Target Company",
                    "primary_risk_holder": competitor_mentioned,
                    "sentiment_for_target": "Neutral",
                    "beneficiary_note": note,
                }

        # Mixed or uncertain competitor context
        return {
            "primary_beneficiary": "Unknown",
            "primary_risk_holder": "Unknown",
            "sentiment_for_target": "Neutral",
            "beneficiary_note": f"This article mentions both {company_name} and competitor {competitor_mentioned} with mixed or unclear signals.",
        }


    # ─────────────────────────────────────────────────────────────────────────
    # Deduplication
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _is_duplicate(headline: str, seen: list) -> bool:
        words_a = set(re.findall(r"\w+", headline.lower()))
        if len(words_a) < 4:
            return False
        for art in seen:
            words_b = set(re.findall(r"\w+", art.get("headline", "").lower()))
            union = words_a | words_b
            if union and len(words_a & words_b) / len(union) > 0.55:
                return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Source tiering
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_source_tier(source: str) -> tuple:
        s = (source or "").lower().strip()
        tier1 = ["reuters", "bloomberg", "sec", "sec.gov", "ft.com", "financial times"]
        tier2 = ["cnbc", "wsj", "wall street journal", "barron", "the economist"]
        if any(t in s for t in tier1):
            return 1, 1.5
        if any(t in s for t in tier2):
            return 2, 1.0
        return 3, 0.5

    # ─────────────────────────────────────────────────────────────────────────
    # Financial impact detection
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def detect_financial_impacts(headline: str, summary: str) -> list:
        text = (headline + " " + summary).lower()
        impacts = []
        categories = {
            "Revenue":     (["revenue", "sales", "turnover"], ["grow", "surge", "record"], ["decline", "fall", "miss"]),
            "Margins":     (["margin", "profitability"], ["expand", "improve"], ["squeeze", "compress", "shrink"]),
            "Demand":      (["demand", "orders", "bookings", "subscribers"], ["strong", "surging"], ["weak", "slowing"]),
            "Competition": (["competition", "rival", "market share"], ["gain", "dominant"], ["lose", "erosion"]),
            "Valuation":   (["price target", "valuation", "pe ratio"], ["upgrade", "raise"], ["downgrade", "lower"]),
            "Guidance":    (["guidance", "outlook", "forecast", "estimates"], ["raise", "beat"], ["cut", "lower"]),
        }
        for cat, (kws, pos, neg) in categories.items():
            if any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in kws):
                direction = "Neutral"
                if any(i in text for i in pos):
                    direction = "Positive"
                elif any(i in text for i in neg):
                    direction = "Negative"
                impacts.append({"category": cat, "direction": direction})
        return impacts

    # ─────────────────────────────────────────────────────────────────────────
    # Main entry-point
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def analyze_news(cls, ticker: str) -> dict:
        """
        Fetch, filter, and analyse Finnhub news for the target ticker.
        Identifies primary beneficiary and risk holder per article.
        Only articles where the target company is the primary beneficiary
        count as Bullish; only articles where it is the primary risk holder
        count as Bearish.
        """
        api_key = settings.FINNHUB_API_KEY
        if not api_key or api_key == "your_finnhub_api_key_here":
            logger.error(f"[SentimentService] Missing FINNHUB_API_KEY for {ticker}")
            return {"error": "Missing Finnhub API Key"}

        end_date   = datetime.now()
        start_date = end_date - timedelta(days=7)
        params     = {
            "symbol": ticker,
            "from":   start_date.strftime("%Y-%m-%d"),
            "to":     end_date.strftime("%Y-%m-%d"),
            "token":  api_key,
        }

        try:
            logger.info(f"[SentimentService] Fetching Finnhub news for {ticker}")
            resp = requests.get(
                "https://finnhub.io/api/v1/company-news", params=params, timeout=10
            )

            if resp.status_code == 429:
                return {"error": "Rate Limit Exceeded (Finnhub)"}
            if resp.status_code in (401, 403):
                return {"error": "Unauthorized / Invalid Finnhub API Key"}
            resp.raise_for_status()
            raw = resp.json()

            if not raw:
                return {"error": "No recent news found"}

            cat          = cls._catalogue(ticker)
            company_name = cat.get("name", ticker.upper())

            # ── Phase 1: Relevance filtering & deduplication ─────────────
            relevant_pool   = []
            excluded_list   = []

            for art in raw:
                hl  = art.get("headline", "").strip()
                sm  = art.get("summary",  "").strip()
                src = art.get("source",   "Unknown")

                if not hl:
                    continue

                label, exc_reason = cls.classify_relevance(hl, sm, ticker)

                if label == "NOT_RELEVANT":
                    excluded_list.append({"title": hl, "source": src, "reason": exc_reason})
                    continue

                if cls._is_duplicate(hl, relevant_pool):
                    excluded_list.append({
                        "title":  hl,
                        "source": src,
                        "reason": "Duplicate — highly similar to an already-included article",
                    })
                    continue

                art["relevance"] = label
                relevant_pool.append(art)

            relevant_count = len(relevant_pool)
            excluded_count = len(excluded_list)

            # ── Empty case ───────────────────────────────────────────────
            if not relevant_pool:
                return {
                    "sentiment_scores":        {"Bullish": "0.0%", "Bearish": "0.0%", "Neutral": "100.0%"},
                    "article_count":           0,
                    "relevant_articles_count": 0,
                    "excluded_articles_count": excluded_count,
                    "bullish_count":           0,
                    "bearish_count":           0,
                    "neutral_count":           0,
                    "good_news":               [],
                    "potential_concerns":      [],
                    "news_worth_watching":     [],
                    "bottom_line":             (
                        f"There are no relevant news stories about {company_name} "
                        f"in the past 7 days. This is not necessarily good or bad — "
                        f"it simply means nothing major has been reported recently."
                    ),
                    "confidence_score":        10.0,
                    "confidence_explanation":  (
                        f"Confidence is 10% — no relevant articles found. "
                        f"All {excluded_count} fetched articles were excluded as "
                        f"not directly related to {company_name}."
                    ),
                    "key_events":              [],
                    "financial_impacts":       [],
                    "recent_articles":         [],
                    "excluded_articles":       excluded_list[:20],
                }

            # ── Phase 2: Per-article beneficiary analysis ────────────────
            analyzed = relevant_pool[:15]

            w_bull = w_bear = w_neut = total_w = 0.0
            bull_count = bear_count = neut_count = 0

            good_news:            list = []
            potential_concerns:   list = []
            news_worth_watching:  list = []
            key_events:           list = []
            fin_impacts:          list = []
            fmt_articles:         list = []

            for art in analyzed:
                hl  = art.get("headline", "")
                sm  = art.get("summary",  "")
                src = art.get("source",   "Unknown")
                rel = art.get("relevance", "RELEVANT")

                tier, weight = cls.get_source_tier(src)
                if rel == "PARTIAL":
                    weight *= 0.5

                binfo = cls.detect_beneficiary(hl, sm, ticker)
                tgt_sentiment = binfo["sentiment_for_target"]

                entry = {
                    "headline":           hl,
                    "source":             src,
                    "target_company":     company_name,
                    "primary_beneficiary": binfo["primary_beneficiary"],
                    "primary_risk_holder": binfo["primary_risk_holder"],
                    "beneficiary_note":   binfo["beneficiary_note"],
                    "sentiment":          tgt_sentiment,
                    "relevance":          rel,
                }

                if tgt_sentiment == "Bullish":
                    w_bull += weight
                    bull_count += 1
                    if len(good_news) < 5:
                        good_news.append(entry)
                elif tgt_sentiment == "Bearish":
                    w_bear += weight
                    bear_count += 1
                    if len(potential_concerns) < 5:
                        potential_concerns.append(entry)
                else:
                    w_neut += weight
                    neut_count += 1
                    if len(news_worth_watching) < 5:
                        news_worth_watching.append(entry)

                total_w += weight

                fin_impacts.extend(cls.detect_financial_impacts(hl, sm))

                if len(key_events) < 5:
                    key_events.append({
                        "event":     hl,
                        "source":    src,
                        "date":      datetime.fromtimestamp(art.get("datetime", 0)).strftime("%Y-%m-%d"),
                        "sentiment": tgt_sentiment,
                    })

                fmt_articles.append({
                    "title":             hl,
                    "source":            src,
                    "tier":              f"Tier {tier}",
                    "relevance":         rel,
                    "beneficiary":       binfo["primary_beneficiary"],
                    "risk_holder":       binfo["primary_risk_holder"],
                    "datetime":          datetime.fromtimestamp(art.get("datetime", 0)).strftime("%Y-%m-%d %H:%M"),
                    "url":               art.get("url"),
                    "sentiment":         tgt_sentiment,
                })

            total_analyzed = len(analyzed)

            bull_pct = (w_bull / total_w * 100) if total_w else 0.0
            bear_pct = (w_bear / total_w * 100) if total_w else 0.0
            neut_pct = (w_neut / total_w * 100) if total_w else 0.0

            # ── Phase 3: Confidence score ────────────────────────────────
            vol_score   = min(relevant_count * 4, 40)
            t12_count   = sum(1 for a in fmt_articles if "Tier 3" not in a["tier"])
            src_score   = (t12_count / total_analyzed * 30) if total_analyzed else 0.0
            highest_pct = max(bull_pct, bear_pct, neut_pct)
            agr_score   = (highest_pct / 100.0) * 25

            base_conf       = vol_score + src_score + agr_score
            penalty_applied = relevant_count < 5
            conf_score      = round(min(base_conf * (0.70 if penalty_applied else 1.0), 95.0), 1)

            conf_expl = (
                f"Confidence {conf_score}% = "
                f"Volume {vol_score:.1f}/40 ({relevant_count} relevant articles) + "
                f"Source quality {src_score:.1f}/30 ({t12_count} premium sources) + "
                f"Consensus {agr_score:.1f}/25 ({highest_pct:.1f}% dominant sentiment)."
            )
            if penalty_applied:
                conf_expl += (
                    f" ⚠️ 30% penalty applied — fewer than 5 relevant articles found "
                    f"({relevant_count} total)."
                )
            conf_expl += " Capped at 95% to reflect inherent market uncertainty."

            # ── Phase 4: Bottom Line (beginner summary) ──────────────────
            if bull_pct >= 55:
                mood = "mostly positive"
                mood_detail = (
                    f"The recent news about {company_name} is leaning positive. "
                    f"More stories suggest things are going well for the company than not."
                )
            elif bear_pct >= 55:
                mood = "mostly cautious"
                mood_detail = (
                    f"The recent news about {company_name} raises some concerns. "
                    f"More stories point to challenges than opportunities right now."
                )
            elif bull_pct > bear_pct:
                mood = "slightly positive"
                mood_detail = (
                    f"The recent news about {company_name} is slightly more positive than negative, "
                    f"but the picture is mixed. It is worth keeping an eye on upcoming developments."
                )
            elif bear_pct > bull_pct:
                mood = "slightly cautious"
                mood_detail = (
                    f"The recent news about {company_name} is slightly more cautious than positive. "
                    f"Nothing alarming, but there are a few things worth watching."
                )
            else:
                mood = "neutral"
                mood_detail = (
                    f"The recent news about {company_name} is balanced — "
                    f"no strong positive or negative signals stand out right now."
                )

            bottom_line = (
                f"📋 **Bottom Line**: Based on {relevant_count} relevant news articles "
                f"from the past 7 days, the overall news mood for {company_name} is **{mood}**. "
                f"{mood_detail} "
                f"We found {bull_count} positive stories, {bear_count} concerning stories, "
                f"and {neut_count} neutral updates. "
                f"Our confidence in this reading is {conf_score}% — "
                f"{'this is solid given the volume of news.' if conf_score >= 60 else 'lower than usual due to limited recent coverage.'}"
            )

            return {
                "sentiment_scores": {
                    "Bullish": f"{bull_pct:.1f}%",
                    "Bearish": f"{bear_pct:.1f}%",
                    "Neutral": f"{neut_pct:.1f}%",
                },
                "article_count":           total_analyzed,
                "relevant_articles_count": relevant_count,
                "excluded_articles_count": excluded_count,
                "bullish_count":           bull_count,
                "bearish_count":           bear_count,
                "neutral_count":           neut_count,
                "good_news":               good_news,
                "potential_concerns":      potential_concerns,
                "news_worth_watching":     news_worth_watching,
                "bottom_line":             bottom_line,
                "confidence_score":        conf_score,
                "confidence_explanation":  conf_expl,
                "key_events":              key_events,
                "financial_impacts":       fin_impacts,
                "recent_articles":         fmt_articles[:8],
                "excluded_articles":       excluded_list[:20],
            }

        except Exception as e:
            logger.error(f"[SentimentService] Error fetching news for {ticker}: {e}")
            return {"error": f"API Error: {str(e)}"}
