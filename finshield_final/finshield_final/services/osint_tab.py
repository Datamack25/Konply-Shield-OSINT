"""
FinShield — Onglet Analyse OSINT
"""
import streamlit as st
import plotly.graph_objects as go
from osint_service import analyze_entity, OSINTResult
from pdf_service import generate_osint_pdf


def _risk_gauge(score: float, risk_level: str) -> go.Figure:
    color_map = {"low": "#52B788", "medium": "#F4A261", "high": "#E63946", "critical": "#6A0572"}
    color = color_map.get(risk_level, "#ADB5BD")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(score * 100, 1),
        number={"suffix": "%", "font": {"size": 28}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar":  {"color": color},
            "steps": [
                {"range": [0,  25], "color": "#D8F3DC"},
                {"range": [25, 50], "color": "#FFE8CC"},
                {"range": [50, 75], "color": "#FFDAD9"},
                {"range": [75, 100],"color": "#E9C8F0"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "value": score * 100},
        },
        title={"text": f"Score de risque — {risk_level.upper()}", "font": {"size": 14}},
    ))
    fig.update_layout(height=220, margin=dict(t=40, b=10, l=20, r=20), paper_bgcolor="white")
    return fig


def render_osint_tab():
    st.header("🔍 Analyse OSINT")
    st.caption("Due diligence : sanctions, PEP, presse, réputation — propulsé par Claude AI")

    api_key = st.session_state.get("anthropic_api_key", "")
    if not api_key:
        st.warning("⚠️ Clé API Anthropic non configurée. L'analyse IA sera désactivée (scoring heuristique uniquement).")

    with st.form("osint_form"):
        col1, col2 = st.columns(2)
        with col1:
            entity_name = st.text_input("Nom de l'entité *", placeholder="Ex : Jean Dupont ou ACME Corp SA")
            entity_type = st.selectbox(
                "Type",
                ["person", "company"],
                format_func=lambda x: "Personne physique" if x == "person" else "Personne morale",
            )
        with col2:
            country    = st.text_input("Pays (optionnel)", placeholder="France, Liban, USA...")
            birth_date = st.text_input("Date de naissance (optionnel)", placeholder="1975-03-15")

        context = st.text_area(
            "Contexte supplémentaire (optionnel)",
            placeholder="Ex : Directeur général de XYZ Corp, anciennement ministre des finances de...",
            height=80,
        )
        submitted = st.form_submit_button("🔍 Lancer l'analyse OSINT", use_container_width=True, type="primary")

    if not submitted or not entity_name.strip():
        st.divider()
        st.subheader("ℹ️ Comment ça fonctionne ?")
        cols = st.columns(3)
        steps = [
            ("1️⃣ OpenSanctions", "Vérification contre les listes ONU, UE, OFAC, SECO, UK HMT..."),
            ("2️⃣ Presse & Web",  "Recherche de contenus négatifs : fraude, corruption, PEP."),
            ("3️⃣ Synthèse IA",   "Claude analyse tout et produit un rapport avec score de risque."),
        ]
        for col, (title, desc) in zip(cols, steps):
            col.info(f"**{title}**\n\n{desc}")
        return

    with st.spinner(f"Analyse OSINT de **{entity_name}** en cours... (10-30 secondes)"):
        result = analyze_entity(
            entity_name=entity_name.strip(),
            entity_type=entity_type,
            country=country.strip(),
            birth_date=birth_date.strip(),
            api_key=api_key,
            additional_context=context.strip(),
        )

    if result.error:
        st.error(f"❌ Erreur : {result.error}")
        return

    st.divider()
    st.subheader(f"Résultats pour : **{entity_name}**")

    col_gauge, col_kpis = st.columns([1, 2])
    with col_gauge:
        fig = _risk_gauge(result.risk_score, result.risk_level)
        st.plotly_chart(fig, use_container_width=True)

    with col_kpis:
        c1, c2 = st.columns(2)
        c1.metric("Niveau de risque", result.risk_badge)
        c2.metric("Score", f"{result.risk_score:.0%}")
        c1.metric("Hits sanctions", len(result.sanctions_hits))
        c2.metric("Adverse media", len(result.adverse_media))
        if result.summary:
            st.info(f"📋 **Résumé :** {result.summary}")

    st.divider()

    t1, t2, t3, t4 = st.tabs(["⚠️ Sanctions", "📰 Adverse Media", "🏛️ PEP & Litiges", "📄 Analyse complète"])

    with t1:
        st.subheader("Résultats Sanctions (OpenSanctions)")
        if result.sanctions_hits:
            for h in result.sanctions_hits:
                with st.expander(f"🔴 {h.get('name','—')} — Score : {h.get('score',0):.0%}"):
                    st.markdown(f"**Listes :** {', '.join(h.get('datasets', []))}")
                    st.markdown(f"**Pays :** {', '.join(h.get('countries', []))}")
                    if h.get("source_url"):
                        st.markdown(f"**Source :** [{h['source_url']}]({h['source_url']})")
        else:
            st.success("✅ Aucun hit sanctions identifié dans OpenSanctions.")
        st.caption("Source : OpenSanctions.org — ONU, UE, OFAC, SECO, UK HMT, et 100+ listes")

    with t2:
        st.subheader("Adverse Media — Presse & Web")
        if result.adverse_media:
            for item in result.adverse_media:
                title = item.get("title", "—")
                url   = item.get("url", "")
                src   = item.get("source", "")
                st.markdown(f"• **{title}**")
                if url:
                    st.markdown(f"  🔗 [{url[:60]}]({url})")
                st.caption(f"  Source : {src}")
        else:
            st.success("✅ Aucun résultat négatif identifié dans la presse et le web ouvert.")

    with t3:
        col_pep, col_legal = st.columns(2)
        with col_pep:
            st.subheader("PEP identifiés")
            if result.pep_hits:
                for pep in result.pep_hits:
                    st.warning(f"🏛️ **{pep.get('name','—')}** — {pep.get('position','—')} ({pep.get('country','—')})")
            else:
                st.success("✅ Aucun PEP identifié.")
        with col_legal:
            st.subheader("Litiges & condamnations")
            if result.legal_hits:
                for legal in result.legal_hits:
                    st.error(f"⚖️ {legal.get('description','—')}")
            else:
                st.success("✅ Aucun litige ou condamnation identifié.")

    with t4:
        st.subheader("Analyse détaillée (Claude AI)")
        if result.raw_analysis:
            st.markdown(result.raw_analysis)
        else:
            st.info("Analyse textuelle non disponible (clé API manquante ou erreur).")
        st.divider()
        st.subheader("Sources consultées")
        for src in result.sources_checked:
            st.markdown(f"✅ {src}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Générer rapport PDF", use_container_width=True):
            with st.spinner("Génération PDF..."):
                pdf = generate_osint_pdf(result)
            st.download_button(
                "⬇️ Télécharger le rapport PDF",
                pdf,
                file_name=f"osint_{entity_name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    with col2:
        import json
        st.download_button(
            "📋 Exporter JSON",
            json.dumps({
                "entity":         result.entity,
                "risk_level":     result.risk_level,
                "risk_score":     result.risk_score,
                "sanctions_hits": result.sanctions_hits,
                "adverse_media":  result.adverse_media,
                "summary":        result.summary,
            }, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"osint_{entity_name.replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
        )
