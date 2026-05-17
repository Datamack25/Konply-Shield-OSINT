"""
FinShield — Service OSINT
Analyse due diligence : presse, sanctions, PEP, litiges, réputation
Via Anthropic Claude + recherche web DuckDuckGo
"""

from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from typing import Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# ── Résultat OSINT ─────────────────────────────────────────────────────────────
@dataclass
class OSINTResult:
    entity: str
    entity_type: str = "person"  # person | company
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
        badges = {
            "low":      "🟢 Faible",
            "medium":   "🟡 Modéré",
            "high":     "🔴 Élevé",
            "critical": "🟣 Critique",
        }
        return badges.get(self.risk_level, "⚪ Inconnu")


# ── DuckDuckGo search (no key needed) ─────────────────────────────────────────
def _search_ddg(query: str, max_results: int = 5) -> list[dict]:
    """Recherche DuckDuckGo Instant Answer API (gratuite, sans clé)."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_redirect": 1,
            "no_html": 1,
            "skip_disambig": 1,
        }
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        results = []
        for item in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(item, dict) and item.get("Text"):
                results.append({
                    "title": item.get("Text", "")[:100],
                    "url":   item.get("FirstURL", ""),
                    "source": "DuckDuckGo",
                })
        return results
    except Exception:
        return []


def _search_opensanctions(entity_name: str) -> list[dict]:
    """
    Interroge l'API OpenSanctions (données publiques gratuites).
    https://www.opensanctions.org/api/
    """
    hits = []
    try:
        url = "https://api.opensanctions.org/match/default"
        payload = {
            "queries": {
                "q1": {
                    "schema": "Person",
                    "properties": {"name": [entity_name]},
                }
            }
        }
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for _, result in data.get("responses", {}).items():
                for match in result.get("results", []):
                    score = match.get("score", 0)
                    if score > 0.5:
                        props = match.get("properties", {})
                        hits.append({
                            "name":       props.get("name", [entity_name])[0],
                            "score":      round(score, 2),
                            "datasets":   match.get("datasets", []),
                            "countries":  props.get("country", []),
                            "source_url": f"https://www.opensanctions.org/entities/{match.get('id', '')}",
                            "source":     "OpenSanctions",
                        })
    except Exception:
        pass
    return hits


# ── Moteur OSINT principal ─────────────────────────────────────────────────────

def analyze_entity(
    entity_name: str,
    entity_type: str = "person",
    country: str = "",
    birth_date: str = "",
    api_key: str = "",
    additional_context: str = "",
) -> OSINTResult:
    """
    Analyse OSINT complète d'une entité :
    1. Vérification OpenSanctions
    2. Recherche presse DuckDuckGo
    3. Synthèse et scoring via Claude
    """
    result = OSINTResult(entity=entity_name, entity_type=entity_type)
    sources = []

    # ── Étape 1 : OpenSanctions ──
    sanctions_hits = _search_opensanctions(entity_name)
    result.sanctions_hits = sanctions_hits
    sources.append("OpenSanctions (ONU, UE, OFAC, SECO...)")

    # ── Étape 2 : Presse & web ──
    queries = [
        f'"{entity_name}" sanctions fraud corruption',
        f'"{entity_name}" PEP politiquement exposé',
        f'"{entity_name}" litige tribunal condamné',
        f'"{entity_name}" blanchiment financement terrorisme',
    ]
    media_hits = []
    for q in queries[:2]:  # limiter les appels
        hits = _search_ddg(q, max_results=3)
        media_hits.extend(hits)
        time.sleep(0.3)

    result.adverse_media = media_hits[:8]
    sources.append("DuckDuckGo / Web ouvert")

    result.sources_checked = sources

    # ── Étape 3 : Scoring préliminaire ──
    base_score = 0.0
    if sanctions_hits:
        max_sanction_score = max(h.get("score", 0) for h in sanctions_hits)
        base_score = max(base_score, max_sanction_score * 0.8)
    if len(media_hits) >= 3:
        base_score = max(base_score, 0.35)

    # ── Étape 4 : Synthèse Claude (si API key disponible) ──
    if api_key:
        analysis = _claude_analyze(
            entity_name=entity_name,
            entity_type=entity_type,
            country=country,
            birth_date=birth_date,
            sanctions_hits=sanctions_hits,
            media_hits=media_hits,
            api_key=api_key,
            additional_context=additional_context,
        )
        result.raw_analysis = analysis.get("analysis", "")
        result.summary      = analysis.get("summary", "")
        result.risk_level   = analysis.get("risk_level", "low")
        result.risk_score   = analysis.get("risk_score", base_score)
        result.pep_hits     = analysis.get("pep_hits", [])
        result.legal_hits   = analysis.get("legal_hits", [])
    else:
        # Sans API : scoring heuristique
        result.risk_score = round(min(base_score, 1.0), 2)
        result.risk_level = _score_to_level(result.risk_score)
        result.summary    = (
            f"Analyse préliminaire sans IA : {len(sanctions_hits)} hit(s) sanctions, "
            f"{len(media_hits)} résultat(s) presse. "
            "Ajoutez une clé API Anthropic pour une synthèse complète."
        )

    return result


def _score_to_level(score: float) -> str:
    if score < 0.25:  return "low"
    if score < 0.50:  return "medium"
    if score < 0.75:  return "high"
    return "critical"


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def _claude_analyze(
    entity_name: str,
    entity_type: str,
    country: str,
    birth_date: str,
    sanctions_hits: list[dict],
    media_hits: list[dict],
    api_key: str,
    additional_context: str = "",
) -> dict:
    """
    Appel à Claude (claude-sonnet) pour synthèse OSINT structurée.
    Retourne un dict JSON analysé.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    sanctions_txt = json.dumps(sanctions_hits[:5], ensure_ascii=False, indent=2) if sanctions_hits else "Aucun"
    media_txt = "\n".join(
        f"- {h.get('title', '')} [{h.get('url', '')}]"
        for h in media_hits[:6]
    ) or "Aucun résultat"

    context_block = f"\nContexte supplémentaire fourni : {additional_context}" if additional_context else ""

    prompt = f"""Tu es un analyste senior en conformité AML/KYC et due diligence.

ENTITÉ À ANALYSER :
- Nom : {entity_name}
- Type : {entity_type}
- Pays : {country or 'Non précisé'}
- Date de naissance : {birth_date or 'Non précisée'}
{context_block}

DONNÉES COLLECTÉES :

=== Hits OpenSanctions (ONU, UE, OFAC, SECO, etc.) ===
{sanctions_txt}

=== Résultats presse & web ouvert ===
{media_txt}

INSTRUCTIONS :
1. Analyse toutes les données disponibles.
2. Identifie les risques AML/KYC : sanctions, PEP, adverse media, litiges, criminalité financière.
3. Évalue le niveau de risque global : low / medium / high / critical.
4. Fournis une justification claire et sourcée.
5. Ne pas inventer de données — base-toi uniquement sur ce qui est fourni.
6. Réponds UNIQUEMENT en JSON valide avec ce schéma exact :

{{
  "summary": "Résumé exécutif 2-3 phrases",
  "risk_level": "low|medium|high|critical",
  "risk_score": 0.0,
  "analysis": "Analyse détaillée (500 mots max)",
  "pep_hits": [
    {{"name": "...", "position": "...", "country": "...", "source": "..."}}
  ],
  "legal_hits": [
    {{"description": "...", "type": "...", "source": "..."}}
  ],
  "red_flags": ["..."],
  "recommendation": "Accepter / Surveiller / Refuser — justification courte"
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # Nettoyer les fences markdown si présentes
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "summary": "Analyse disponible en texte brut.",
            "risk_level": "medium",
            "risk_score": 0.5,
            "analysis": raw if "raw" in dir() else "Erreur de parsing.",
            "pep_hits": [],
            "legal_hits": [],
            "red_flags": [],
            "recommendation": "À vérifier manuellement.",
        }
    except Exception as e:
        return {
            "summary": f"Erreur API : {e}",
            "risk_level": "low",
            "risk_score": 0.0,
            "analysis": "",
            "pep_hits": [],
            "legal_hits": [],
            "red_flags": [],
            "recommendation": "Erreur — relancez l'analyse.",
        }
