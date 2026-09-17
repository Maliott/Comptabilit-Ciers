import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Trésorerie Sou des Écoles", page_icon="💰", layout="wide")

# Fichiers et dossiers
UPLOAD_DIR = "justificatifs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
CSV_FILE = "depenses_sou.csv"
CSV_ARCHIVE_FILE = "depenses_archivees.csv"

st.title("💰 Gestion de la Trésorerie — Sou des Écoles")

tab1, tab2 = st.tabs(["📝 Saisir une dépense", "📊 Tableau de bord Trésorier"])

# --- ONGLET 1 : SAISIE ---
with tab1:
    st.subheader("Enregistrer un nouveau justificatif")
    
    col_event, col_date = st.columns(2)
    with col_event:
        manifestation_choice = st.selectbox(
            "Manifestation *", 
            ["Chalet gourmand", "Tombola", "Fête de l'école", "Autre"]
        )
        # Gestion du choix "Autre"
        if manifestation_choice == "Autre":
            manifestation = st.text_input("Précisez le nom de la manifestation *")
        else:
            manifestation = manifestation_choice

    with col_date:
        date_depense = st.date_input("Date de la dépense *", datetime.now())
        
    col_ben, col_ens = st.columns(2)
    with col_ben:
        nom_prenom = st.text_input("Nom & Prénom du bénévole / payeur *")
    with col_ens:
        enseigne = st.text_input("Enseigne / Magasin / Fournisseur *")

    col_pay, col_tva_rate = st.columns(2)
    with col_pay:
        mode_paiement = st.selectbox(
            "Mode de paiement *",
            ["Carte Bancaire", "Chèque", "Espèces", "Virement", "Avance bénévole (À rembourser)"]
        )
    with col_tva_rate:
        taux_tva = st.selectbox(
            "Taux de TVA *",
            ["20.0%", "10.0%", "5.5%", "2.1%", "0.0% (Saisie HT manuelle)"]
        )

    col_ttc, col_ht, col_tva = st.columns(3)
    with col_ttc:
        montant_ttc = st.number_input("Montant TTC (€) *", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    
    rate_val = 0.0
    if "20.0%" in taux_tva: rate_val = 0.20
    elif "10.0%" in taux_tva: rate_val = 0.10
    elif "5.5%" in taux_tva: rate_val = 0.055
    elif "2.1%" in taux_tva: rate_val = 0.021

    auto_ht = round(montant_ttc / (1 + rate_val), 2) if rate_val > 0 else montant_ttc
    auto_tva = round(montant_ttc - auto_ht, 2)

    with col_ht:
        montant_ht = st.number_input("Montant HT (€)", min_value=0.0, value=auto_ht, step=0.01, format="%.2f")
    with col_tva:
        montant_tva = st.number_input("Montant TVA (€)", min_value=0.0, value=auto_tva, step=0.01, format="%.2f")

    piece_jointe = st.file_uploader("📷 Photo du ticket de caisse ou PDF de la facture *", type=["png", "jpg", "jpeg", "pdf"])
    
    st.caption("* Champs obligatoires")
    
    if st.button("💾 Valider et enregistrer la dépense", type="primary"):
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
            st.success("✅ Dépense et justificatif enregistrés avec succès !")
        else:
            st.error("⚠️ Veuillez remplir tous les champs obligatoires (y compris le nom de la manifestation si 'Autre' est sélectionné) et joindre un justificatif.")

# --- ONGLET 2 : TABLEAU DE BORD TRÉSORIER ---
with tab2:
    st.subheader("📊 Suivi global et gestion des pièces")
    
    CODE_TRESORIER = "1234"
    mot_de_passe = st.text_input("🔒 Entrez le code d'accès Trésorier :", type="password")
    
    if mot_de_passe == CODE_TRESORIER:
        st.success("Accès autorisé.")
        
        if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
            df = pd.read_csv(CSV_FILE)
            
            if not df.empty:
                # Filtres
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    event_filter = st.selectbox("Filtrer par manifestation", ["Toutes"] + list(df["Manifestation"].unique()))
                with col_f2:
                    pay_filter = st.selectbox("Filtrer par mode de paiement", ["Tous"] + list(df["Mode de paiement"].unique()))
                    
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
                st.subheader("🔎 Consulter, Archiver ou Supprimer une pièce")
                
                # Préparation des libellés pour le menu déroulant
                df['Libelle'] = df['Date'] + " - " + df['Bénévole'] + " - " + df['Enseigne'] + " (" + df['Montant TTC (€)'].astype(str) + " €)"
                selected_entry = st.selectbox("Choisissez une dépense :", df['Libelle'])
                
                selected_idx = df[df['Libelle'] == selected_entry].index[0]
                selected_row = df.loc[selected_idx]
                file_path = selected_row['Justificatif']
                
                # Actions : Télécharger / Archiver / Supprimer
                col_act1, col_act2, col_act3 = st.columns(3)
                
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
                        # Ajouter aux archives
                        archived_row = pd.DataFrame([selected_row.drop('Libelle')])
                        archived_row.to_csv(CSV_ARCHIVE_FILE, mode='a', header=not os.path.exists(CSV_ARCHIVE_FILE), index=False)
                        
                        # Retirer du CSV principal
                        df = df.drop(selected_idx).drop(columns=['Libelle'])
                        df.to_csv(CSV_FILE, index=False)
                        
                        st.success("📦 Dépense archivée avec succès !")
                        st.rerun()

                with col_act3:
                    if st.button("🗑️ Supprimer définitivement", type="primary", use_container_width=True):
                        # Supprimer le fichier image/PDF si présent
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                pass
                        
                        # Retirer du CSV principal
                        df = df.drop(selected_idx).drop(columns=['Libelle'])
                        df.to_csv(CSV_FILE, index=False)
                        
                        st.success("🗑️ Dépense et justificatif supprimés définitivement !")
                        st.rerun()

                # Visualisation de la photo ou du PDF
                if os.path.exists(file_path):
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in [".png", ".jpg", ".jpeg"]:
                        st.image(file_path, caption=f"Justificatif : {selected_row['Enseigne']}", use_container_width=True)
                    elif file_ext == ".pdf":
                        st.info("📄 Document PDF. Téléchargez-le avec le bouton ci-dessus pour le consulter.")
                else:
                    st.warning("Fichier justificatif non trouvé sur le serveur.")

            else:
                st.info("Aucune dépense active à afficher.")
        else:
            st.info("Aucune dépense enregistrée pour le moment.")

        # --- SECTION ARCHIVES ---
        st.divider()
        with st.expander("📁 Voir et consulter les dépenses archivées"):
            if os.path.exists(CSV_ARCHIVE_FILE) and os.path.getsize(CSV_ARCHIVE_FILE) > 0:
                df_archive = pd.read_csv(CSV_ARCHIVE_FILE)
                if not df_archive.empty:
                    st.dataframe(df_archive, use_container_width=True)
                    st.caption(f"Total des dépenses archivées : {df_archive['Montant TTC (€)'].sum():.2f} € ({len(df_archive)} pièces)")
                    
                    st.divider()
                    st.subheader("🔎 Visualiser un justificatif archivé")
                    
                    df_archive['Libelle'] = df_archive['Date'] + " - " + df_archive['Bénévole'] + " - " + df_archive['Enseigne'] + " (" + df_archive['Montant TTC (€)'].astype(str) + " €)"
                    selected_archive_entry = st.selectbox("Choisissez une dépense archivée :", df_archive['Libelle'], key="archive_select")
                    
                    arch_row = df_archive[df_archive['Libelle'] == selected_archive_entry].iloc[0]
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
                        
                        arch_ext = os.path.splitext(arch_file_path)[1].lower()
                        if arch_ext in [".png", ".jpg", ".jpeg"]:
                            st.image(arch_file_path, caption=f"Justificatif archivé : {arch_row['Enseigne']}", use_container_width=True)
                        elif arch_ext == ".pdf":
                            st.info("📄 Document PDF. Téléchargez-le avec le bouton ci-dessus.")
                    else:
                        st.warning("Fichier justificatif archivé introuvable sur le serveur.")
                else:
                    st.info("Aucune dépense archivée.")
            else:
                st.info("Aucune dépense archivée pour l'instant.")

    elif mot_de_passe != "":
        st.error("Code d'accès incorrect.")
