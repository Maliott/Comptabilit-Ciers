import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Trésorerie Sou des Écoles", page_icon="💰", layout="wide")

# Dossier de stockage des justificatifs
UPLOAD_DIR = "justificatifs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
CSV_FILE = "depenses_sou.csv"

st.title("💰 Gestion de la Trésorerie — Sou des Écoles")

tab1, tab2 = st.tabs(["📝 Saisir une dépense", "📊 Tableau de bord Trésorier"])

# --- ONGLET 1 : SAISIE ---
with tab1:
    st.subheader("Enregistrer un nouveau justificatif")
    
    col_event, col_date = st.columns(2)
    with col_event:
        manifestation = st.selectbox(
            "Manifestation *", 
            ["Chalet gourmand", "Tombola", "Fête de l'école"]
        )
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
        if nom_prenom and enseigne and montant_ttc > 0 and piece_jointe:
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
            st.error("⚠️ Veuillez remplir tous les champs obligatoires et joindre un justificatif.")

# --- ONGLET 2 : TABLEAU DE BORD TRÉSORIER ---
with tab2:
    st.subheader("📊 Suivi global et consultation des justificatifs")
    
    CODE_TRESORIER = "1234"
    mot_de_passe = st.text_input("🔒 Entrez le code d'accès Trésorier :", type="password")
    
    if mot_de_passe == CODE_TRESORIER:
        st.success("Accès autorisé.")
        
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            
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
            st.dataframe(filtered_df, use_container_width=True)
            
            st.divider()
            st.subheader("🔎 Consulter / Télécharger une pièce jointe")
            
            # Sélection de la dépense à consulter
            df['Libelle'] = df['Date'] + " - " + df['Bénévole'] + " - " + df['Enseigne'] + " (" + df['Montant TTC (€)'].astype(str) + " €)"
            selected_entry = st.selectbox("Choisissez une dépense pour afficher son justificatif :", df['Libelle'])
            
            selected_row = df[df['Libelle'] == selected_entry].iloc[0]
            file_path = selected_row['Justificatif']
            
            if os.path.exists(file_path):
                file_ext = os.path.splitext(file_path)[1].lower()
                with open(file_path, "rb") as file:
                    btn = st.download_button(
                        label="📥 Télécharger le justificatif",
                        data=file,
                        file_name=os.path.basename(file_path)
                    )
                
                # Affichage direct si c'est une image
                if file_ext in [".png", ".jpg", ".jpeg"]:
                    st.image(file_path, caption=f"Justificatif : {selected_row['Enseigne']}", use_column_width=True)
                elif file_ext == ".pdf":
                    st.info("📄 C'est un document PDF. Utilisez le bouton ci-dessus pour le télécharger et l'ouvrir.")
            else:
                st.warning("Fichier introuvable sur le serveur.")
                
        else:
            st.info("Aucune dépense enregistrée pour le moment.")
    elif mot_de_passe != "":
        st.error("Code d'accès incorrect.")
