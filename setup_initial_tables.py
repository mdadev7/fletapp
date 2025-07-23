import sqlite3
import os

# --- Configuration de la base de données ---
DB_FILE = 'dossiers.db' # Assurez-vous que c'est le même fichier que votre app Flet

def insert_example_data():
    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"Connected to database: {DB_FILE}")

        # 1. Create tables if they don't exist
        # Table vehicule
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
        print("Table 'vehicule' checked/created.")

        # Table proprietaire
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
        print("Table 'proprietaire' checked/created.")

        # Table HistoriqueProprietaires
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
        print("Table 'historique_proprietaires' checked/created.")

        # 2. Insert sample data if tables are empty
        # This prevents inserting duplicates if you run the script multiple times
        cursor.execute("SELECT COUNT(*) FROM vehicule")
        if cursor.fetchone()[0] == 0:
            print("\nInserting sample data into tables...")

            # --- Sample Data for vehicule ---
            cursor.execute("INSERT INTO vehicule (id_vehicule, immatriculation, marque, modele, annee_fabrication, couleur) VALUES (?, ?, ?, ?, ?, ?)",
                           (1, 'AB-123-CD', 'Renault', 'Clio', 2020, 'Bleu'))
            print("  - Inserted Vehicle 1: Renault Clio (ID: 1)")

            cursor.execute("INSERT INTO vehicule (id_vehicule, immatriculation, marque, modele, annee_fabrication, couleur) VALUES (?, ?, ?, ?, ?, ?)",
                           (2, 'EF-456-GH', 'Peugeot', '308', 2018, 'Gris'))
            print("  - Inserted Vehicle 2: Peugeot 308 (ID: 2)")
            
            cursor.execute("INSERT INTO vehicule (id_vehicule, immatriculation, marque, modele, annee_fabrication, couleur) VALUES (?, ?, ?, ?, ?, ?)",
                           (3, 'IJ-789-KL', 'Volkswagen', 'Golf', 2022, 'Noir'))
            print("  - Inserted Vehicle 3: Volkswagen Golf (ID: 3)")

            # --- Sample Data for proprietaire ---
            cursor.execute("INSERT INTO proprietaire (id_proprietaire, type_proprietaire, nom, prenom, adresse, email) VALUES (?, ?, ?, ?, ?, ?)",
                           (101, 'PHYSIQUE', 'Dupont', 'Jean', '12 Rue de la Paix, Paris', 'jean.dupont@example.com'))
            print("  - Inserted Owner 1: Jean Dupont (ID: 101, type: PHYSIQUE)")

            cursor.execute("INSERT INTO proprietaire (id_proprietaire, type_proprietaire, raison_sociale, siret, adresse) VALUES (?, ?, ?, ?, ?)",
                           (102, 'MORALE', 'ABC Corp', '12345678901234', 'ZI Sud, Marseille'))
            print("  - Inserted Owner 2: ABC Corp (ID: 102, type: MORALE)")
            
            cursor.execute("INSERT INTO proprietaire (id_proprietaire, type_proprietaire, nom, prenom, adresse) VALUES (?, ?, ?, ?, ?)",
                           (103, 'PHYSIQUE', 'Martin', 'Sophie', '25 Avenue des Champs, Lyon'))
            print("  - Inserted Owner 3: Sophie Martin (ID: 103, type: PHYSIQUE)")

            # --- Sample Data for historique_proprietaires ---
            cursor.execute("INSERT INTO historique_proprietaires (id_historique, id_vehicule, id_proprietaire, date_debut, date_fin) VALUES (?, ?, ?, ?, ?)",
                           (1001, 1, 101, '2020-05-10', '2023-01-15'))
            print("  - Inserted History 1: Vehicle 1 (Renault Clio) owned by Jean Dupont")

            cursor.execute("INSERT INTO historique_proprietaires (id_historique, id_vehicule, id_proprietaire, date_debut) VALUES (?, ?, ?, ?)",
                           (1002, 1, 102, '2023-01-16')) # Current owner
            print("  - Inserted History 2: Vehicle 1 (Renault Clio) currently owned by ABC Corp")

            cursor.execute("INSERT INTO historique_proprietaires (id_historique, id_vehicule, id_proprietaire, date_debut, date_fin) VALUES (?, ?, ?, ?, ?)",
                           (1003, 2, 101, '2019-03-20', '2024-06-01'))
            print("  - Inserted History 3: Vehicle 2 (Peugeot 308) owned by Jean Dupont")
                           
            cursor.execute("INSERT INTO historique_proprietaires (id_historique, id_vehicule, id_proprietaire, date_debut) VALUES (?, ?, ?, ?)",
                           (1004, 2, 103, '2024-06-02')) # Current owner
            print("  - Inserted History 4: Vehicle 2 (Peugeot 308) currently owned by Sophie Martin")
                           
            cursor.execute("INSERT INTO historique_proprietaires (id_historique, id_vehicule, id_proprietaire, date_debut) VALUES (?, ?, ?, ?)",
                           (1005, 3, 103, '2022-10-01')) # Current owner
            print("  - Inserted History 5: Vehicle 3 (VW Golf) currently owned by Sophie Martin")

            conn.commit()
            print("\nAll sample data inserted successfully!")
        else:
            print("Tables already contain data. Skipping sample data insertion.")

    except sqlite3.Error as e:
        print(f"An SQLite error occurred: {e}")
        if conn:
            conn.rollback() # Rollback changes if an error occurred
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    insert_example_data()