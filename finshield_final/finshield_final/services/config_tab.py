"""
FinShield — Onglet Sources & Configuration
"""
import streamlit as st


def render_config_tab():
    st.header("⚙️ Sources & Configuration")
    st.caption("Documentation des sources de données, guide de déploiement, configuration")

    tab1, tab2, tab3, tab4 = st.tabs(["📡 Sources intégrées", "🚀 Déploiement", "🔑 Configuration API", "📋 Roadmap"])

    with tab1:
        st.subheader("Sources de données intégrées")
        sources = [
            {
                "name": "OpenSanctions",
                "url": "https://www.opensanctions.org",
                "description": "Listes de sanctions consolidées : ONU, UE, OFAC (USA), SECO (Suisse), UK HMT, Interpol, et 100+ autres",
                "type": "🔴 Sanctions",
                "access": "API gratuite (rate-limited) / données ouvertes",
            },
            {
                "name": "DuckDuckGo Search",
                "url": "https://api.duckduckgo.com",
                "description": "Recherche presse et web ouverts pour adverse media. Aucune clé API requise.",
                "type": "📰 Adverse Media",
                "access": "API publique gratuite",
            },
            {
                "name": "Base CIB Banque de France",
                "url": "https://www.banque-france.fr",
                "description": "Répertoire des codes interbancaires (CIB) — 200+ banques indexées localement.",
                "type": "🏦 IBAN / Banques FR",
                "access": "Données publiques — base locale",
            },
            {
                "name": "Répertoire BDL (Liban)",
                "url": "https://www.bdl.gov.lb",
                "description": "Liste des établissements bancaires libanais avec codes BIC et adresses.",
                "type": "🏦 IBAN / Banques LB",
                "access": "Données publiques — base locale",
            },
            {
                "name": "Registre IBAN (SWIFT)",
                "url": "https://www.swift.com/standards/data-standards/iban",
                "description": "Structure officielle IBAN pour 80+ pays.",
                "type": "🏦 Structure IBAN",
                "access": "Standard international — base locale",
            },
            {
                "name": "Anthropic Claude",
                "url": "https://www.anthropic.com",
                "description": "Modèle claude-sonnet pour la synthèse OSINT et scoring IA.",
                "type": "🤖 IA / Synthèse",
                "access": "API payante — clé requise",
            },
        ]
        for src in sources:
            with st.expander(f"{src['type']} — **{src['name']}**"):
                st.markdown(f"🔗 [{src['url']}]({src['url']})")
                st.markdown(src["description"])
                st.markdown(f"**Accès :** {src['access']}")

        st.divider()
        st.subheader("Sources complémentaires recommandées")
        extra = [
            ("Infogreffe", "https://www.infogreffe.fr", "Registre des entreprises françaises"),
            ("BODACC", "https://www.bodacc.fr", "Annonces légales, procédures collectives"),
            ("AMF", "https://www.amf-france.org", "Régulation marchés financiers FR"),
            ("ACPR", "https://www.acpr.banque-france.fr", "Supervision bancaire et assurance FR"),
            ("World-Check (LSEG)", "https://www.lseg.com/en/data-analytics/financial-data/kyc", "PEP & Sanctions premium (payant)"),
        ]
        for name, url, desc in extra:
            st.markdown(f"- **[{name}]({url})** — {desc}")

    with tab2:
        st.subheader("🚀 Guide de déploiement")
        st.markdown("### Local")
        st.code("""
git clone https://github.com/VOTRE_ORG/finshield-osint.git
cd finshield-osint
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
""", language="bash")

        st.markdown("### Streamlit Community Cloud")
        st.markdown("""
1. **Fork** ce repo sur GitHub
2. Aller sur [share.streamlit.io](https://share.streamlit.io)
3. **New app** → votre repo → `app.py`
4. **Advanced Settings → Secrets** :
```toml
ANTHROPIC_API_KEY = "sk-ant-votre-clé-ici"
```
5. **Deploy** ✅
""")

        st.markdown("### Structure des fichiers dans le repo")
        st.code("""
votre-repo/
├── app.py                  ← Point d'entrée
├── requirements.txt
├── README.md
├── data/
│   └── banks_fr.py         ← Base banques FR
└── services/
    ├── iban_service.py     ← Moteur IBAN
    ├── osint_service.py    ← Moteur OSINT
    ├── pdf_service.py      ← Génération PDF
    ├── Iban_tab.py         ← Onglet IBAN
    ├── osint_tab.py        ← Onglet OSINT
    ├── bank_search_tab.py  ← Onglet Banques
    └── config_tab.py       ← Onglet Config
""", language="text")

    with tab3:
        st.subheader("🔑 Configuration de la clé API Anthropic")
        st.markdown("""
1. Aller sur [console.anthropic.com](https://console.anthropic.com)
2. **API Keys** → **Create Key**
3. Copier la clé (format `sk-ant-api03-...`)

### Dans Streamlit Cloud — Secrets
""")
        st.code("""
# Advanced Settings → Secrets
ANTHROPIC_API_KEY = "sk-ant-api03-VOTRE_CLE_ICI"
""", language="toml")
        st.warning("⚠️ Ne jamais committer ce fichier sur GitHub !")
        st.markdown("### Variable d'environnement (Docker / serveur)")
        st.code("export ANTHROPIC_API_KEY='sk-ant-api03-VOTRE_CLE'", language="bash")

    with tab4:
        st.subheader("📋 Roadmap")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("**✅ Disponible**")
            for item in [
                "Validation IBAN 80+ pays",
                "Banques France (200+ CIB)",
                "Banques Liban (BDL)",
                "Analyse OSINT Claude AI",
                "OpenSanctions (100+ listes)",
                "Adverse media DuckDuckGo",
                "Rapports PDF",
                "Export JSON",
            ]:
                st.markdown(f"✅ {item}")
        with col2:
            st.warning("**🔄 En cours**")
            for item in [
                "Authentification utilisateurs",
                "Base PostgreSQL / audit",
                "Import CSV sanctions custom",
                "Dashboard métriques",
            ]:
                st.markdown(f"🔄 {item}")
        with col3:
            st.info("**⏳ Planifié**")
            for item in [
                "Module FATF pays à risque",
                "Codes APE/NAF/NACE",
                "Infogreffe / BODACC",
                "API REST FastAPI",
                "Cache Redis",
                "Batch screening CSV",
            ]:
                st.markdown(f"⏳ {item}")
