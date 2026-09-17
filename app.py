import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(page_title="Trésorerie Sou des Écoles", page_icon="💰", layout="wide")

# 2. Masquer TOUS les éléments d'interface Streamlit (Header, Toolbar, Badge rouge du bas, Menu)
hide_streamlit_style = """
    <style>
    /* Masquer le menu hamburger et le footer par défaut */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Masquer la barre supérieure (GitHub, Crayon, Share) */
    [data-testid="stHeader"] {display: none !important;}
    .stAppToolbar {display: none !important;}
    
    /* Masquer le badge "Created with Streamlit" / "Hosted with Streamlit" en bas */
    [data-testid="stStatusWidget"] {display: none !important;}
    .stAppDeployButton {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    div[class*="styles_viewerBadge"] {display: none !important;}
    a[href*="streamlit.io"] {display: none !important;}
    #stDecoration {display: none !important;}
    
    /* Ajuster la marge supérieure laissée par le header masqué */
    .block-container {
        padding-top: 1.5rem !important;
    }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 3. Fichiers et dossiers
UPLOAD_DIR = "justificatifs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
CSV_FILE = "depenses_sou.csv"
CSV_ARCHIVE_FILE = "depenses_archivees.csv"

# 4. Codes d'accès
try:
    CODE_TRESORIER = st.secrets["CODE_TRESORIER"]
except Exception:
    CODE_TRESORIER = "1234"

# Code secret requis pour valider toute suppression
CODE_SUPPRESSION = " suppression "

st.title("💰 Gestion de la Trésorerie — Sou des Écoles")

tab_saisie, tab_tresorier = st.tabs(["📝 Saisir une dépense", "📊 Tableau de bord Trésorier"])

# ==========================================
# --- ONGLET 1 : SAISIE DES DÉPENSES ---
# ==========================================
with tab_saisie:
    st.subheader("Enregistrer un nouveau justificatif")

    # Initialisation de la clé d'upload pour forcer le réenregistrement du file_uploader
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    col_event, col_date = st.columns(2)
    with col_event:
        manifestation_choice = st.selectbox(
            "Manifestation *", 
            ["Chalet gourmand", "Tombola", "Fête de l'école", "Autre"],
            key="saisie_manifestation_choice"
        )
        
        # Le champ n'apparaît QUE si "Autre" est sélectionné
        if manifestation_choice == "Autre":
            manifestation_autre = st.text_input("Précisez le nom de la manifestation *", key="saisie_manifestation_autre")
        else:
            manifestation_autre = ""

    with col_date:
        date_depense = st.date_input("Date de la dépense *", datetime.now(), key="saisie_date")

    with st.form("form_saisie_depense", clear_on_submit=True):
        col_ben, col_ens = st.columns(2)
        with col_ben:
            nom_prenom = st.text_input("Nom & Prénom du bénévole / payeur *", key="form_nom_prenom")
        with col_ens:
            enseigne = st.text_input("Enseigne / Magasin / Fournisseur *", key="form_enseigne")

        col_pay, col_tva_rate = st.columns(2)
        with col_pay:
            mode_paiement = st.selectbox(
                "Mode de paiement *",
                ["Carte Bancaire", "Chèque", "Espèces", "Virement", "Avance bénévole (À rembourser)"],
                key="form_mode_paiement"
            )
        with col_tva_rate:
            taux_tva = st.selectbox(
                "Taux de TVA *",
                ["20.0%", "10.0%", "5.5%", "2.1%", "0.0% (Saisie HT manuelle)"],
                key="form_taux_tva"
            )

        col_ttc, col_ht, col_tva = st.columns(3)
        with col_ttc:
            montant_ttc = st.number_input("Montant TTC (€) *", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="form_ttc")

        rate_val = 0.0
        if "20.0%" in taux_tva: rate_val = 0.20
        elif "10.0%" in taux_tva: rate_val = 0.10
        elif "5.5%" in taux_tva: rate_val = 0.055
        elif "2.1%" in taux_tva: rate_val = 0.021

        auto_ht = round(montant_ttc / (1 + rate_val), 2) if rate_val > 0 else montant_ttc
        auto_tva = round(montant_ttc - auto_ht, 2)

        with col_ht:
            montant_ht = st.number_input("Montant HT (€)", min_value=0.0, value=auto_ht, step=0.01, format="%.2f", key="form_ht")
        with col_tva:
            montant_tva = st.number_input("Montant TVA (€)", min_value=0.0, value=auto_tva, step=0.01, format="%.2f", key="form_tva")

        piece_jointe = st.file_uploader(
            "📷 Photo du ticket de caisse ou PDF de la facture *", 
            type=["png", "jpg", "jpeg", "pdf"],
            key=f"uploader_{st.session_state.uploader_key}"
        )
        
        st.caption("* Champs obligatoires")
        
        submit_btn = st.form_submit_button("💾 Valider et enregistrer la dépense", type="primary")

    if submit_btn:
        manifestation = manifestation_autre.strip() if manifestation_choice == "Autre" else manifestation_choice
        
        if manifestation and nom_prenom and enseigne and montant_ttc > 0 and piece_jointe:
            file_ext = os.path.splitext(piece_jointe.name)[1]
            clean_name = f"{date_depense}_{manifestation.replace(' ', '_')}_{nom_prenom.replace(' ', '_')}{file_ext}"
            file_path = os.path.join(UPLOAD_DIR, clean_name)
            
            with open(file_path, "wb") as f:
                f.write(piece_jointe.getbuffer())
            
            new_data = pd.DataFrame([{
                "Date": date_depense.strftime("%Y-%m-%d"),
                "Manifestation": manifestation,
                "Bénévole": nom_prenom,
                "Enseigne": enseigne,
                "Mode de paiement": mode_paiement,
                "Montant TTC (€)": round(montant_ttc, 2),
                "Montant HT (€)": round(montant_ht, 2),
                "TVA (€)": round(montant_tva, 2),
                "Justificatif": file_path
            }])
            
            new_data.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
            
            # Réinitialiser le composant d'import de fichier
            st.session_state.uploader_key += 1
            
            st.success("✅ Dépense et justificatif enregistrés avec succès ! Le formulaire a été réinitialisé.")
            st.rerun()
        else:
            st.error("⚠️ Veuillez remplir tous les champs obligatoires (y compris la précision du nom si 'Autre') et joindre un justificatif.")

# ==========================================
# --- ONGLET 2 : TABLEAU DE BORD TRÉSORIER ---
# ==========================================
with tab_tresorier:
    mot_de_passe = st.text_input("🔒 Entrez le code d'accès Trésorier :", type="password")
    
    if mot_de_passe == str(CODE_TRESORIER):
        st.success("Accès autorisé.")
        
        # Sous-onglets dans la partie Trésorier
        sub_tab1, sub_tab2 = st.tabs(["📊 Dépenses en cours & Pièces", "🎪 Bilan des Manifestations (Archivées)"])
        
        # ----------------------------------------------------
        # SOUS-ONGLET 1 : DÉPENSES EN COURS & GESTION DES PIÈCES
        # ----------------------------------------------------
        with sub_tab1:
            st.subheader("📊 Suivi général et gestion des pièces")
            
            if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
                df = pd.read_csv(CSV_FILE)
                
                if not df.empty:
                    # Filtres
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        event_filter = st.selectbox("Filtrer par manifestation", ["Toutes"] + list(df["Manifestation"].unique()), key="f_event_global")
                    with col_f2:
                        pay_filter = st.selectbox("Filtrer par mode de paiement", ["Tous"] + list(df["Mode de paiement"].unique()), key="f_pay_global")
                        
                    filtered_df = df.copy()
                    if event_filter != "Toutes":
                        filtered_df = filtered_df[filtered_df["Manifestation"] == event_filter]
                    if pay_filter != "Tous":
                        filtered_df = filtered_df[filtered_df["Mode de paiement"] == pay_filter]

                    # Indicateurs
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total TTC", f"{filtered_df['Montant TTC (€)'].sum():.2f} €")
                    m2.metric("Total HT", f"{filtered_df['Montant HT (€)'].sum():.2f} €")
                    m3.metric("Total TVA", f"{filtered_df['TVA (€)'].sum():.2f} €")
                    m4.metric("Nombre de pièces", len(filtered_df))

                    st.divider()
                    st.subheader("📋 Liste des dépenses en cours")
                    st.dataframe(filtered_df, use_container_width=True)
                    
                    st.divider()
                    st.subheader("🔎 Consulter, Archiver ou Supprimer une dépense en cours")
                    
                    df['Libelle'] = df['Date'] + " - " + df['Bénévole'] + " - " + df['Enseigne'] + " (" + df['Montant TTC (€)'].astype(str) + " €)"
                    selected_entry = st.selectbox("Choisissez une dépense :", df['Libelle'], key="select_active")
                    
                    selected_idx = df[df['Libelle'] == selected_entry].index[0]
                    selected_row = df.loc[selected_idx]
                    file_path = selected_row['Justificatif']
                    
                    # Actions
                    col_act1, col_act2 = st.columns(2)
                    
                    with col_act1:
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as file:
                                st.download_button(
                                    label="📥 Télécharger le justificatif",
                                    data=file,
                                    file_name=os.path.basename(file_path),
                                    use_container_width=True,
                                    key="dl_active"
                                )
                    
                    with col_act2:
                        if st.button("📦 Archiver la dépense", type="secondary", use_container_width=True):
                            archived_row = pd.DataFrame([selected_row.drop('Libelle')])
                            archived_row.to_csv(CSV_ARCHIVE_FILE, mode='a', header=not os.path.exists(CSV_ARCHIVE_FILE), index=False)
                            
                            df = df.drop(selected_idx).drop(columns=['Libelle'])
                            df.to_csv(CSV_FILE, index=False)
                            st.success("📦 Dépense archivée avec succès !")
                            st.rerun()

                    # Zone de suppression sécurisée avec mot de passe
                    with st.expander("🚨 Supprimer cette dépense en cours"):
                        st.warning("⚠️ Attention : La suppression est définitive. Le fichier justificatif ainsi que la ligne dans le tableau seront supprimés irréversiblement.")
                        
                        pwd_del_active = st.text_input("🔑 Mot de passe de suppression requis :", type="password", key="pwd_del_active")
                        confirm_del_active = st.checkbox("Je confirme vouloir supprimer définitivement cette ligne et son justificatif", key="chk_del_active")
                        
                        is_pwd_correct_active = (pwd_del_active == CODE_SUPPRESSION)
                        
                        if pwd_del_active != "" and not is_pwd_correct_active:
                            st.error("Mot de passe de suppression incorrect.")

                        if st.button("🗑️ Confirmer la suppression définitive", type="primary", disabled=not (confirm_del_active and is_pwd_correct_active), key="btn_del_active"):
                            if os.path.exists(file_path):
                                try:
                                    os.remove(file_path)
                                except Exception:
                                    pass
                            
                            df = df.drop(selected_idx).drop(columns=['Libelle'])
                            df.to_csv(CSV_FILE, index=False)
                            st.success("🗑️ Dépense supprimée !")
                            st.rerun()

                    # Aperçu image/PDF
                    if os.path.exists(file_path):
                        file_ext = os.path.splitext(file_path)[1].lower()
                        if file_ext in [".png", ".jpg", ".jpeg"]:
                            st.image(file_path, caption=f"Justificatif : {selected_row['Enseigne']}", use_container_width=True)
                        elif file_ext == ".pdf":
                            st.info("📄 Document PDF. Utilisez le bouton ci-dessus pour le télécharger.")
                    else:
                        st.warning("Fichier introuvable sur le serveur.")

                else:
                    st.info("Aucune dépense active à afficher.")
            else:
                st.info("Aucune dépense enregistrée pour le moment.")

            # SECTION ARCHIVES
            st.divider()
            with st.expander("📁 Voir, consulter ou supprimer des dépenses archivées"):
                if os.path.exists(CSV_ARCHIVE_FILE) and os.path.getsize(CSV_ARCHIVE_FILE) > 0:
                    df_archive = pd.read_csv(CSV_ARCHIVE_FILE)
                    if not df_archive.empty:
                        st.dataframe(df_archive, use_container_width=True)
                        st.caption(f"Total archivé : {df_archive['Montant TTC (€)'].sum():.2f} € ({len(df_archive)} pièces)")
                        
                        st.divider()
                        st.subheader("🔎 Visualiser ou Supprimer un justificatif archivé")
                        df_archive['Libelle'] = df_archive['Date'] + " - " + df_archive['Bénévole'] + " - " + df_archive['Enseigne'] + " (" + df_archive['Montant TTC (€)'].astype(str) + " €)"
                        selected_archive_entry = st.selectbox("Choisissez une dépense archivée :", df_archive['Libelle'], key="archive_select")
                        
                        arch_idx = df_archive[df_archive['Libelle'] == selected_archive_entry].index[0]
                        arch_row = df_archive.loc[arch_idx]
                        arch_file_path = arch_row['Justificatif']
                        
                        if os.path.exists(arch_file_path):
                            with open(arch_file_path, "rb") as file:
                                st.download_button(
                                    label="📥 Télécharger le justificatif archivé",
                                    data=file,
                                    file_name=os.path.basename(arch_file_path),
                                    use_container_width=True,
                                    key="dl_archive"
                                )
                        
                        # Zone de suppression d'archive sécurisée avec mot de passe
                        with st.expander("🚨 Supprimer cette dépense archivée"):
                            st.warning("⚠️ Attention : La suppression d'une dépense archivée est irréversible et retirera définitivement cette pièce du bilan financier.")
                            
                            pwd_del_archive = st.text_input("🔑 Mot de passe de suppression requis :", type="password", key="pwd_del_archive")
                            confirm_del_archive = st.checkbox("Je confirme vouloir supprimer définitivement cette ligne archivée et son justificatif", key="chk_del_archive")
                            
                            is_pwd_correct_archive = (pwd_del_archive == CODE_SUPPRESSION)
                            
                            if pwd_del_archive != "" and not is_pwd_correct_archive:
                                st.error("Mot de passe de suppression incorrect.")

                            if st.button("🗑️ Confirmer la suppression définitive de l'archive", type="primary", disabled=not (confirm_del_archive and is_pwd_correct_archive), key="btn_del_archive"):
                                if os.path.exists(arch_file_path):
                                    try:
                                        os.remove(arch_file_path)
                                    except Exception:
                                        pass
                                
                                df_archive = df_archive.drop(arch_idx).drop(columns=['Libelle'])
                                df_archive.to_csv(CSV_ARCHIVE_FILE, index=False)
                                st.success("🗑️ Dépense archivée supprimée avec succès !")
                                st.rerun()

                        if os.path.exists(arch_file_path):
                            arch_ext = os.path.splitext(arch_file_path)[1].lower()
                            if arch_ext in [".png", ".jpg", ".jpeg"]:
                                st.image(arch_file_path, caption=f"Justificatif archivé : {arch_row['Enseigne']}", use_container_width=True)
                            elif arch_ext == ".pdf":
                                st.info("📄 Document PDF.")
                        else:
                            st.warning("Fichier introuvable sur le serveur.")
                    else:
                        st.info("Aucune dépense archivée.")
                else:
                    st.info("Aucune dépense archivée pour l'instant.")

        # ----------------------------------------------------
        # SOUS-ONGLET 2 : BILAN DES MANIFESTATIONS (ARCHIVÉES)
        # ----------------------------------------------------
        with sub_tab2:
            st.subheader("🎪 Bilan financier par manifestation (Dépenses archivées)")
            
            if os.path.exists(CSV_ARCHIVE_FILE) and os.path.getsize(CSV_ARCHIVE_FILE) > 0:
                df_manifest_archive = pd.read_csv(CSV_ARCHIVE_FILE)
                
                if not df_manifest_archive.empty:
                    list_manifestations = sorted(list(df_manifest_archive["Manifestation"].unique()))
                    selected_manifestation = st.selectbox(
                        "🎯 Choisissez la manifestation archivée à analyser :", 
                        list_manifestations,
                        key="select_manifest_recap_archive"
                    )
                    
                    df_event = df_manifest_archive[df_manifest_archive["Manifestation"] == selected_manifestation]
                    
                    st.divider()
                    
                    # Cartes d'indicateurs
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total TTC", f"{df_event['Montant TTC (€)'].sum():.2f} €")
                    c2.metric("Total HT", f"{df_event['Montant HT (€)'].sum():.2f} €")
                    c3.metric("Total TVA", f"{df_event['TVA (€)'].sum():.2f} €")
                    c4.metric("Factures / Tickets", len(df_event))
                    
                    st.divider()
                    
                    col_table, col_chart = st.columns([3, 2])
                    
                    with col_table:
                        st.subheader(f"📋 Dépenses archivées : {selected_manifestation}")
                        st.dataframe(df_event.drop(columns=['Justificatif']), use_container_width=True)
                        
                        # Exportation CSV des dépenses archivées de cet événement
                        csv_data = df_event.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"📥 Exporter le bilan de '{selected_manifestation}' (CSV)",
                            data=csv_data,
                            file_name=f"bilan_archive_{selected_manifestation.replace(' ', '_')}.csv",
                            mime="text/csv"
                        )

                    with col_chart:
                        st.subheader("💳 Répartition par paiement")
                        chart_data = df_event.groupby("Mode de paiement")["Montant TTC (€)"].sum()
                        st.bar_chart(chart_data)

                else:
                    st.info("Aucune dépense archivée à analyser pour le moment.")
            else:
                st.info("Aucune dépense n'a encore été archivée.")

    elif mot_de_passe != "":
        st.error("Code d'accès incorrect.")
