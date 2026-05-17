"""
FinShield — Service OSINT
Sources : OpenSanctions + Google (titres) + DuckDuckGo
"""

from __future__ import annotations
import json
import time
import re
from dataclasses import dataclass, field
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# ── Mots-clés négatifs ────────────────────────────────────────────────────────
NEGATIVE_KEYWORDS = {
    "fr": [
        "corruption", "condamné", "condamnation", "fraude", "escroquerie",
        "blanchiment", "détournement", "sanction", "mis en examen",
        "garde à vue", "perquisition", "jugement", "tribunal", "prison",
        "amende", "trafic", "terrorisme", "faillite", "liquidation",
        "redressement judiciaire", "pot-de-vin", "renvoi en jugement",
    ],
    "en": [
        "corruption", "convicted", "conviction", "fraud", "scam",
        "money laundering", "embezzlement", "sanction", "indicted",
        "arrested", "charged", "trial", "court", "prison", "jail",
        "fine", "penalty", "trafficking", "terrorism", "bribery",
        "bankruptcy", "liquidation", "watchlist", "blacklist", "sentenced",
    ],
}


def _build_queries(entity_name: str, entity_type: str, country: str = "") -> list[dict]:
    """Construit les requêtes négatives ciblées pour l'entité."""
    q = f'"{entity_name}"'
    c = f" {country}" if country else ""
    queries = [
        {"q": f'{q} corruption OR fraude OR condamné OR sanction{c}',         "label": "Corruption / Fraude (FR)"},
        {"q": f'{q} tribunal OR jugement OR "mis en examen" OR "garde à vue"{c}', "label": "Judiciaire (FR)"},
        {"q": f'{q} blanchiment OR "financement terrorisme" OR trafic{c}',    "label": "Criminalité financière (FR)"},
        {"q": f'{q} corruption OR fraud OR convicted OR sanction{c}',         "label": "Corruption / Fraud (EN)"},
        {"q": f'{q} "money laundering" OR terrorism OR trafficking{c}',       "label": "Financial crime (EN)"},
        {"q": f'{q} arrested OR indicted OR sentenced OR trial{c}',           "label": "Legal proceedings (EN)"},
        {"q": f'{q} PEP OR ministre OR député OR "politically exposed"{c}',   "label": "PEP / Politique"},
    ]
    if entity_type == "company":
        queries.append({"q": f'{q} faillite OR liquidation OR "fraude fiscale" OR perquisition', "label": "Entreprise"})
    return queries


def _is_negative(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in NEGATIVE_KEYWORDS["fr"] + NEGATIVE_KEYWORDS["en"])


def _clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    for esc, rep in [("&amp;","&"),("&quot;",'"'),("&#39;","'"),("&lt;","<"),("&gt;",">")]:
        text = text.replace(esc, rep)
    return text.strip()


def _extract_domain(url: str) -> str:
    try:
        m = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return m.group(1) if m else "Google"
    except Exception:
        return "Google"


# ── Google Search (titres uniquement) ─────────────────────────────────────────
def _search_google(query: str, max_results: int = 8) -> list[dict]:
    """
    Récupère les titres des résultats Google sans lire les articles.
    Extraction des balises <h3> des résultats de recherche uniquement.
    """
    results = []
    try:
        r = requests.get(
            "https://www.google.com/search",
            params={"q": query, "num": max_results, "hl": "fr", "gl": "fr"},
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            },
            timeout=10,
        )
        if r.status_code != 200:
            return []

        html = r.text
        seen = set()

        # Pattern 1 : titres avec classe LC20lb (résultats standards Google)
        titles = re.findall(r'<h3[^>]*class="[^"]*LC20lb[^"]*"[^>]*>(.*?)</h3>', html)
        urls   = re.findall(r'href="(https?://[^"&]{10,})"[^>]*>\s*<h3', html)

        for i, raw_title in enumerate(titles[:max_results]):
            title = _clean_html(raw_title)
            if not title or len(title) < 8 or title in seen:
                continue
            seen.add(title)
            url = urls[i] if i < len(urls) else ""
            results.append({
                "title":  title,
                "url":    url,
                "source": _extract_domain(url),
                "engine": "Google",
            })

        # Pattern 2 fallback : balises <h3> génériques
        if not results:
            for raw_title in re.findall(r'<h3[^>]*>(.*?)</h3>', html)[:max_results]:
                title = _clean_html(raw_title)
                if title and len(title) > 8 and title not in seen:
                    seen.add(title)
                    results.append({
                        "title":  title,
                        "url":    "",
                        "source": "Google",
                        "engine": "Google",
                    })

    except Exception:
        pass
    return results[:max_results]


# ── DuckDuckGo ────────────────────────────────────────────────────────────────
def _search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """DuckDuckGo Instant Answer API — titres et liens."""
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            timeout=8,
            headers={"User-Agent": "FinShield-OSINT/1.0"},
        )
        data = r.json()
        results = []
        if data.get("AbstractText"):
            results.append({
                "title":  data["AbstractText"][:120],
                "url":    data.get("AbstractURL", ""),
                "source": data.get("AbstractSource", "DuckDuckGo"),
                "engine": "DuckDuckGo",
            })
        for item in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(item, dict) and item.get("Text"):
                results.append({
                    "title":  item["Text"][:120],
                    "url":    item.get("FirstURL", ""),
                    "source": "DuckDuckGo",
                    "engine": "DuckDuckGo",
                })
        return results
    except Exception:
        return []


# ── OpenSanctions ─────────────────────────────────────────────────────────────
def _search_opensanctions(entity_name: str) -> list[dict]:
    hits = []
    try:
        r = requests.post(
            "https://api.opensanctions.org/match/default",
            json={"queries": {"q1": {"schema": "Person", "properties": {"name": [entity_name]}}}},
            timeout=10,
        )
        if r.status_code == 200:
            for _, res in r.json().get("responses", {}).items():
                for match in res.get("results", []):
                    if match.get("score", 0) > 0.5:
                        props = match.get("properties", {})
                        hits.append({
                            "name":      props.get("name", [entity_name])[0],
                            "score":     round(match["score"], 2),
                            "datasets":  match.get("datasets", []),
                            "countries": props.get("country", []),
                            "source_url": f"https://www.opensanctions.org/entities/{match.get('id','')}",
                            "source":    "OpenSanctions",
                        })
    except Exception:
        pass
    return hits


# ── Résultat ──────────────────────────────────────────────────────────────────
@dataclass
class OSINTResult:
    entity: str
    entity_type: str = "person"
    risk_score: float = 0.0
    risk_level: str = "low"
    summary: str = ""
    sanctions_hits: list[dict] = field(default_factory=list)
    pep_hits: list[dict] = field(default_factory=list)
    adverse_media: list[dict] = field(default_factory=list)
    legal_hits: list[dict] = field(default_factory=list)
    sources_checked: list[str] = field(default_factory=list)
    raw_analysis: str = ""
    error: Optional[str] = None

    @property
    def risk_badge(self) -> str:
        return {"low":"🟢 Faible","medium":"🟡 Modéré","high":"🔴 Élevé","critical":"🟣 Critique"}.get(self.risk_level,"⚪")


# ── Moteur principal ──────────────────────────────────────────────────────────
def analyze_entity(
    entity_name: str,
    entity_type: str = "person",
    country: str = "",
    birth_date: str = "",
    api_key: str = "",
    additional_context: str = "",
) -> OSINTResult:

    result = OSINTResult(entity=entity_name, entity_type=entity_type)
    all_media: list[dict] = []
    sources = []

    # 1. OpenSanctions
    result.sanctions_hits = _search_opensanctions(entity_name)
    sources.append("OpenSanctions (ONU, UE, OFAC, SECO, UK HMT, 100+ listes)")

    # 2. Google — 4 requêtes ciblées
    queries = _build_queries(entity_name, entity_type, country)
    for q in queries[:4]:
        hits = _search_google(q["q"], max_results=6)
        for h in hits:
            h["query_label"] = q["label"]
            h["is_negative"] = _is_negative(h.get("title", ""))
        all_media.extend(hits)
        time.sleep(1.5)
    sources.append("Google Search (titres uniquement — requêtes négatives ciblées)")

    # 3. DuckDuckGo — 2 requêtes complémentaires
    for q in queries[1:3]:
        hits = _search_duckduckgo(q["q"], max_results=4)
        for h in hits:
            h["query_label"] = q["label"]
            h["is_negative"] = _is_negative(h.get("title", ""))
        all_media.extend(hits)
        time.sleep(0.5)
    sources.append("DuckDuckGo Search (complément)")

    # Déduplication + tri négatifs en premier
    seen, unique = set(), []
    for item in all_media:
        key = item.get("title", "")[:60].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    unique.sort(key=lambda x: not x.get("is_negative", False))
    result.adverse_media = unique[:20]
    result.sources_checked = sources

    # Scoring préliminaire
    negative_count = sum(1 for m in result.adverse_media if m.get("is_negative"))
    base_score = 0.0
    if result.sanctions_hits:
        base_score = max(base_score, max(h.get("score", 0) for h in result.sanctions_hits) * 0.85)
    if negative_count >= 5:   base_score = max(base_score, 0.65)
    elif negative_count >= 3: base_score = max(base_score, 0.45)
    elif negative_count >= 1: base_score = max(base_score, 0.25)

    # 4. Claude AI
    if api_key:
        analysis = _claude_analyze(
            entity_name, entity_type, country, birth_date,
            result.sanctions_hits, result.adverse_media,
            negative_count, api_key, additional_context,
        )
        result.raw_analysis = analysis.get("analysis", "")
        result.summary      = analysis.get("summary", "")
        result.risk_level   = analysis.get("risk_level", "low")
        result.risk_score   = analysis.get("risk_score", base_score)
        result.pep_hits     = analysis.get("pep_hits", [])
        result.legal_hits   = analysis.get("legal_hits", [])
    else:
        result.risk_score = round(min(base_score, 1.0), 2)
        result.risk_level = _score_to_level(result.risk_score)
        result.summary = (
            f"{negative_count} résultat(s) négatif(s) sur {len(result.adverse_media)} trouvés "
            f"(Google + DuckDuckGo) | {len(result.sanctions_hits)} hit(s) sanctions. "
            "Ajoutez une clé Anthropic pour la synthèse IA."
        )
    return result


def _score_to_level(s: float) -> str:
    if s < 0.25: return "low"
    if s < 0.50: return "medium"
    if s < 0.75: return "high"
    return "critical"


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def _claude_analyze(entity_name, entity_type, country, birth_date,
                     sanctions_hits, media_hits, negative_count, api_key, additional_context="") -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    neg_hits   = [m for m in media_hits if m.get("is_negative")]
    other_hits = [m for m in media_hits if not m.get("is_negative")]

    neg_txt = "\n".join(
        f"- [{m.get('engine','?')}] {m.get('title','')} | {m.get('source','')} | {m.get('url','')}"
        for m in neg_hits[:12]
    ) or "Aucun"

    other_txt = "\n".join(
        f"- [{m.get('engine','?')}] {m.get('title','')} | {m.get('source','')}"
        for m in other_hits[:4]
    ) or "Aucun"

    prompt = f"""Tu es un analyste senior AML/KYC et due diligence.

ENTITÉ : {entity_name} | Type : {entity_type} | Pays : {country or 'N/A'} | DDN : {birth_date or 'N/A'}
{f"Contexte : {additional_context}" if additional_context else ""}

=== OpenSanctions ===
{json.dumps(sanctions_hits[:5], ensure_ascii=False) if sanctions_hits else "Aucun"}

=== Résultats NÉGATIFS Google/DuckDuckGo ({negative_count} hits) ===
{neg_txt}

=== Autres résultats (contexte) ===
{other_txt}

INSTRUCTIONS :
- Les résultats Google/DDG sont des TITRES d'articles — évalue leur pertinence pour l'entité.
- Si plusieurs titres convergent sur un même risque, c'est un signal fort.
- Identifie : sanctions, PEP, fraude, corruption, condamnations, blanchiment, terrorisme.
- Ne pas inventer — base-toi uniquement sur les données ci-dessus.
- Réponds UNIQUEMENT en JSON valide :

{{
  "summary": "Résumé exécutif 2-3 phrases",
  "risk_level": "low|medium|high|critical",
  "risk_score": 0.0,
  "analysis": "Analyse détaillée (400 mots max)",
  "pep_hits": [{{"name":"...","position":"...","country":"...","source":"..."}}],
  "legal_hits": [{{"description":"...","type":"...","source":"..."}}],
  "red_flags": ["..."],
  "recommendation": "Accepter / Surveiller / Refuser — justification courte"
}}"""

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "summary": f"Erreur : {e}", "risk_level": "low", "risk_score": 0.0,
            "analysis": "", "pep_hits": [], "legal_hits": [], "red_flags": [],
            "recommendation": "Erreur — relancez.",
        }
