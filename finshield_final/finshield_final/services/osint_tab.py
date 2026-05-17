"""
FinShield — Onglet Analyse OSINT
Moteur v4 — 28 requêtes thématiques · Google + DuckDuckGo + Bing + Brave
"""

import streamlit as st
import time
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# § 4  OSINT ENGINE
# ─────────────────────────────────────────────────────────────────

# ── Mots-clés négatifs ─────────────────────────────────────────────────────
NEGATIVE_KEYWORDS = [
    # FR — corruption & fraude
    "corruption","corrompu","fraudeur","condamné","condamnation",
    "fraude","escroquerie","blanchiment","détournement","malversation",
    "sanction","sanctionné","mis en examen","inculpé","inculpation",
    "garde à vue","perquisition","jugement","tribunal","prison",
    "emprisonné","amende","pénalité","trafic","terrorisme",
    "faillite","liquidation","redressement judiciaire","pot-de-vin",
    "pots-de-vin","renvoi en jugement","abus de biens sociaux",
    "recel","extorsion","escroq","liste noire","blacklist",
    "gel des avoirs","interdiction","poursuite","mise en cause",
    "accusé","fraude fiscale","évasion fiscale","blanchiment d'argent",
    "financement du terrorisme","trafic d'influence","abus de pouvoir",
    "favoritisme","collusion","entente illicite","arnaque",
    # EN — corruption & fraud
    "corruption","convicted","conviction","fraud","scam",
    "money laundering","embezzlement","sanction","sanctioned",
    "indicted","indictment","arrested","charged","trial","court",
    "prison","jail","fine","penalty","trafficking","terrorism",
    "bribery","kickback","bankruptcy","liquidation","watchlist",
    "sentenced","investigation","probe","misconduct","allegation",
    "accused","implicated","wrongdoing","unethical","tax evasion",
    "asset freeze","travel ban","ofac","embargo","conflict of interest",
    "regulatory breach","non-compliance","human rights abuse","corrupt",
    "under investigation","red flag","compliance risk","scandal",
    "enforcement","penalty","settlement","lawsuit","class action",
]

# ── Source credibility ─────────────────────────────────────────────────────
SOURCE_CREDIBILITY = {
    "opensanctions.org":2.0,"ofac.treas.gov":2.0,"amf-france.org":2.0,
    "acpr.banque-france.fr":2.0,"legifrance.gouv.fr":2.0,"justice.fr":2.0,
    "bodacc.fr":1.8,"interpol.int":2.0,"europol.europa.eu":2.0,
    "tracfin.gouv.fr":2.0,"courdecassation.fr":1.9,"sec.gov":2.0,
    "pacer.gov":1.8,"companieshouse.gov.uk":1.7,"opencorporates.com":1.5,
    "pappers.fr":1.6,"societe.com":1.4,"infogreffe.fr":1.8,
    "lemonde.fr":1.5,"lefigaro.fr":1.5,"liberation.fr":1.3,
    "bfmtv.com":1.3,"franceinfo.fr":1.4,"latribune.fr":1.4,
    "lesechos.fr":1.5,"capital.fr":1.3,"leparisien.fr":1.3,
    "reuters.com":1.6,"bloomberg.com":1.6,"ft.com":1.6,
    "theguardian.com":1.5,"nytimes.com":1.5,"bbc.com":1.4,
    "trustpilot.com":1.2,"signal-arnaques.com":1.5,
    "cybermalveillance.gouv.fr":1.8,"twitter.com":0.9,
    "linkedin.com":1.0,"reddit.com":0.9,
}

RISK_THRESHOLDS = {"CRITIQUE":70,"ELEVE":40,"MODERE":10,"FAIBLE":0}
GRAVITY_WEIGHTS = {"eleve":5.0,"moyen":3.0,"faible":1.0}
SCORE_WEIGHTS   = {"sanctions":3.0,"fraud":2.5,"judicial":2.0,"reputation":1.5,"pep":1.0}


# ── Catalogue de requêtes (28 requêtes négatives croisées) ─────────────────
def build_query_catalogue(entity: str) -> list:
    """
    Génère 28 requêtes thématiques négatives croisées pour l'entité.
    Format : (query_string, category, gravity, label)
    """
    q = f'"{entity}"'
    return [
        # ── Corruption / Fraude FR ─────────────────────────────────────────
        (f'{q} corruption OR fraude OR condamné OR "mis en examen" OR inculpé',
         "fraud","eleve","Corruption / Fraude FR"),
        (f'{q} blanchiment OR "financement terrorisme" OR "abus de biens sociaux" OR détournement',
         "fraud","eleve","Criminalité financière FR"),
        (f'{q} escroquerie OR extorsion OR recel OR malversation OR "pot-de-vin"',
         "fraud","eleve","Infractions pénales FR"),
        (f'{q} "fraude fiscale" OR "évasion fiscale" OR favoritisme OR collusion',
         "fraud","eleve","Fraude fiscale FR"),
        # ── Procédures judiciaires FR ──────────────────────────────────────
        (f'{q} tribunal OR jugement OR condamnation OR "garde à vue" OR perquisition',
         "judicial","eleve","Procédures judiciaires FR"),
        (f'{q} prison OR emprisonné OR amende OR pénalité OR poursuite OR arrêté',
         "judicial","eleve","Sanctions pénales FR"),
        (f'{q} "mise en examen" OR inculpation OR "renvoi en jugement" OR "renvoi correctionnel"',
         "judicial","eleve","Inculpation FR"),
        # ── Sanctions & Listes internationales ────────────────────────────
        (f'{q} sanction OR sanctionné OR "liste noire" OR blacklist OR "gel des avoirs"',
         "sanctions","eleve","Sanctions / Listes FR"),
        (f'{q} OFAC OR embargo OR "UN sanctions" OR "EU sanctions" OR "UK sanctions"',
         "sanctions","eleve","Listes internationales"),
        (f'{q} watchlist OR "asset freeze" OR "travel ban" OR "SDN list" OR interpol',
         "sanctions","eleve","Restrictions internationales"),
        # ── Corruption / Fraud EN ──────────────────────────────────────────
        (f'{q} corruption OR fraud OR convicted OR bribery OR indicted',
         "fraud","eleve","Corruption / Fraud EN"),
        (f'{q} "money laundering" OR terrorism OR trafficking OR embezzlement OR kickback',
         "fraud","eleve","Financial crime EN"),
        (f'{q} arrested OR sentenced OR prison OR jail OR "criminal charges" OR "criminal conviction"',
         "judicial","eleve","Legal proceedings EN"),
        (f'{q} misconduct OR wrongdoing OR "regulatory breach" OR "non-compliance" OR "enforcement action"',
         "reputation","moyen","Misconduct EN"),
        (f'{q} scandal OR allegation OR accused OR implicated OR "under investigation"',
         "reputation","moyen","Allegations EN"),
        (f'{q} "tax evasion" OR "insider trading" OR "conflict of interest" OR settlement OR lawsuit',
         "fraud","eleve","Financial misconduct EN"),
        # ── Adverse media / presse négative ───────────────────────────────
        (f'{q} "adverse media" OR "negative news" OR "bad press" OR "red flag" OR probe',
         "reputation","moyen","Adverse media"),
        (f'{q} enquête OR investigation OR suspect OR soupçon OR signalement',
         "judicial","moyen","Enquêtes FR"),
        # ── PEP ───────────────────────────────────────────────────────────
        (f'{q} PEP OR "politically exposed" OR ministre OR député OR sénateur OR oligarque',
         "pep","moyen","PEP / Politique"),
        # ── Sources officielles ciblées ────────────────────────────────────
        (f'site:opensanctions.org {q}',          "sanctions","eleve","OpenSanctions"),
        (f'site:ofac.treas.gov {q}',             "sanctions","eleve","OFAC USA"),
        (f'site:amf-france.org {q}',             "sanctions","eleve","AMF France"),
        (f'site:sec.gov {q}',                    "sanctions","eleve","SEC USA"),
        (f'site:signal-arnaques.com {q}',        "reputation","eleve","Signal Arnaques"),
        (f'site:legifrance.gouv.fr {q}',         "judicial","eleve","Legifrance"),
        # ── Entreprises ────────────────────────────────────────────────────
        (f'{q} faillite OR liquidation OR "redressement judiciaire" OR perquisition',
         "judicial","moyen","Défaillance entreprise"),
        (f'{q} "class action" OR "regulatory fine" OR "enforcement action" OR settlement',
         "judicial","moyen","Litiges entreprise EN"),
        (f'{q} amende OR "contrôle fiscal" OR "autorité de régulation" OR "mise en demeure"',
         "sanctions","eleve","Régulation FR"),
    ]


def _is_negative(text: str) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in NEGATIVE_KEYWORDS)


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


# ── Google Search ──────────────────────────────────────────────────────────
def _search_google(query: str, num: int = 6) -> list:
    import re, random, requests
    results = []
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    ]
    try:
        r = requests.get(
            "https://www.google.com/search",
            params={"q": query, "num": num + 4, "hl": "fr", "gl": "fr"},
            headers={
                "User-Agent": random.choice(ua_list),
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://www.google.com/",
            },
            timeout=12,
        )
        if r.status_code not in (200, 301, 302):
            return []
        html = r.text

        def clean(t):
            t = re.sub(r'<[^>]+>', '', t)
            for esc, rep in [("&amp;","&"),("&quot;",'"'),("&#39;","'"),
                              ("&lt;","<"),("&gt;",">"),("&nbsp;"," ")]:
                t = t.replace(esc, rep)
            return t.strip()

        seen = set()
        block_re = re.compile(r'href="(https?://[^"]+)"[^>]*>.*?<h3[^>]*>(.*?)</h3>', re.DOTALL)
        for url_raw, title_raw in block_re.findall(html):
            title = clean(title_raw)
            url   = url_raw.split("&amp;")[0].split("&")[0]
            if not title or len(title) < 5 or title in seen:
                continue
            if any(x in url for x in ["google.com/search","accounts.google","support.google"]):
                continue
            seen.add(title)
            results.append({"title": title, "url": url, "snippet": "", "engine": "Google"})
            if len(results) >= num:
                break

        if len(results) < 2:
            redirect_urls = re.findall(r'/url\?q=(https?://[^&"]+)', html)
            h3_titles     = re.findall(r'<h3[^>]*>(.*?)</h3>', html)
            for i, raw_title in enumerate(h3_titles[:num+5]):
                title = clean(raw_title)
                if not title or len(title) < 5 or title in seen:
                    continue
                url = redirect_urls[i] if i < len(redirect_urls) else ""
                if any(x in url for x in ["google.com","accounts.google"]):
                    continue
                seen.add(title)
                results.append({"title": title, "url": url, "snippet": "", "engine": "Google"})
                if len(results) >= num:
                    break
    except Exception:
        pass
    return results[:num]


# ── DuckDuckGo HTML ────────────────────────────────────────────────────────
def _search_duckduckgo(query: str, num: int = 5) -> list:
    import random, requests
    results = []
    try:
        from bs4 import BeautifulSoup
        from urllib.parse import quote_plus
        q   = quote_plus(query)
        ua  = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        ])
        r = requests.get(
            f"https://html.duckduckgo.com/html/?q={q}&kl=fr-fr&kp=-1",
            headers={"User-Agent": ua, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"},
            timeout=12,
        )
        if r.status_code != 200 or len(r.text) < 500:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        seen = set()
        for item in soup.select(".result,.web-result"):
            a    = item.find("a", class_="result__a") or item.find("a", attrs={"data-testid":"result-title-a"})
            snip = item.find("a", class_="result__snippet") or item.find("span", class_="result__snippet")
            if not a:
                continue
            title   = a.get_text(strip=True)
            href    = a.get("href", "")
            if href.startswith("//"):
                href = "https:" + href
            snippet = snip.get_text(strip=True)[:200] if snip else ""
            if title and title not in seen and href.startswith("http"):
                seen.add(title)
                results.append({"title": title, "url": href, "snippet": snippet, "engine": "DuckDuckGo"})
            if len(results) >= num:
                break
    except Exception:
        try:
            import requests
            r2 = requests.get("https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
                timeout=8, headers={"User-Agent": "FinShield-OSINT/2.0"})
            data = r2.json()
            if data.get("AbstractText"):
                results.append({"title": data["AbstractText"][:150],
                                 "url": data.get("AbstractURL", ""),
                                 "snippet": "", "engine": "DuckDuckGo"})
            for item in data.get("RelatedTopics", [])[:num]:
                if isinstance(item, dict) and item.get("Text"):
                    results.append({"title": item["Text"][:150],
                                     "url": item.get("FirstURL", ""),
                                     "snippet": "", "engine": "DuckDuckGo"})
        except Exception:
            pass
    return results[:num]


# ── Bing HTML ──────────────────────────────────────────────────────────────
def _search_bing(query: str, num: int = 5) -> list:
    import requests
    results = []
    try:
        from bs4 import BeautifulSoup
        from urllib.parse import quote_plus
        q = quote_plus(query)
        r = requests.get(
            f"https://www.bing.com/search?q={q}&count={num+3}&mkt=fr-FR",
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
        for li in soup.select("li.b_algo,.b_algo"):
            h2 = li.find("h2") or li.find("h3")
            a  = h2.find("a") if h2 else li.find("a")
            p  = li.find("p") or li.find("div", class_="b_caption")
            if not a:
                continue
            title   = a.get_text(strip=True)
            href    = a.get("href", "")
            snippet = p.get_text(strip=True)[:200] if p else ""
            if title and title not in seen and href.startswith("http"):
                seen.add(title)
                results.append({"title": title, "url": href, "snippet": snippet, "engine": "Bing"})
            if len(results) >= num:
                break
    except Exception:
        pass
    return results[:num]


# ── Brave HTML ─────────────────────────────────────────────────────────────
def _search_brave(query: str, num: int = 5) -> list:
    import requests
    results = []
    try:
        from bs4 import BeautifulSoup
        from urllib.parse import quote_plus
        q = quote_plus(query)
        r = requests.get(
            f"https://search.brave.com/search?q={q}&source=web&lang=fr",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "fr-FR,fr;q=0.9",
            },
            timeout=12,
        )
        if r.status_code != 200 or len(r.text) < 500:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        seen = set()
        for item in soup.select(".snippet,.web-result,[data-type='web'],.fdb"):
            a    = item.find("a", class_="heading-serpresult") or item.find("a")
            desc = item.find("p", class_="snippet-description") or item.find("p")
            if not a:
                continue
            href    = a.get("href", "")
            title   = a.get_text(strip=True)
            snippet = desc.get_text(strip=True)[:200] if desc else ""
            if href.startswith("http") and title and title not in seen:
                seen.add(title)
                results.append({"title": title, "url": href, "snippet": snippet, "engine": "Brave"})
            if len(results) >= num:
                break
    except Exception:
        pass
    return results[:num]


# ── OpenSanctions ──────────────────────────────────────────────────────────
def check_opensanctions(name: str) -> dict:
    import requests
    from urllib.parse import quote_plus
    try:
        r = requests.get(
            f"https://api.opensanctions.org/search/default?q={quote_plus(name)}&limit=5",
            timeout=8)
        if r.status_code == 200:
            d = r.json()
            return {"found": d.get("total", 0) > 0, "count": d.get("total", 0),
                    "results": d.get("results", [])[:5]}
    except Exception:
        pass
    try:
        import requests as req
        r2 = req.post(
            "https://api.opensanctions.org/match/default",
            json={"queries": {"q1": {"schema": "Person", "properties": {"name": [name]}}}},
            timeout=8)
        if r2.status_code == 200:
            hits = []
            for _, res in r2.json().get("responses", {}).items():
                for m in res.get("results", []):
                    if m.get("score", 0) > 0.4:
                        hits.append(m)
            return {"found": len(hits) > 0, "count": len(hits), "results": hits}
    except Exception:
        pass
    return {"found": False, "count": 0, "results": [], "error": "Non disponible"}


# ── Analyse et scoring ────────────────────────────────────────────────────
def run_osint_analysis(entity: str, all_results_with_meta: list,
                       scraped_texts: list, os_result: dict) -> dict:
    entity_low    = entity.lower().strip()
    entity_words  = [w for w in entity_low.split() if len(w) >= 3]
    entity_tokens = list(set([entity_low] + entity_words))
    if len(entity_words) >= 2:
        entity_tokens += [entity_words[0], entity_words[-1]]

    def entity_in_text(txt: str) -> bool:
        t = " " + txt.lower() + " "
        return any(tok in t for tok in entity_tokens)

    scores   = {k: 0.0 for k in SCORE_WEIGHTS}
    negative_news, all_articles = [], []

    for r in all_results_with_meta:
        title   = r.get("title", "")
        url     = r.get("url", "")
        snippet = r.get("snippet", "")
        domain  = _extract_domain(url)
        cred    = SOURCE_CREDIBILITY.get(domain, 1.0)
        q_cat   = r.get("query_cat", "reputation")
        q_grav  = r.get("query_gravity", "faible")
        q_label = r.get("query_label", "Recherche web")

        combined    = f"{title} {snippet}"
        entity_hit  = entity_in_text(combined) or entity_in_text(url)
        combined_lo = combined.lower()
        triggered   = [w for w in NEGATIVE_KEYWORDS if w.lower() in combined_lo]

        all_articles.append({
            "title": title, "url": url, "snippet": snippet,
            "domain": domain, "entity_mentioned": entity_hit,
            "query_label": q_label, "triggered_keywords": triggered,
        })

        weight = GRAVITY_WEIGHTS.get(q_grav, 1.0) * cred
        scores[q_cat] = scores.get(q_cat, 0.0) + weight

        if triggered:
            bonus = min(len(triggered), 5) * 0.5 * cred
            scores[q_cat] += bonus

        nature_map = {
            "sanctions": "Sanction / Liste internationale",
            "fraud":     "Fraude / Crime financier",
            "judicial":  "Procédure judiciaire",
            "reputation":"Signal réputationnel",
            "pep":       "Exposition PEP",
        }
        negative_news.append({
            "titre":       title[:120] or url[:80],
            "source":      domain,
            "url":         url,
            "snippet":     snippet[:200],
            "nature":      nature_map.get(q_cat, q_label),
            "gravite":     q_grav,
            "mots_cles":   triggered[:6] if triggered else [f"[requête: {q_label}]"],
            "query_label": q_label,
            "score_brut":  round(weight, 1),
            "category":    q_cat,
            "entity_found":entity_hit,
            "is_negative": _is_negative(combined),
        })

    # OpenSanctions : poids maximal
    if os_result.get("found"):
        scores["sanctions"] += os_result["count"] * 15
        for r in os_result.get("results", []):
            negative_news.insert(0, {
                "titre":       f"OpenSanctions : {r.get('caption', r.get('name', ''))}",
                "source":      "opensanctions.org",
                "url":         f"https://www.opensanctions.org/entities/{r.get('id', '')}",
                "snippet":     f"Datasets : {', '.join(r.get('datasets', []))}",
                "nature":      "Sanction internationale confirmée",
                "gravite":     "eleve",
                "mots_cles":   ["opensanctions"] + r.get("datasets", [])[:3],
                "query_label": "OpenSanctions API",
                "score_brut":  15.0,
                "category":    "sanctions",
                "entity_found":True,
                "is_negative": True,
            })

    negative_news.sort(key=lambda x: (
        not x.get("is_negative", False),
        not x.get("entity_found", False),
        -x.get("score_brut", 0)
    ))

    seen_urls, neg_dedup = {}, []
    for n in negative_news:
        u = n.get("url", "") or n.get("titre", "")[:60]
        if u not in seen_urls:
            seen_urls[u] = True
            neg_dedup.append(n)

    raw   = sum(scores.get(cat, 0) * w for cat, w in SCORE_WEIGHTS.items())
    score = min(100, max(0, int(raw * 1.5)))

    neg_count = sum(1 for n in neg_dedup if n.get("is_negative"))
    if neg_count >= 1 and score < 5:   score = 5
    if neg_count >= 3 and score < 15:  score = 15
    if neg_count >= 8 and score < 30:  score = 30
    if os_result.get("found") and score < 50: score = 50

    niveau = "FAIBLE"
    for lvl, threshold in [("CRITIQUE", 70), ("ELEVE", 40), ("MODERE", 10)]:
        if score >= threshold:
            niveau = lvl
            break

    reco = ("REFUSER"             if score >= 20 or os_result.get("found") else
            "VIGILANCE_RENFORCEE" if score >= 5  or len(neg_dedup) >= 1   else
            "ACCEPTER")

    nb_entity = sum(1 for n in neg_dedup if n.get("entity_found"))

    aggravants, attenuants = [], []
    if os_result.get("found"):
        aggravants.append(f"{os_result['count']} entrée(s) OpenSanctions confirmée(s)")
    if scores.get("fraud", 0) > 3:
        aggravants.append(f"Signaux fraude/corruption (score:{round(scores['fraud'],1)})")
    if scores.get("judicial", 0) > 2:
        aggravants.append(f"Signaux procédures judiciaires (score:{round(scores['judicial'],1)})")
    if scores.get("sanctions", 0) > 3:
        aggravants.append(f"Signaux sanctions/listes (score:{round(scores['sanctions'],1)})")
    if neg_count > 0:
        aggravants.append(f"{neg_count} résultat(s) contenant des mots-clés négatifs")
    if nb_entity == 0 and len(neg_dedup) > 0:
        attenuants.append(f"{len(neg_dedup)} alertes sans mention directe — possibles homonymes")
    if not os_result.get("found"):
        attenuants.append("Absent des listes OpenSanctions consultées")

    resume = (
        f"Analyse OSINT de '{entity}' : {len(all_articles)} résultats collectés, "
        f"{len(neg_dedup)} signal(aux) remontés dont {nb_entity} mentionnant "
        f"directement l'entité ({neg_count} contenant des mots-clés négatifs). "
        f"Score de risque : {score}/100 ({niveau}). "
        f"Recommandation : {reco}. Revue humaine obligatoire avant toute décision."
    )

    return {
        "score_risque":        score,
        "niveau_risque":       niveau,
        "resume_executif":     resume,
        "recommandation":      reco,
        "negative_news":       neg_dedup,
        "all_articles":        all_articles,
        "sanctions":           {"trouve": os_result.get("found", False) or scores.get("sanctions", 0) > 3,
                                "details": f"{os_result['count']} OpenSanctions" if os_result.get("found") else ""},
        "litiges_judiciaires": {"trouve": scores.get("judicial", 0) > 2,
                                "details": f"Score judiciaire : {round(scores.get('judicial',0),1)}"},
        "pep_exposure":        {"trouve": scores.get("pep", 0) > 2, "details": ""},
        "facteurs_aggravants": aggravants,
        "facteurs_attenuants": attenuants,
        "sources_consultees":  list({n["source"] for n in neg_dedup if n.get("source")})[:30],
        "scores_categories":   {k: round(v, 1) for k, v in scores.items()},
        "nb_sources_total":    len(all_articles),
        "nb_sources_filtrees": nb_entity,
        "os_result":           os_result,
        "negative_count":      neg_count,
    }


# ─────────────────────────────────────────────────────────────────
# § 9  TAB 2 — OSINT ANALYSIS
# ─────────────────────────────────────────────────────────────────

def render_osint_tab():
    """Point d'entrée appelé depuis app.py — with tab2: render_osint_tab()"""

    st.markdown("## Screening OSINT & Due Diligence")
    nb_queries = len(build_query_catalogue("X"))
    st.markdown(f"""<div class='info-box'>
    <b>Moteur v4 — {nb_queries} requêtes thématiques · Google + DuckDuckGo + Bing + Brave</b><br>
    Fraude, blanchiment, sanctions, PEP, litiges, presse mondiale.
    Chaque résultat issu d'une requête négative est automatiquement qualifié comme signal.
    <b>Revue humaine obligatoire</b> avant toute décision.
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        entity_input = st.text_input(
            "Entité à analyser",
            placeholder="Ex: Jean Dupont  ou  Binance  ou  Société XYZ SAS",
            key="entity_osint",
        )
    with c2:
        entity_type = st.selectbox("Type", ["Entreprise", "Personne physique", "Groupe bancaire", "Autre"])
    with c3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        launch_btn = st.button("▶ LANCER LE SCREENING", key="btn_osint")

    with st.expander("⚙️ Options avancées"):
        oa, ob = st.columns(2)
        with oa:
            linked_iban  = st.text_input("IBAN lié (optionnel)", key="linked_iban")
            add_to_watch = st.checkbox("Ajouter à la surveillance après analyse")
        with ob:
            nb_results_per_query = st.slider(
                "Résultats par requête", 3, 10, 5,
                help="Plus = plus exhaustif mais plus lent",
            )

    # ── Session state ──────────────────────────────────────────────────────
    for k, v in [("osint_analysis", None), ("osint_entity", ""), ("osint_iban_data", {}),
                  ("osint_bank_data", {}), ("osint_os_result", {}), ("osint_has_risk", False),
                  ("osint_all_results", [])]:
        if k not in st.session_state:
            st.session_state[k] = v

    if launch_btn and entity_input.strip():
        entity    = entity_input.strip()
        catalogue = build_query_catalogue(entity)

        prog = st.progress(0)
        stat = st.empty()

        # ── STEP 1 : OpenSanctions ─────────────────────────────────────────
        stat.markdown("🔎 **[1/4]** Vérification OpenSanctions…")
        os_result = check_opensanctions(entity)
        prog.progress(5)
        if os_result.get("found"):
            st.markdown(
                f"<div class='danger-box'>🚨 <b>{os_result['count']}</b> "
                f"correspondance(s) OpenSanctions trouvée(s) !</div>",
                unsafe_allow_html=True,
            )

        # ── STEP 2 : Recherches multi-moteurs ─────────────────────────────
        total_q = len(catalogue)
        stat.markdown(f"🌐 **[2/4]** {total_q} requêtes · Google · DuckDuckGo · Bing · Brave…")

        all_results_with_meta = []
        engines_used = []
        sites_visited  = 0
        neg_found      = 0
        feed_placeholder    = st.empty()
        counter_placeholder = st.empty()
        live_feed = []

        eng_icons = {"Google": "🔍", "DuckDuckGo": "🦆", "Bing": "🔷", "Brave": "🦁"}

        for i, (q_str_tpl, q_cat, q_grav, q_label) in enumerate(catalogue):

            # Google
            g_hits = _search_google(q_str_tpl, nb_results_per_query)
            if g_hits and "Google" not in engines_used:
                engines_used.append("Google")

            # DDG ou Bing en alternance
            if i % 2 == 0:
                d_hits = _search_duckduckgo(q_str_tpl, nb_results_per_query)
                if d_hits and "DuckDuckGo" not in engines_used:
                    engines_used.append("DuckDuckGo")
            else:
                d_hits = _search_bing(q_str_tpl, nb_results_per_query)
                if d_hits and "Bing" not in engines_used:
                    engines_used.append("Bing")

            # Brave (toutes les 3 requêtes)
            if i % 3 == 0:
                bv_hits = _search_brave(q_str_tpl, nb_results_per_query)
                if bv_hits and "Brave" not in engines_used:
                    engines_used.append("Brave")
            else:
                bv_hits = []

            hits_this_query = g_hits + d_hits + bv_hits

            for h in hits_this_query:
                h["query_cat"]     = q_cat
                h["query_gravity"] = q_grav
                h["query_label"]   = q_label

            all_results_with_meta.extend(hits_this_query)
            sites_visited += len(hits_this_query)

            for h in hits_this_query:
                txt = h.get("title", "") + " " + h.get("snippet", "")
                if _is_negative(txt):
                    neg_found += 1

            # ── Compteur live ──────────────────────────────────────────────
            eng_str = "  ".join(f"{eng_icons.get(e,'🔘')} {e}" for e in engines_used)
            counter_placeholder.markdown(
                f"""<div style='background:#111520;border:1px solid #1e2535;border-radius:6px;
                padding:12px 20px;margin:8px 0;font-family:IBM Plex Mono,monospace;'>
                <span style='color:#5a6a7a;font-size:0.75rem;'>PROGRESSION</span><br>
                <span style='color:#00d4ff;font-size:1.1rem;font-weight:bold;'>{i+1}</span>
                <span style='color:#5a6a7a;'> / {total_q} requêtes</span>
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span style='color:#00d4ff;font-size:1.1rem;font-weight:bold;'>{sites_visited}</span>
                <span style='color:#5a6a7a;'> pages parcourues</span>
                &nbsp;&nbsp;·&nbsp;&nbsp;
                <span style='color:#ff3366;font-size:1.1rem;font-weight:bold;'>{neg_found}</span>
                <span style='color:#5a6a7a;'> signaux négatifs</span>
                <br><span style='color:#5a6a7a;font-size:0.72rem;'>Moteurs : {eng_str}</span>
                </div>""",
                unsafe_allow_html=True,
            )

            # ── Feed défilant ──────────────────────────────────────────────
            grav_icon = {"eleve": "🔴", "moyen": "🟡", "faible": "🟢"}.get(q_grav, "⚪")
            for h in hits_this_query[-3:]:
                eng   = h.get("engine", "?")
                icon  = eng_icons.get(eng, "🔘")
                title = h.get("title", "")[:70]
                url   = h.get("url", "#")
                is_neg = _is_negative(h.get("title", "") + " " + h.get("snippet", ""))
                neg_marker = " 🚨" if is_neg else ""
                link_html = (
                    f'<a href="{url}" target="_blank" style="color:#00d4ff;">{title}</a>'
                    if url and url != "#" else title
                )
                live_feed.append(
                    f"{icon} `{eng}` &nbsp;·&nbsp; {grav_icon} **{q_label}**"
                    f"&nbsp;·&nbsp; {link_html}{neg_marker}"
                )
            live_feed = live_feed[-10:]

            feed_placeholder.markdown("\n\n".join(live_feed), unsafe_allow_html=True)
            prog.progress(5 + int((i + 1) / total_q * 60))
            time.sleep(0.3)

        counter_placeholder.empty()
        feed_placeholder.empty()

        # ── STEP 3 : Déduplication ─────────────────────────────────────────
        stat.markdown("🔗 **[3/4]** Déduplication et analyse…")
        seen, unique = set(), []
        for r in all_results_with_meta:
            u = r.get("url", "") or r.get("title", "")[:60]
            if u and u not in seen:
                seen.add(u)
                unique.append(r)
        all_results_with_meta = unique
        prog.progress(70)

        # ── STEP 4 : IBAN + Scoring ────────────────────────────────────────
        stat.markdown("🏦 **[4/4]** IBAN + Scoring final…")
        iban_data, bank_data = {}, {}

        # Validation IBAN optionnelle (si la fonction est disponible)
        if linked_iban.strip():
            try:
                from iban_service import validate_iban
                iban_data = validate_iban(linked_iban.strip())
            except ImportError:
                iban_data = {"raw": linked_iban.strip(), "valid": False,
                             "error": "iban_service non disponible"}

        analysis = run_osint_analysis(entity, all_results_with_meta, [], os_result)
        prog.progress(90)

        # ── Résumé final ───────────────────────────────────────────────────
        st.markdown(
            f"""<div style='background:#111520;border:1px solid #1e2535;border-radius:6px;
            padding:14px 20px;margin:12px 0;font-family:IBM Plex Mono,monospace;'>
            <span style='color:#00ff88;font-size:0.8rem;letter-spacing:2px;'>✅ SCREENING TERMINÉ</span><br>
            <span style='color:#00d4ff;font-size:1.2rem;font-weight:bold;'>{total_q}</span>
            <span style='color:#5a6a7a;'> requêtes effectuées</span>
            &nbsp;&nbsp;·&nbsp;&nbsp;
            <span style='color:#00d4ff;font-size:1.2rem;font-weight:bold;'>{sites_visited}</span>
            <span style='color:#5a6a7a;'> pages analysées</span>
            &nbsp;&nbsp;·&nbsp;&nbsp;
            <span style='color:#ff3366;font-size:1.2rem;font-weight:bold;'>{analysis.get("negative_count",0)}</span>
            <span style='color:#5a6a7a;'> signaux négatifs confirmés</span>
            &nbsp;&nbsp;·&nbsp;&nbsp;
            <span style='color:#00d4ff;font-size:1.2rem;font-weight:bold;'>{len(engines_used)}</span>
            <span style='color:#5a6a7a;'> moteurs ({", ".join(engines_used)})</span>
            </div>""",
            unsafe_allow_html=True,
        )

        # ── Sauvegarde DB / Excel (gracieux si non disponible) ─────────────
        try:
            from db_service import db_save_report, db_add_watchlist
            db_save_report(entity, entity_type, linked_iban or "",
                           analysis["score_risque"], analysis["niveau_risque"],
                           analysis["recommandation"], analysis["resume_executif"],
                           json.dumps(analysis, ensure_ascii=False))
            if add_to_watch:
                db_add_watchlist(entity, entity_type, "Screening auto",
                                 analysis["niveau_risque"], "Auto")
        except ImportError:
            pass

        try:
            from excel_service import append_to_excel_history
            append_to_excel_history(entity, entity_type, analysis, os_result,
                                    iban_data if iban_data.get("raw") else None)
        except (ImportError, Exception) as ex:
            if not isinstance(ex, ImportError):
                st.warning(f"Excel history : {ex}")

        score  = analysis["score_risque"]
        niveau = analysis["niveau_risque"]
        reco   = analysis["recommandation"]
        has_risk = (
            score >= 5
            or os_result.get("found")
            or analysis["sanctions"]["trouve"]
            or analysis["litiges_judiciaires"]["trouve"]
            or len(analysis["negative_news"]) >= 1
            or analysis.get("negative_count", 0) >= 1
            or niveau in ("MODERE", "ELEVE", "CRITIQUE")
        )

        st.session_state.update({
            "osint_analysis":    analysis,
            "osint_entity":      entity,
            "osint_iban_data":   iban_data,
            "osint_bank_data":   bank_data,
            "osint_os_result":   os_result,
            "osint_has_risk":    has_risk,
            "osint_all_results": all_results_with_meta,
        })
        prog.progress(100)
        stat.empty()

    # ── AFFICHAGE DES RÉSULTATS ────────────────────────────────────────────
    analysis  = st.session_state["osint_analysis"]
    entity_d  = st.session_state["osint_entity"]
    iban_data = st.session_state["osint_iban_data"]
    bank_data = st.session_state["osint_bank_data"]
    os_result = st.session_state["osint_os_result"]
    has_risk  = st.session_state["osint_has_risk"]

    if not analysis:
        return

    st.markdown("---")
    score  = analysis["score_risque"]
    niveau = analysis["niveau_risque"]
    reco   = analysis["recommandation"]
    neg_n  = analysis["negative_news"]
    nb_tot = analysis["nb_sources_total"]
    nb_ent = analysis["nb_sources_filtrees"]
    neg_ct = analysis.get("negative_count", 0)

    if not has_risk:
        st.markdown(f"""<div style='background:rgba(0,255,136,0.07);border:2px solid #00ff88;
        border-radius:8px;padding:28px;text-align:center;'>
        <div style='font-size:2.5rem;'>✅</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;color:#00ff88;margin:10px 0;'>
        RAS — AUCUN RISQUE DÉTECTÉ</div>
        <div style='color:#c8d6e5;'><b>{entity_d}</b></div>
        <div style='color:#5a6a7a;font-size:0.8rem;margin-top:10px;'>
        Score : {score}/100 · {nb_tot} pages analysées · {nb_ent} mentions directes</div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"<div class='ok-box'>{analysis['resume_executif']}</div>", unsafe_allow_html=True)
    else:
        bmap = {"FAIBLE":"badge-low","MODERE":"badge-medium",
                "ELEVE":"badge-high","CRITIQUE":"badge-high"}.get(niveau, "badge-medium")
        rc_c = {"ACCEPTER":"#00ff88","VIGILANCE_RENFORCEE":"#ffcc00",
                "REFUSER":"#ff3366"}.get(reco, "#5a6a7a")

        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.markdown(f"<div class='metric-card'><div class='label'>Score</div><div class='value'>{score}<span style='font-size:0.8rem;color:#5a6a7a;'>/100</span></div></div>", unsafe_allow_html=True)
        mc2.markdown(f"<div class='metric-card'><div class='label'>Niveau</div><div style='margin-top:12px;'><span class='{bmap}'>{niveau}</span></div></div>", unsafe_allow_html=True)
        mc3.markdown(f"<div class='metric-card'><div class='label'>Signaux négatifs</div><div class='value' style='color:#ff3366;'>{neg_ct}</div></div>", unsafe_allow_html=True)
        sc_t = f"🔴 {os_result.get('count',0)} hit(s)" if os_result.get("found") else "✅ Aucune"
        sc_c = "#ff3366" if os_result.get("found") else "#00ff88"
        mc4.markdown(f"<div class='metric-card'><div class='label'>Sanctions</div><div class='value' style='font-size:0.8rem;color:{sc_c};'>{sc_t}</div></div>", unsafe_allow_html=True)
        mc5.markdown(f"<div class='metric-card'><div class='label'>Recommandation</div><div class='value' style='font-size:0.65rem;color:{rc_c};'>{reco}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='warn-box'><b>⚠ Résumé :</b> {analysis['resume_executif']}</div>", unsafe_allow_html=True)

        dl, dr = st.columns(2)
        with dl:
            st.markdown(f"#### 📰 Signaux détectés ({len(neg_n)})")
            for n in neg_n[:30]:
                g   = n.get("gravite", "").lower()
                cls = {"faible":"info-box","moyen":"warn-box","eleve":"danger-box"}.get(g, "warn-box")
                url = n.get("url", "")
                lnk = (f'<a href="{url}" target="_blank" style="color:#00d4ff;font-size:0.75rem;'
                       f'font-family:IBM Plex Mono,monospace;">↗ Consulter la source</a>'
                       if url and url.startswith("http") else "")
                kws    = ", ".join(n.get("mots_cles", [])[:4])
                direct = (" <span style='color:#00ff88;font-size:0.7rem;'>✓ entité directe</span>"
                          if n.get("entity_found") else
                          " <span style='color:#ffcc00;font-size:0.7rem;'>⚠ vérifier homonyme</span>")
                neg_tag = (" <span style='color:#ff3366;font-size:0.7rem;'>🚨 mots-clés négatifs</span>"
                           if n.get("is_negative") else "")
                st.markdown(f"""<div class='{cls}'>
                <b>{n.get('titre','')[:100]}</b>{direct}{neg_tag}<br>
                <small style='color:#5a6a7a;'>{n.get('source','')} · <b style='color:#c8d6e5;'>{n.get('nature','')}</b> · {n.get('query_label','')}</small><br>
                <small style='color:#ffcc00;'>🔑 {kws}</small>
                {f"<br>{lnk}" if lnk else ""}
                </div>""", unsafe_allow_html=True)

        with dr:
            st.markdown("#### 🚨 Sanctions & PEP")
            if os_result.get("found"):
                st.markdown(f"<div class='danger-box'>🔴 {os_result['count']} entrée(s) OpenSanctions</div>", unsafe_allow_html=True)
                for r in os_result.get("results", [])[:3]:
                    name   = r.get("caption", "") or r.get("name", "")
                    eid    = r.get("id", "")
                    os_url = f"https://www.opensanctions.org/entities/{eid}" if eid else ""
                    os_lnk = (f'<a href="{os_url}" target="_blank" style="color:#00d4ff;font-size:0.75rem;">'
                              f'↗ Voir sur OpenSanctions</a>' if os_url else "")
                    st.markdown(
                        f"<div class='result-row'><b>{name}</b> · "
                        f"{', '.join(r.get('datasets',[]))}<br>{os_lnk}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown("<div class='ok-box'>Absent des listes de sanctions</div>", unsafe_allow_html=True)

            for f in analysis.get("facteurs_aggravants", []):
                st.markdown(f"<div class='danger-box'>🔺 {f}</div>", unsafe_allow_html=True)
            for f in analysis.get("facteurs_attenuants", []):
                st.markdown(f"<div class='ok-box'>🔻 {f}</div>", unsafe_allow_html=True)

    # ── Sources complètes ──────────────────────────────────────────────────
    all_art = analysis.get("all_articles", [])
    with st.expander(f"📋 Toutes les sources collectées ({len(all_art)} pages)"):
        art_neg    = [a for a in all_art if _is_negative(a.get("title","")+" "+a.get("snippet",""))]
        art_direct = [a for a in all_art if a.get("entity_mentioned") and a not in art_neg]
        art_other  = [a for a in all_art if a not in art_neg and a not in art_direct]

        if art_neg:
            st.markdown(f"**🚨 Sources avec mots-clés négatifs ({len(art_neg)})**")
            for a in art_neg:
                url = a.get("url", "")
                lnk = (f'<a href="{url}" target="_blank" style="color:#ff3366;font-size:0.75rem;">↗ lire</a>'
                       if url and url.startswith("http") else "")
                st.markdown(f"""<div class='result-row' style='border-left:3px solid #ff3366;'>
                <b>{a.get('title','')[:100]}</b> {lnk}<br>
                <small style='color:#5a6a7a;'>{a.get('domain','')} · {a.get('query_label','')}</small>
                </div>""", unsafe_allow_html=True)

        if art_direct:
            st.markdown(f"**✓ Mentions directes de '{entity_d}' ({len(art_direct)})**")
            for a in art_direct:
                url = a.get("url", "")
                lnk = (f'<a href="{url}" target="_blank" style="color:#00d4ff;font-size:0.75rem;">↗ lire</a>'
                       if url and url.startswith("http") else "")
                st.markdown(f"""<div class='result-row' style='border-left:3px solid #00d4ff;'>
                <b>{a.get('title','')[:100]}</b> {lnk}<br>
                <small style='color:#5a6a7a;'>{a.get('domain','')} · {a.get('query_label','')}</small>
                </div>""", unsafe_allow_html=True)

        if art_other:
            st.markdown(f"**Autres résultats ({len(art_other)})**")
            for a in art_other[:30]:
                url = a.get("url", "")
                lnk = (f'<a href="{url}" target="_blank" style="color:#5a6a7a;font-size:0.72rem;">↗ lire</a>'
                       if url and url.startswith("http") else "")
                st.markdown(f"""<div class='result-row'>
                <span style='color:#5a6a7a;'>{a.get('title','')[:100]}</span> {lnk}
                </div>""", unsafe_allow_html=True)

    # ── Validation humaine ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-title'>✍️ VALIDATION HUMAINE</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='info-box'>Après examen des articles (liens cliquables ci-dessus), "
        "renseignez votre décision.</div>",
        unsafe_allow_html=True,
    )

    vh1, vh2 = st.columns([1, 2])
    with vh1:
        analyst_name = st.text_input("👤 Nom de l'analyste", placeholder="ex: Marie Dupont", key="analyst_name")
        human_decision_raw = st.radio(
            "Décision après analyse",
            ["En attente", "✅ RAS — Rien à signaler", "⚠️ Informations négatives confirmées"],
            key="human_decision",
        )
    with vh2:
        human_comment = st.text_area(
            "Commentaire", placeholder="ex: RAS — homonyme identifié.", height=110, key="human_comment"
        )

    decision_map = {
        "En attente": None,
        "✅ RAS — Rien à signaler": "RAS",
        "⚠️ Informations négatives confirmées": "RISQUE_CONFIRME",
    }
    h_decision = decision_map.get(human_decision_raw, None)

    pdf_c1, pdf_c2, pdf_c3 = st.columns(3)

    with pdf_c1:
        if st.button("⬇ GÉNÉRER RAPPORT PDF OSINT", key="gen_pdf_main"):
            with st.spinner("Génération du PDF…"):
                try:
                    from pdf_service import generate_osint_pdf
                    pdf_bytes = generate_osint_pdf(
                        entity_d, analysis, os_result,
                        iban_data if iban_data.get("raw") else None,
                        bank_data if bank_data else None,
                        human_decision=h_decision,
                        human_comment=human_comment,
                        analyst_name=analyst_name,
                    )
                    suffix = {"RAS":"RAS","RISQUE_CONFIRME":"RISQUE"}.get(h_decision,"ATTENTE")
                    fname  = (f"FinShield_OSINT_{entity_d.replace(' ','_')}"
                              f"_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
                    st.download_button("📥 Télécharger PDF", data=pdf_bytes,
                                       file_name=fname, mime="application/pdf",
                                       key="dl_pdf_main")
                    st.markdown("<div class='ok-box'>✅ Rapport PDF généré.</div>", unsafe_allow_html=True)
                except Exception as e:
                    import traceback
                    st.error(f"Erreur PDF : {e}")
                    st.code(traceback.format_exc())

    with pdf_c2:
        if st.button("📊 METTRE À JOUR EXCEL", key="update_excel"):
            try:
                from excel_service import append_to_excel_history, EXCEL_HISTORY_PATH
                xl_path = append_to_excel_history(
                    entity_d, entity_type, analysis, os_result,
                    iban_data if iban_data.get("raw") else None,
                    analyst_name=analyst_name,
                    human_decision=h_decision,
                )
                with open(xl_path, "rb") as f:
                    st.download_button(
                        "📥 Télécharger Excel", data=f.read(),
                        file_name="finshield_history.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_excel_main",
                    )
                st.markdown("<div class='ok-box'>✅ Historique Excel mis à jour.</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Erreur Excel : {e}")

    with pdf_c3:
        try:
            from excel_service import EXCEL_HISTORY_PATH
            if os.path.exists(EXCEL_HISTORY_PATH):
                with open(EXCEL_HISTORY_PATH, "rb") as f:
                    st.download_button(
                        "📥 Excel complet", data=f.read(),
                        file_name="finshield_history.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_excel_full",
                    )
        except ImportError:
            pass
