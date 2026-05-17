# 🛡️ FinShield OSINT

**Plateforme de conformité financière & due diligence**

Application Streamlit multi-onglets pour l'analyse OSINT, la vérification d'IBAN et la recherche bancaire.

---

## ✨ Fonctionnalités

| Onglet | Description |
|--------|-------------|
| 🏦 **Vérification IBAN** | Validation MOD97, décomposition BBAN, lookup banque/succursale |
| 🔍 **Analyse OSINT** | Sanctions, adverse media, PEP, litiges + rapport PDF (propulsé par Claude AI) |
| 📋 **Recherche Banque** | Base 200+ banques françaises — par code CIB ou nom |
| ⚙️ **Sources & Config** | Documentation des sources, guide de déploiement |

---

## 🚀 Installation rapide

### Prérequis
- Python 3.11+
- Clé API Anthropic ([console.anthropic.com](https://console.anthropic.com))

### Local

```bash
# 1. Cloner
git clone https://github.com/VOTRE_ORG/finshield-osint.git
cd finshield-osint

# 2. Environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Dépendances
pip install -r requirements.txt

# 4. Clé API
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Éditer secrets.toml → ANTHROPIC_API_KEY = "sk-ant-..."

# 5. Lancer
streamlit run app.py
```

### Streamlit Community Cloud (gratuit)

1. **Fork** ce repo sur GitHub
2. Aller sur [share.streamlit.io](https://share.streamlit.io)
3. **New app** → votre repo → `app.py`
4. **Advanced settings → Secrets** :
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-VOTRE_CLE"
```
5. **Deploy** ✅

### Docker

```bash
docker build -t finshield-osint .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=sk-ant-xxx finshield-osint
```

---

## 📁 Structure du projet

```
finshield-osint/
├── app.py                        # Point d'entrée Streamlit
├── requirements.txt              # Dépendances Python
├── README.md
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example     # Template de configuration
├── tabs/
│   ├── __init__.py
│   ├── iban_tab.py               # Onglet IBAN
│   ├── osint_tab.py              # Onglet OSINT
│   ├── bank_search_tab.py        # Onglet Banques FR
│   └── config_tab.py             # Onglet Config
├── services/
│   ├── __init__.py
│   ├── iban_service.py           # Moteur IBAN (validation + lookup)
│   ├── osint_service.py          # Moteur OSINT (OpenSanctions + Claude)
│   └── pdf_service.py            # Génération PDF (ReportLab)
├── data/
│   ├── __init__.py
│   └── banks_fr.py               # Base 200+ banques françaises (CIB)
└── utils/
    └── __init__.py
```

---

## 🔑 Sources intégrées

| Source | Type | Accès |
|--------|------|-------|
| [OpenSanctions](https://www.opensanctions.org) | Sanctions ONU, UE, OFAC, SECO... | API gratuite |
| DuckDuckGo | Presse & web ouvert | API publique |
| Base CIB Banque de France | Répertoire bancaire FR | Base locale |
| Répertoire BDL (Liban) | Banques libanaises | Base locale |
| Registre IBAN SWIFT | Structure IBAN 80+ pays | Base locale |
| [Anthropic Claude](https://www.anthropic.com) | Synthèse IA | Clé API |

---

## ⚠️ Avertissement légal

- **Usage professionnel uniquement**
- Respectez le RGPD et les législations locales applicables
- Les résultats sont **informatifs** — vérifiez toujours les sources primaires
- Ne stocker que des métadonnées et extraits courts (jamais de contenu intégral protégé)
- Toute décision de conformité doit être validée par un professionnel qualifié

---

## 📜 Licence

MIT — Voir [LICENSE](LICENSE)
