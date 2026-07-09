import sqlite3
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

# connexion a la base de donnees
def connexion_db():
    conn = sqlite3.connect('transport_data.db')
    return conn

# creation de la table si elle n'existe pas encore
def creer_table():
    conn = connexion_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS collectes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_usager TEXT,
            date_voyage TEXT,
            quartier_origine TEXT,
            type_transport TEXT,
            probleme_rencontre TEXT,
            satisfaction INTEGER
        )
    """)
    conn.commit()
    conn.close()

creer_table()

st.set_page_config(page_title="Suivi des Transports Yaounde", layout="wide")

st.title("Application de Collecte : Transport Urbain a Yaounde")
st.write("---")

col1, col2 = st.columns([1, 2])

# ----- formulaire -----
with col1:
    st.subheader("Formulaire de Saisie")

    with st.form("form_saisie_transport", clear_on_submit=True):
        nom = st.text_input("Nom de l'usager :")
        date_v = st.date_input("Date du voyage :", date.today())
        quartier = st.selectbox("Quartier de depart :", ["NGOA", "MESSASSI", "BASTOS", "MESSA", "BIYEM-ASSI"])
        transport = st.radio("Moyen de transport emprunte :", ["Taxi", "Moto-Taxi", "Bus"])
        probleme = st.selectbox("Probleme majeur identifie :", ["Surcharge", "Tarif eleve", "Retard", "Etat du vehicule", "Aucun"])
        satisfaction = st.slider("Note de satisfaction generale (0 a 10) :", 0, 10, 5)

        envoyer = st.form_submit_button("Enregistrer la fiche")

    if envoyer:
        nom = nom.strip()

        if nom == "" or len(nom) < 2:
            st.error("Le nom doit contenir au moins 2 caracteres.")
        else:
            conn = connexion_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO collectes (nom_usager, date_voyage, quartier_origine, type_transport, probleme_rencontre, satisfaction) VALUES (?, ?, ?, ?, ?, ?)",
                (nom, str(date_v), quartier, transport, probleme, satisfaction)
            )
            conn.commit()
            conn.close()

            st.success("Donnees enregistrees avec succes !")
            st.rerun()

# ----- lecture des donnees -----
conn = connexion_db()
df = pd.read_sql_query("SELECT * FROM collectes", conn)
conn.close()

with col2:
    st.subheader("Registre des Donnees")
    if len(df) == 0:
        st.info("Le registre est vide pour le moment.")
    else:
        st.dataframe(df, use_container_width=True)

# ----- statistiques -----
st.write("---")
st.header("Rapport Analytique")

if len(df) == 0:
    st.warning("Pas encore de statistiques a afficher.")
else:
    moyenne = df['satisfaction'].mean()
    total = len(df)

    k1, k2 = st.columns(2)
    k1.metric("Nombre de fiches", total)
    k2.metric("Satisfaction moyenne", str(round(moyenne, 1)) + " / 10")

    st.write("### Graphiques")
    g1, g2 = st.columns(2)

    with g1:
        compte_probleme = df['probleme_rencontre'].value_counts().reset_index()
        compte_probleme.columns = ['Type de probleme', 'Nombre']
        fig1 = px.bar(compte_probleme, x='Type de probleme', y='Nombre', title="Incidents signales")
        st.plotly_chart(fig1, use_container_width=True)

    with g2:
        fig2 = px.pie(df, names='type_transport', title="Usage par type de transport")
        st.plotly_chart(fig2, use_container_width=True)