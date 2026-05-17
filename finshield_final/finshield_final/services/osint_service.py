"""
FinShield — Service OSINT v2 (amélioré)
Sources : OpenSanctions + Google (titres) + DuckDuckGo + Bing + Brave
Logique renforcée : requêtes croisées négatives, détection adverse media.
"""

from __future__ import annotations
import json
import time
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import quote_plus, urlparse

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# ── Mots-clés négatifs (détection dans les titres) ───────────────────────────
NEGATIVE_KEYWORDS = [
    # FR — corruption & fraude
    "corruption", "corrompu", "corruptible", "fraudeur",
    "condamné", "condamnation", "fraude", "escroquerie",
    "blanchiment", "détournement", "détournés", "malversation",
    "sanction", "sanctionné", "mis en examen", "inculpé",
    "garde à vue", "perquisition", "jugement", "tribunal",
    "prison", "emprisonné", "amende", "pénalité",
    "trafic", "trafiquant", "terrorisme", "bribery",
    "faillite", "liquidation", "redressement judiciaire",
    "pot-de-vin", "pots-de-vin", "renvoi en jugement",
    "abus de biens sociaux", "recel", "extorsion", "escroq",
    "liste noire", "blacklist", "gel des avoirs", "interdiction",
    "poursuite", "inculpation", "mise en cause", "accusé",
    "fraude fiscale", "évasion fiscale", "blanchiment d'argent",
    "financement du terrorisme", "trafic d'influence",
    "abus de pouvoir", "favoritisme", "collusion", "entente illicite",
    # EN — corruption & fraud
    "corruption", "convicted", "conviction", "fraud", "scam",
    "money laundering", "embezzlement", "sanction", "sanctioned",
    "indicted", "indictment", "arrested", "charged", "trial",
    "court", "prison", "jail", "fine", "penalty",
    "trafficking", "terrorism", "bribery", "kickback",
    "bankruptcy", "liquidation", "watchlist", "blacklist",
    "sentenced", "investigation", "probe", "misconduct",
    "allegation", "accused", "implicated", "wrongdoing",
    "unethical", "tax evasion", "money laundering",
    "asset freeze", "travel ban", "ofac", "embargo",
    "conflict of interest", "regulatory breach", "non-compliance",
    "human rights abuse", "environmental violation", "corrupt",
    "under investigation", "red flag", "compliance risk",
    "adverse", "negative press", "bad press", "scandal",
    # Listes de sanctions spécifiques
    "ofac", "sdn list", "un sanctions", "eu sanctions",
    "uk sanctions", "interpol", "red notice",
]

# Domaines haute crédibilité (boost scoring)
SOURCE_CREDIBILITY = {
    "opensanctions.org": 2.0, "ofac.treas.gov": 2.0,
    "amf-france.org": 2.0, "acpr.banque-france.fr": 2.0,
    "legifrance.gouv.fr": 2.0, "justice.fr": 2.0,
    "bodacc.fr": 1.8, "interpol.int": 2.0,
    "europol.europa.eu": 2.0, "tracfin.gouv.fr": 2.0,
    "sec.gov": 2.0, "pacer.gov": 1.8,
    "lemonde.fr": 1.5, "lefigaro.fr": 1.5,
    "reuters.com": 1.6, "bloomberg.com": 1.6,
    "ft.com": 1.6, "bfmtv.com": 1.3,
    "lesechos.fr": 1.5, "latribune.fr": 1.4,
    "theguardian.com": 1.5, "nytimes.com": 1.5,
    "bbc.com": 1.4, "signal-arnaques.com": 1.5,
    "cybermalveillance.gouv.fr": 1.8,
}


def _build_queries(entity_name: str, entity_type: str, country: str = "") -> list[dict]:
    """
    Construit un catalogue complet de requêtes négatives croisées.
    Chaque requête combine le nom entre guillemets avec des termes négatifs.
    """
    q = f'"{entity_name}"'
    c = f" {country}" if country else ""

    queries = [
        # ── Bloc 1 : Corruption & Fraude (FR) ──────────────────────────────
        {
            "q": f'{q} corruption OR fraude OR condamné OR "mis en examen" OR inculpé{c}',
            "label": "Corruption / Fraude FR", "category": "fraud", "gravity": "eleve"
        },
        {
            "q": f'{q} blanchiment OR "financement terrorisme" OR "abus de biens sociaux" OR détournement{c}',
            "label": "Criminalité financière FR", "category": "fraud", "gravity": "eleve"
        },
        {
            "q": f'{q} escroquerie OR extorsion OR "trafic d\'influence" OR recel OR malversation{c}',
            "label": "Infractions pénales FR", "category": "fraud", "gravity": "eleve"
        },
        {
            "q": f'{q} "pot-de-vin" OR collusion OR "fraude fiscale" OR "évasion fiscale" OR favoritisme{c}',
            "label": "Corruption passive/active FR", "category": "fraud", "gravity": "eleve"
        },
        # ── Bloc 2 : Procédures judiciaires (FR) ──────────────────────────
        {
            "q": f'{q} tribunal OR jugement OR condamnation OR "garde à vue" OR perquisition{c}',
            "label": "Procédures judiciaires FR", "category": "judicial", "gravity": "eleve"
        },
        {
            "q": f'{q} prison OR emprisonné OR amende OR pénalité OR poursuite{c}',
            "label": "Sanctions pénales FR", "category": "judicial", "gravity": "eleve"
        },
        {
            "q": f'{q} "mise en examen" OR inculpation OR "renvoi en jugement" OR arrêté{c}',
            "label": "Inculpation FR", "category": "judicial", "gravity": "eleve"
        },
        # ── Bloc 3 : Sanctions & Listes (FR/EN) ───────────────────────────
        {
            "q": f'{q} sanction OR sanctionné OR "liste noire" OR blacklist OR "gel des avoirs"{c}',
            "label": "Sanctions & Listes FR", "category": "sanctions", "gravity": "eleve"
        },
        {
            "q": f'{q} OFAC OR embargo OR "interdiction de voyager" OR "UN sanctions" OR "EU sanctions"',
            "label": "Listes internationales", "category": "sanctions", "gravity": "eleve"
        },
        {
            "q": f'{q} watchlist OR "asset freeze" OR "travel ban" OR "UK sanctions" OR "SDN list"',
            "label": "Restrictions internationales", "category": "sanctions", "gravity": "eleve"
        },
        # ── Bloc 4 : Corruption & Fraud (EN) ──────────────────────────────
        {
            "q": f'{q} corruption OR fraud OR convicted OR bribery OR indicted{c}',
            "label": "Corruption / Fraud EN", "category": "fraud", "gravity": "eleve"
        },
        {
            "q": f'{q} "money laundering" OR terrorism OR trafficking OR embezzlement{c}',
            "label": "Financial crime EN", "category": "fraud", "gravity": "eleve"
        },
        {
            "q": f'{q} arrested OR sentenced OR prison OR jail OR "criminal charges"{c}',
            "label": "Legal proceedings EN", "category": "judicial", "gravity": "eleve"
        },
        {
            "q": f'{q} misconduct OR wrongdoing OR "regulatory breach" OR "non-compliance"{c}',
            "label": "Misconduct EN", "category": "reputation", "gravity": "moyen"
        },
        {
            "q": f'{q} scandal OR allegation OR accused OR implicated OR investigation{c}',
            "label": "Allegations EN", "category": "reputation", "gravity": "moyen"
        },
        {
            "q": f'{q} kickback OR "conflict of interest" OR "tax evasion" OR "insider trading"{c}',
            "label": "Financial misconduct EN", "category": "fraud", "gravity": "eleve"
        },
        # ── Bloc 5 : Presse negative ────────────────────────────────────────
        {
            "q": f'{q} "adverse media" OR "negative news" OR "bad press" OR "red flag" OR "compliance risk"',
            "label": "Adverse media", "category": "reputation", "gravity": "moyen"
        },
        {
            "q": f'{q} enquête OR investigation OR probe OR "under investigation" OR suspect{c}',
            "label": "Enquêtes", "category": "judicial", "gravity": "moyen"
        },
        # ── Bloc 6 : PEP / Politique ───────────────────────────────────────
        {
            "q": f'{q} PEP OR "politically exposed" OR ministre OR député OR sénateur{c}',
            "label": "PEP / Politique", "category": "pep", "gravity": "moyen"
        },
        # ── Bloc 7 : Sources officielles ───────────────────────────────────
        {
            "q": f'site:opensanctions.org {q}',
            "label": "OpenSanctions web", "category": "sanctions", "gravity": "eleve"
        },
        {
            "q": f'site:ofac.treas.gov {q}',
            "label": "OFAC", "category": "sanctions", "gravity": "eleve"
        },
        {
            "q": f'site:amf-france.org {q}',
            "label": "AMF France", "category": "sanctions", "gravity": "eleve"
        },
        {
            "q": f'site:sec.gov {q}',
            "label": "SEC USA", "category": "sanctions", "gravity": "eleve"
        },
        {
            "q": f'site:signal-arnaques.com {q}',
            "label": "Signal Arnaques", "category": "reputation", "gravity": "eleve"
        },
    ]

    # Requêtes supplémentaires pour les entreprises
    if entity_type in ("company", "Entreprise", "Groupe bancaire"):
        queries += [
            {
                "q": f'{q} faillite OR liquidation OR "fraude fiscale" OR perquisition OR "redressement judiciaire"{c}',
                "label": "Défaillance entreprise FR", "category": "judicial", "gravity": "moyen"
            },
            {
                "q": f'{q} bankruptcy OR insolvency OR "regulatory action" OR "enforcement action"{c}',
                "label": "Défaillance entreprise EN", "category": "judicial", "gravity": "moyen"
            },
            {
                "q": f'{q} "class action" OR lawsuit OR "regulatory fine" OR settlement{c}',
                "label": "Litiges entreprise EN", "category": "judicial", "gravity": "moyen"
            },
            {
                "q": f'{q} amende OR poursuite OR "autorité de régulation" OR "contrôle fiscal"{c}',
                "label": "Régulation FR", "category": "sanctions", "gravity": "eleve"
            },
        ]

    return queries


def _is_negative(text: str) -> bool:
    """Vérifie si un titre/snippet contient des mots-clés négatifs."""
    t = text.lower()
    return any(kw.lower() in t for kw in NEGATIVE_KEYWORDS)


def _clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    for esc, rep in [("&amp;", "&"), ("&quot;", '"'), ("&#39;", "'"),
                     ("&lt;", "<"), ("&gt;", ">"), ("&nbsp;", " ")]:
        text = text.replace(esc, rep)
    return text.strip()


def _extract_domain(url: str) -> str:
    try:
        m = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return m.group(1) if m else ""
    except Exception:
        return ""


def _get_credibility(url: str) -> float:
    domain = _extract_domain(url)
    return SOURCE_CREDIBILITY.get(domain, 1.0)


# ── Google Search (titres uniquement, sans scraping des articles) ─────────────
def _search_google(query: str, max_results: int = 8) -> list[dict]:
    """
    Lit uniquement les titres des résultats Google.
    Plusieurs patterns HTML pour couvrir les variantes de layout Google.
    """
    results = []
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    ]
    import random
    ua = random.choice(ua_list)

    try:
        r = requests.get(
            "https://www.google.com/search",
            params={"q": query, "num": max_results + 3, "hl": "fr", "gl": "fr"},
            headers={
                "User-Agent": ua,
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.google.com/",
            },
            timeout=12,
        )
        if r.status_code not in (200, 301, 302):
            return []

        html = r.text
        seen = set()

        # ── Pattern 1 : LC20lb (résultats standards) ──────────────────────
        # Extraire titre + URL ensemble
        block_pattern = re.compile(
            r'<a[^>]+href="(https?://[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>',
            re.DOTALL
        )
        for url_raw, title_raw in block_pattern.findall(html):
            title = _clean_html(title_raw)
            url = url_raw.split("&")[0]  # nettoyer les paramètres Google
            if not title or len(title) < 6 or title in seen:
                continue
            # Filtrer les URLs Google internes
            if any(x in url for x in ["google.com/search", "accounts.google", "support.google"]):
                continue
            seen.add(title)
            results.append({
                "title": title,
                "url": url,
                "source": _extract_domain(url),
                "engine": "Google",
            })
            if len(results) >= max_results:
                break

        # ── Pattern 2 fallback : h3 génériques avec URL reconstituée ────
        if len(results) < 3:
            # Extraire les URLs de redirection Google (/url?q=...)
            redirect_urls = re.findall(r'/url\?q=(https?://[^&"]+)', html)
            h3_titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html)

            for i, raw_title in enumerate(h3_titles[:max_results + 5]):
                title = _clean_html(raw_title)
                if not title or len(title) < 6 or title in seen:
                    continue
                url = redirect_urls[i] if i < len(redirect_urls) else ""
                if any(x in url for x in ["google.com", "accounts.google"]):
                    continue
                seen.add(title)
                results.append({
                    "title": title,
                    "url": url,
                    "source": _extract_domain(url) if url else "Google",
                    "engine": "Google",
                })
                if len(results) >= max_results:
                    break

    except Exception:
        pass

    return results[:max_results]


# ── DuckDuckGo HTML ───────────────────────────────────────────────────────────
def _search_duckduckgo(query: str, max_results: int = 6) -> list[dict]:
    """DuckDuckGo HTML search — plus fiable que l'API Instant Answer pour ce cas."""
    results = []
    try:
        from bs4 import BeautifulSoup
        q = quote_plus(query)
        r = requests.get(
            f"https://html.duckduckgo.com/html/?q={q}&kl=fr-fr&kp=-1",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            },
            timeout=12,
        )
        if r.status_code != 200 or len(r.text) < 500:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        seen = set()
        for item in soup.select(".result, .web-result"):
            a = (item.find("a", class_="result__a")
                 or item.find("a", attrs={"data-testid": "result-title-a"}))
            snip = (item.find("a", class_="result__snippet")
                    or item.find("span", class_="result__snippet"))
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if href.startswith("//"):
                href = "https:" + href
            snippet = snip.get_text(strip=True)[:200] if snip else ""
            if title and title not in seen and href.startswith("http"):
                seen.add(title)
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                    "source": _extract_domain(href),
                    "engine": "DuckDuckGo",
                })
            if len(results) >= max_results:
                break
    except Exception:
        # Fallback API
        try:
            r2 = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
                timeout=8,
                headers={"User-Agent": "FinShield-OSINT/2.0"},
            )
            data = r2.json()
            if data.get("AbstractText"):
                results.append({
                    "title": data["AbstractText"][:150],
                    "url": data.get("AbstractURL", ""),
                    "snippet": "",
                    "source": data.get("AbstractSource", "DuckDuckGo"),
                    "engine": "DuckDuckGo",
                })
            for item in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(item, dict) and item.get("Text"):
                    results.append({
                        "title": item["Text"][:150],
                        "url": item.get("FirstURL", ""),
                        "snippet": "",
                        "source": "DuckDuckGo",
                        "engine": "DuckDuckGo",
                    })
        except Exception:
            pass
    return results[:max_results]


# ── Bing Search ───────────────────────────────────────────────────────────────
def _search_bing(query: str, max_results: int = 6) -> list[dict]:
    """Bing HTML search — bon complément pour les résultats FR/EN."""
    results = []
    try:
        from bs4 import BeautifulSoup
        q = quote_plus(query)
        r = requests.get(
            f"https://www.bing.com/search?q={q}&count={max_results + 3}&mkt=fr-FR",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            },
            timeout=12,
        )
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        seen = set()
        for li in soup.select("li.b_algo, .b_algo"):
            h2 = li.find("h2") or li.find("h3")
            a = h2.find("a") if h2 else li.find("a")
            p = li.find("p") or li.find("div", class_="b_caption")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            snippet = p.get_text(strip=True)[:200] if p else ""
            if title and title not in seen and href.startswith("http"):
                seen.add(title)
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet,
                    "source": _extract_domain(href),
                    "engine": "Bing",
                })
            if len(results) >= max_results:
                break
    except Exception:
        pass
    return results[:max_results]


# ── OpenSanctions API ─────────────────────────────────────────────────────────
def _search_opensanctions(entity_name: str) -> list[dict]:
    """Interroge l'API OpenSanctions (matching + search)."""
    hits = []

    # Méthode 1 : match API (personnes)
    try:
        r = requests.post(
            "https://api.opensanctions.org/match/default",
            json={"queries": {"q1": {"schema": "Person", "properties": {"name": [entity_name]}}}},
            timeout=10,
        )
        if r.status_code == 200:
            for _, res in r.json().get("responses", {}).items():
                for match in res.get("results", []):
                    if match.get("score", 0) > 0.4:
                        props = match.get("properties", {})
                        hits.append({
                            "name": props.get("name", [entity_name])[0],
                            "score": round(match["score"], 2),
                            "datasets": match.get("datasets", []),
                            "countries": props.get("country", []),
                            "source_url": f"https://www.opensanctions.org/entities/{match.get('id', '')}",
                            "source": "OpenSanctions",
                        })
    except Exception:
        pass

    # Méthode 2 : search API (entreprises + personnes)
    if not hits:
        try:
            r2 = requests.get(
                f"https://api.opensanctions.org/search/default?q={quote_plus(entity_name)}&limit=5",
                timeout=8,
            )
            if r2.status_code == 200:
                data = r2.json()
                for item in data.get("results", []):
                    hits.append({
                        "name": item.get("caption", entity_name),
                        "score": round(item.get("score", 0.5), 2),
                        "datasets": item.get("datasets", []),
                        "countries": item.get("properties", {}).get("country", []),
                        "source_url": f"https://www.opensanctions.org/entities/{item.get('id', '')}",
                        "source": "OpenSanctions",
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
    negative_count: int = 0
    total_results: int = 0

    @property
    def risk_badge(self) -> str:
        return {
            "low": "🟢 Faible",
            "medium": "🟡 Modéré",
            "high": "🔴 Élevé",
            "critical": "🟣 Critique"
        }.get(self.risk_level, "⚪")


# ── Moteur principal ──────────────────────────────────────────────────────────
def analyze_entity(
    entity_name: str,
    entity_type: str = "person",
    country: str = "",
    birth_date: str = "",
    api_key: str = "",
    additional_context: str = "",
    nb_results_per_query: int = 5,
) -> OSINTResult:

    result = OSINTResult(entity=entity_name, entity_type=entity_type)
    all_media: list[dict] = []
    sources = []

    # ── 1. OpenSanctions ─────────────────────────────────────────
    result.sanctions_hits = _search_opensanctions(entity_name)
    sources.append("OpenSanctions (ONU, UE, OFAC, SECO, UK HMT, 100+ listes)")

    # ── 2. Requêtes multi-moteurs ────────────────────────────────
    queries = _build_queries(entity_name, entity_type, country)

    for i, q in enumerate(queries):
        q_str = q["q"]
        q_label = q["label"]
        q_cat = q.get("category", "reputation")
        q_grav = q.get("gravity", "moyen")

        # Google (priorité 1)
        g_hits = _search_google(q_str, max_results=nb_results_per_query)
        for h in g_hits:
            h.update({
                "query_label": q_label,
                "query_cat": q_cat,
                "query_gravity": q_grav,
                "is_negative": _is_negative(h.get("title", "") + " " + h.get("snippet", "")),
                "credibility": _get_credibility(h.get("url", "")),
            })
        all_media.extend(g_hits)

        # DuckDuckGo (pair) ou Bing (impair)
        if i % 2 == 0:
            d_hits = _search_duckduckgo(q_str, max_results=4)
        else:
            d_hits = _search_bing(q_str, max_results=4)

        for h in d_hits:
            h.update({
                "query_label": q_label,
                "query_cat": q_cat,
                "query_gravity": q_grav,
                "is_negative": _is_negative(h.get("title", "") + " " + h.get("snippet", "")),
                "credibility": _get_credibility(h.get("url", "")),
            })
        all_media.extend(d_hits)

        time.sleep(0.8)  # politesse entre requêtes

    sources.append("Google Search (titres — requêtes négatives croisées)")
    sources.append("DuckDuckGo HTML + Bing Search (complément)")

    # ── 3. Déduplication & tri ───────────────────────────────────
    seen, unique = set(), []
    for item in all_media:
        key = item.get("url", "") or item.get("title", "")[:60].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)

    # Tri : négatifs d'abord, puis par crédibilité de la source
    unique.sort(key=lambda x: (
        not x.get("is_negative", False),
        -x.get("credibility", 1.0)
    ))

    result.adverse_media = unique[:40]
    result.sources_checked = sources
    result.total_results = len(unique)
    result.negative_count = sum(1 for m in unique if m.get("is_negative"))

    # ── 4. Scoring préliminaire ─────────────────────────────────
    base_score = 0.0

    # Sanctions : poids maximum
    if result.sanctions_hits:
        best_os = max(h.get("score", 0) for h in result.sanctions_hits)
        base_score = max(base_score, best_os * 0.9)

    # Résultats négatifs
    neg_count = result.negative_count
    if neg_count >= 10:   base_score = max(base_score, 0.85)
    elif neg_count >= 6:  base_score = max(base_score, 0.70)
    elif neg_count >= 3:  base_score = max(base_score, 0.50)
    elif neg_count >= 1:  base_score = max(base_score, 0.25)

    # Boost si sources officielles ou presse crédible
    high_cred_neg = sum(
        1 for m in unique
        if m.get("is_negative") and m.get("credibility", 1.0) >= 1.5
    )
    if high_cred_neg >= 3:  base_score = min(1.0, base_score + 0.15)
    elif high_cred_neg >= 1: base_score = min(1.0, base_score + 0.08)

    # ── 5. Analyse IA (si clé fournie) ──────────────────────────
    if api_key:
        analysis = _claude_analyze(
            entity_name, entity_type, country, birth_date,
            result.sanctions_hits, result.adverse_media,
            result.negative_count, api_key, additional_context,
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
            f"Analyse OSINT de '{entity_name}' : {result.total_results} résultats collectés "
            f"(Google + DuckDuckGo/Bing), dont {result.negative_count} signal(aux) négatif(s). "
            f"{len(result.sanctions_hits)} correspondance(s) OpenSanctions. "
            f"Score estimé : {round(result.risk_score * 100)}/100 ({result.risk_level.upper()}). "
            "Ajoutez une clé Groq/Anthropic pour la synthèse IA complète."
        )

    return result


def _score_to_level(s: float) -> str:
    if s < 0.25: return "low"
    if s < 0.50: return "medium"
    if s < 0.75: return "high"
    return "critical"


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def _claude_analyze(
    entity_name, entity_type, country, birth_date,
    sanctions_hits, media_hits, negative_count, api_key, additional_context=""
) -> dict:
    """Analyse IA via Claude Sonnet — synthèse et scoring final."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    neg_hits   = [m for m in media_hits if m.get("is_negative")]
    other_hits = [m for m in media_hits if not m.get("is_negative")]

    neg_txt = "\n".join(
        f"- [{m.get('engine','?')}|{m.get('query_label','')}] {m.get('title','')} "
        f"| {m.get('source','')} | {m.get('url','')}"
        for m in neg_hits[:20]
    ) or "Aucun résultat négatif détecté"

    other_txt = "\n".join(
        f"- [{m.get('engine','?')}] {m.get('title','')} | {m.get('source','')}"
        for m in other_hits[:5]
    ) or "Aucun"

    prompt = f"""Tu es un analyste senior AML/KYC et due diligence réglementaire.

ENTITÉ : {entity_name}
Type : {entity_type} | Pays : {country or 'N/A'} | DDN : {birth_date or 'N/A'}
{f"Contexte additionnel : {additional_context}" if additional_context else ""}

=== OpenSanctions ({len(sanctions_hits)} hit(s)) ===
{json.dumps(sanctions_hits[:5], ensure_ascii=False) if sanctions_hits else "Aucune correspondance"}

=== Résultats NÉGATIFS ({negative_count} hits sur Google/DuckDuckGo/Bing) ===
{neg_txt}

=== Autres résultats (contexte neutre) ===
{other_txt}

INSTRUCTIONS STRICTES :
1. Les titres proviennent de recherches ciblées sur des termes négatifs — c'est déjà un signal.
2. Évalue la pertinence de chaque titre pour cette entité spécifique (risque d'homonyme ?).
3. Si plusieurs titres convergent sur un même thème (fraude, sanctions, etc.) = signal fort.
4. Identifie : sanctions, PEP, fraude, corruption, condamnations, blanchiment, terrorisme.
5. NE PAS inventer — base-toi UNIQUEMENT sur les données fournies.
6. Sois conservateur sur les homonymes : mentionne le risque mais ne surpondère pas.
7. Réponds UNIQUEMENT en JSON valide, sans texte avant ou après.

{{
  "summary": "Résumé exécutif clair en 2-3 phrases",
  "risk_level": "low|medium|high|critical",
  "risk_score": 0.0,
  "analysis": "Analyse détaillée structurée (500 mots max)",
  "pep_hits": [{{"name": "...", "position": "...", "country": "...", "source": "..."}}],
  "legal_hits": [{{"description": "...", "type": "fraude|sanction|judiciaire|corruption", "source": "..."}}],
  "red_flags": ["flag 1", "flag 2"],
  "attenuants": ["facteur atténuant 1"],
  "recommendation": "Accepter / Surveiller / Refuser avec justification concise"
}}"""

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "summary": f"Erreur analyse IA : {e}",
            "risk_level": "low",
            "risk_score": 0.0,
            "analysis": "",
            "pep_hits": [],
            "legal_hits": [],
            "red_flags": [],
            "attenuants": [],
            "recommendation": "Erreur — relancez l'analyse.",
        }
