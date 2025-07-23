import flet as ft
import sqlite3
import os

# --- Configuration de la base de données (DOIT CORRESPONDRE À VOTRE DB FLET) ---
DB_FILE = 'dossiers.db' # Assurez-vous que c'est le même fichier que votre app principale

# Connexion à la base de données SQLite
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row # Permet d'accéder aux colonnes par leur nom
    return conn

# --- Fonction pour initialiser les tables originales (pour les tests) ---
def setup_initial_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicule (
            id_vehicule INTEGER PRIMARY KEY,
            immatriculation TEXT UNIQUE NOT NULL,
            marque TEXT NOT NULL,
            modele TEXT NOT NULL,
            annee_fabrication INTEGER,
            couleur TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proprietaire (
            id_proprietaire INTEGER PRIMARY KEY,
            type_proprietaire TEXT NOT NULL CHECK (type_proprietaire IN ('PHYSIQUE', 'MORALE')),
            adresse TEXT,
            telephone TEXT,
            email TEXT,
            nom TEXT,
            prenom TEXT,
            date_naissance TEXT,
            raison_sociale TEXT,
            siret TEXT,
            representant_legal TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historique_proprietaires (
            id_historique INTEGER PRIMARY KEY,
            id_vehicule INTEGER REFERENCES vehicule(id_vehicule),
            id_proprietaire INTEGER REFERENCES proprietaire(id_proprietaire),
            date_debut TEXT NOT NULL,
            date_fin TEXT,
            CONSTRAINT check_dates CHECK (date_fin IS NULL OR date_fin > date_debut)
        )
    ''')

    # Insérer des données d'exemple si les tables sont vides
    cursor.execute("SELECT COUNT(*) FROM vehicule")
    if cursor.fetchone()[0] == 0:
        print("Inserting sample data...")
        cursor.execute("INSERT INTO vehicule (id_vehicule, immatriculation, marque, modele, annee_fabrication, couleur) VALUES (1, 'AB-123-CD', 'Renault', 'Clio', 2020, 'Bleu')")
        cursor.execute("INSERT INTO vehicule (id_vehicule, immatriculation, marque, modele, annee_fabrication, couleur) VALUES (2, 'EF-456-GH', 'Peugeot', '308', 2018, 'Gris')")
        
        cursor.execute("INSERT INTO proprietaire (id_proprietaire, type_proprietaire, nom, prenom, adresse) VALUES (101, 'PHYSIQUE', 'Dupont', 'Jean', '12 Rue de la Paix')")
        cursor.execute("INSERT INTO proprietaire (id_proprietaire, type_proprietaire, raison_sociale, siret, adresse) VALUES (102, 'MORALE', 'ABC Corp', '12345678901234', 'Z.I. Sud')")

        cursor.execute("INSERT INTO historique_proprietaires (id_historique, id_vehicule, id_proprietaire, date_debut, date_fin) VALUES (1001, 1, 101, '2020-05-10', '2023-01-15')")
        cursor.execute("INSERT INTO historique_proprietaires (id_historique, id_vehicule, id_proprietaire, date_debut, date_fin) VALUES (1002, 1, 102, '2023-01-16', NULL)")
        cursor.execute("INSERT INTO historique_proprietaires (id_historique, id_vehicule, id_proprietaire, date_debut, date_fin) VALUES (1003, 2, 101, '2019-03-20', NULL)")
        conn.commit()
    
    conn.close()

# --- Fonction principale pour l'archivage ---
def archive_data_to_single_table(page: ft.Page):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Supprimer la table d'archive existante si elle existe (pour un nettoyage facile)
        print("Dropping existing main_archive table...")
        cursor.execute("DROP TABLE IF EXISTS main_archive;")

        # 2. Créer la nouvelle table main_archive
        print("Creating main_archive table...")
        cursor.execute('''
            CREATE TABLE main_archive (
                id_historique INTEGER PRIMARY KEY,
                id_vehicule_orig INTEGER NOT NULL,
                id_proprietaire_orig INTEGER NOT NULL,
                date_debut TEXT NOT NULL,
                date_fin TEXT,
                
                immatriculation_veh TEXT NOT NULL,
                marque_veh TEXT NOT NULL,
                modele_veh TEXT NOT NULL,
                annee_fabrication_veh INTEGER,
                couleur_veh TEXT,
                
                type_proprietaire_prop TEXT NOT NULL,
                adresse_prop TEXT,
                telephone_prop TEXT,
                email_prop TEXT,
                nom_prop TEXT,
                prenom_prop TEXT,
                date_naissance_prop TEXT,
                raison_sociale_prop TEXT,
                siret_prop TEXT,
                representant_legal_prop TEXT
            );
        ''')

        # 3. Insérer les données en joignant les trois tables
        print("Inserting data into main_archive...")
        cursor.execute('''
            INSERT INTO main_archive (
                id_historique, id_vehicule_orig, id_proprietaire_orig, date_debut, date_fin,
                immatriculation_veh, marque_veh, modele_veh, annee_fabrication_veh, couleur_veh,
                type_proprietaire_prop, adresse_prop, telephone_prop, email_prop,
                nom_prop, prenom_prop, date_naissance_prop,
                raison_sociale_prop, siret_prop, representant_legal_prop
            )
            SELECT
                hp.id_historique, hp.id_vehicule, hp.id_proprietaire, hp.date_debut, hp.date_fin,
                v.immatriculation, v.marque, v.modele, v.annee_fabrication, v.couleur,
                p.type_proprietaire, p.adresse, p.telephone, p.email,
                p.nom, p.prenom, p.date_naissance,
                p.raison_sociale, p.siret, p.representant_legal
            FROM
                historique_proprietaires hp
            JOIN
                vehicule v ON hp.id_vehicule = v.id_vehicule
            JOIN
                proprietaire p ON hp.id_proprietaire = p.id_proprietaire;
        ''')

        conn.commit()
        print("Data archived successfully.")
        page.snack_bar = ft.SnackBar(
            ft.Text("Données archivées dans main_archive avec succès!", color=ft.colors.WHITE),
            bgcolor=ft.colors.GREEN_700
        )
        page.snack_bar.open = True

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback() # Annuler les changements en cas d'erreur
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Erreur d'archivage des données: {e}", color=ft.colors.WHITE),
            bgcolor=ft.colors.RED_700
        )
        page.snack_bar.open = True
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Erreur inattendue: {e}", color=ft.colors.WHITE),
            bgcolor=ft.colors.RED_700
        )
        page.snack_bar.open = True
    finally:
        if conn:
            conn.close()
    page.update()

# --- Fonction Flet principale ---
def main(page: ft.Page):
    page.title = "Application d'Archivage de Données"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Assurez-vous que les tables originales existent et ont des données pour le test
    setup_initial_tables()

    page.add(
        ft.Text("Cliquez sur le bouton pour archiver les données dans une seule table."),
        ft.ElevatedButton(
            "Archiver toutes les données",
            icon=ft.icons.ARCHIVE,
            on_click=lambda e: archive_data_to_single_table(page)
        ),
        ft.Text("Vérifiez votre base de données 'dossiers.db' pour la table 'main_archive'.")
    )

ft.app(target=main)