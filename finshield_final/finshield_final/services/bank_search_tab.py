"""
FinShield — Onglet Recherche Banque
"""
import streamlit as st
import pandas as pd
from banks_fr import lookup_bank_by_cib, search_banks_by_name, get_all_banks, get_bank_types


def render_bank_search_tab():
    st.header("📋 Recherche Banque France")
    st.caption("Base de 200+ établissements bancaires français — Code CIB, nom, BIC, type")

    search_mode = st.radio(
        "Mode de recherche",
        ["🔢 Par code CIB", "🔤 Par nom", "📊 Parcourir tout"],
        horizontal=True,
    )
    st.divider()

    if search_mode == "🔢 Par code CIB":
        col1, col2 = st.columns([1, 3])
        with col1:
            cib = st.text_input("Code CIB (5 chiffres)", placeholder="30006", max_chars=5)
        with col2:
            st.info("💡 Le code CIB correspond aux 5 premiers chiffres du BBAN dans un IBAN français.")

        if cib:
            result = lookup_bank_by_cib(cib)
            if result:
                st.success(f"✅ Établissement trouvé pour CIB **{cib.zfill(5)}**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Nom", result["name"][:30])
                c2.metric("BIC/SWIFT", result.get("bic", "—"))
                c3.metric("Ville", result.get("city", "—"))
                st.markdown(f"**Type :** {result.get('type', '—')}")
                st.markdown(f"**Code CIB :** `{result['cib']}`")
            elif cib.strip():
                st.warning(f"⚠️ Code CIB **{cib}** non trouvé dans la base locale.")

    elif search_mode == "🔤 Par nom":
        query = st.text_input("Nom ou partie du nom", placeholder="Société Générale, Crédit Mutuel, Boursorama...")
        if query and len(query) >= 2:
            results = search_banks_by_name(query, max_results=15)
            if results:
                st.success(f"**{len(results)} résultat(s)** pour « {query} »")
                df = pd.DataFrame(results)[["cib", "name", "bic", "city", "type", "score"]]
                df.columns = ["Code CIB", "Nom", "BIC", "Ville", "Type", "Score match"]
                df["Score match"] = df["Score match"].apply(lambda x: f"{x:.0f}%")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("Aucun établissement trouvé.")
        elif query:
            st.info("Saisissez au moins 2 caractères.")

    else:
        all_banks = get_all_banks()
        df = pd.DataFrame(all_banks)
        col1, col2 = st.columns(2)
        with col1:
            type_filter = st.multiselect("Filtrer par type", get_bank_types())
        with col2:
            city_filter = st.text_input("Filtrer par ville", placeholder="Paris, Lyon...")

        filtered = df.copy()
        if type_filter:
            filtered = filtered[filtered["type"].isin(type_filter)]
        if city_filter:
            filtered = filtered[filtered["city"].str.contains(city_filter, case=False, na=False)]

        st.markdown(f"**{len(filtered)}** établissement(s) affiché(s)")
        display_df = filtered[["cib", "name", "bic", "city", "type"]].copy()
        display_df.columns = ["Code CIB", "Nom", "BIC/SWIFT", "Ville", "Type"]
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=450)
        st.download_button(
            "📥 Exporter CSV",
            display_df.to_csv(index=False).encode("utf-8"),
            file_name="banques_fr.csv",
            mime="text/csv",
        )

    with st.expander("ℹ️ Types d'établissements"):
        types_desc = {
            "Banque commerciale":        "Banques universelles à capitaux privés",
            "Banque coopérative":        "Structures mutualistes (CA, CM, BP...)",
            "Caisse d'épargne":          "Réseau Caisse d'Épargne (groupe BPCE)",
            "Banque en ligne":           "Banques 100% numériques",
            "Néobanque":                 "Fintechs avec agrément bancaire ou de paiement",
            "Banque privée":             "Gestion de fortune",
            "Banque d'investissement":   "CIB, marchés de capitaux, M&A",
            "Banque publique":           "Établissements à capitaux publics",
            "Établissement de paiement": "Agréés ACPR pour services de paiement uniquement",
        }
        for t, desc in types_desc.items():
            st.markdown(f"**{t}** — {desc}")
