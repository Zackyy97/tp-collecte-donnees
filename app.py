import plotly.express as px
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# 1. CONFIGURATION DE LA BASE DE DONNÉES (L'équivalent de ton schéma Mongoose)
def init_db():
    conn = sqlite3.connect('transport_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collectes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_usager TEXT,
            date_voyage TEXT,
            quartier_origine TEXT,
            type_transport TEXT,
            probleme_rencontre TEXT,
            satisfaction INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Initialisation au lancement
init_db()

# 2. INTERFACE UTILISATEUR (UI avec Streamlit)
st.set_page_config(page_title="Collecte Transport Yaoundé", layout="wide")

st.title("🚖 Application de Collecte : Transport Urbain")
st.markdown("---")

# Création de deux colonnes (comme un Row/Col en CSS)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📝 Formulaire de Saisie")
    
    # Utilisation d'un formulaire pour regrouper les inputs
    with st.form("form_collecte", clear_on_submit=True):
        nom = st.text_input("Nom de l'usager")
        date_v = st.date_input("Date du voyage", date.today())
        quartier = st.selectbox("Quartier d'origine", ["NGOA", "MESSASSI", "BASTOS", "MESSA", "BIYEM-ASSI"])
        transport = st.radio("Moyen de transport", ["Taxi", "Moto-Taxi", "Bus"])
        probleme = st.selectbox("Problème majeur", ["Surcharge", "Tarif élevé", "Retard", "État du véhicule", "Aucun"])
        satisfaction = st.slider("Niveau de satisfaction (0 à 10)", 0, 10, 5)
        
        submit = st.form_submit_button("Enregistrer les données")

    if submit:
        # 3. LOGIQUE D'INSERTION (Le "POST" de ton API)
        if nom:
            conn = sqlite3.connect('transport_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO collectes (nom_usager, date_voyage, quartier_origine, type_transport, probleme_rencontre, satisfaction)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nom, str(date_v), quartier, transport, probleme, satisfaction))
            conn.commit()
            conn.close()
            st.success(f"Données enregistrées pour {nom} !")
        else:
            st.error("Veuillez entrer un nom.")

with col2:
    st.subheader("📊 Données Collectées")
    
    # 4. AFFICHAGE DES DONNÉES (Le "GET" de ton API)
    conn = sqlite3.connect('transport_data.db')
    df = pd.read_sql_query("SELECT * FROM collectes", conn)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucune donnée collectée pour le moment.")

##
# --- SECTION 2 : ANALYSE DESCRIPTIVE (Le Cœur du TP) ---
st.markdown("---")
st.header("📈 Analyse Descriptive des Données")

if not df.empty:
    # 1. KPI (Key Performance Indicators) - Les statistiques rapides
    avg_sat = df['satisfaction'].mean()
    total_entries = len(df)
    
    m1, m2 = st.columns(2)
    m1.metric("Nombre de collectes", total_entries)
    m2.metric("Satisfaction Moyenne", f"{avg_sat:.2f} / 10")

    st.write("### Visualisations")
    c1, c2 = st.columns(2)

    with c1:
        # 2. GRAPHIQUE EN BARRES : Problèmes fréquents
        # Analogie JS : df['col'].value_counts() est comme faire un group-by et compter les occurrences
        fig_bar = px.bar(
            df['probleme_rencontre'].value_counts().reset_index(),
            x='index', 
            y='probleme_rencontre',
            title="Fréquence des problèmes rencontrés",
            labels={'index': 'Type de problème', 'probleme_rencontre': 'Nombre de cas'},
            color_discrete_sequence=['#FF4B4B']
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        # 3. CAMEMBERT : Répartition par transport
        fig_pie = px.pie(
            df, 
            names='type_transport', 
            title="Répartition des moyens de transport",
            hole=0.4 # Pour faire un donut (plus moderne)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.warning("Ajoutez des données via le formulaire pour voir l'analyse descriptive.")

##
# --- SECTION 3 : ROBUSTESSE ET VALIDATION ---

if submit:
    # 1. VALIDATION DES CHAMPS (Analogie : If statements avant un fetch)
    if not nom or len(nom.strip()) < 2:
        st.error("❌ Erreur : Le nom de l'usager est obligatoire (minimum 2 caractères).")
    
    elif satisfaction < 0 or satisfaction > 10:
        st.error("❌ Erreur : La satisfaction doit être comprise entre 0 et 10.")
    
    else:
        # 2. GESTION DES ERREURS AVEC TRY/EXCEPT (Analogie : try/catch)
        conn = None
        try:
            conn = sqlite3.connect('transport_data.db')
            cursor = conn.cursor()
            
            # Utilisation de requêtes paramétrées pour éviter les injections SQL
            query = '''
                INSERT INTO collectes (nom_usager, date_voyage, quartier_origine, type_transport, probleme_rencontre, satisfaction)
                VALUES (?, ?, ?, ?, ?, ?)
            '''
            values = (nom.strip(), str(date_v), quartier, transport, probleme, satisfaction)
            
            cursor.execute(query, values)
            conn.commit()
            
            # 3. FEEDBACK UTILISATEUR (Le 'Toast' message)
            st.toast(f"Données enregistrées pour {nom} !", icon='✅')
            st.balloons() # Optionnel : petit effet visuel pour la "créativité"
            
        except sqlite3.Error as e:
            # En cas d'erreur de DB (fichier verrouillé, corruption, etc.)
            st.error(f"🚨 Erreur de base de données : {e}")
            
        except Exception as e:
            # Capture toutes les autres erreurs imprévues
            st.error(f"🧨 Une erreur inattendue est survenue : {e}")
            
        finally:
            # 4. NETTOYAGE (Analogie : finally en JS)
            if conn:
                conn.close()
                # On force le rafraîchissement pour voir les nouvelles données
                st.rerun()