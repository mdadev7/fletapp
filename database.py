import sqlite3
import os

DATABASE_NAME = 'dossiers.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par leur nom
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dossiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            date TEXT NOT NULL,
            personne TEXT NOT NULL,
            objet TEXT NOT NULL,
            numero_reference TEXT,
            date_debut TEXT,
            date_fin TEXT,
            observation TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vérifier si la table est vide pour ne pas insérer plusieurs fois
    cursor.execute("SELECT COUNT(*) FROM dossiers")
    if cursor.fetchone()[0] == 0:
        dossiers_data = [
            ("D001", "2023-01-15", "Jean Dupont", "Demande d'information", "REF001", "2023-01-10", "2023-01-20", "Dossier traité."),
            ("D002", "2023-02-20", "Marie Curie", "Réclamation produit", "REF002", "2023-02-15", "2023-02-25", "En attente de réponse."),
            ("D003", "2023-03-10", "Pierre Dubois", "Suivi de commande", None, "2023-03-05", "2023-03-15", "Commande expédiée."),
            ("D004", "2023-04-01", "Sophie Martin", "Demande de devis", "REF003", "2023-03-28", "2023-04-05", "Devis envoyé."),
            ("D005", "2023-05-05", "Jean Dupont", "Nouveau projet X", "PROJX", "2023-05-01", "2023-05-30", "Réunion planifiée."),
            ("D006", "2023-06-12", "Alice Smith", "Mise à jour coordonnées", None, "2023-06-10", "2023-06-15", "Coordonnées mises à jour."),
            ("D007", "2023-07-01", "Bob Johnson", "Incident technique", "INC001", "2023-06-25", "2023-07-05", "En cours de résolution."),
            ("D008", "2023-08-18", "Marie Curie", "Question sur facture", "FAC005", "2023-08-10", "2023-08-20", "Facture clarifiée."),
            ("D009", "2023-09-22", "Pierre Dubois", "Validation document", "DOC010", "2023-09-15", "2023-09-25", "Document validé."),
            ("D010", "2023-10-30", "Sophie Martin", "Feedback produit Y", "PRDY", "2023-10-25", "2023-11-05", "Feedback enregistré."),
            ("D011", "2023-11-11", "Alice Smith", "Demande de support", "SUP007", "2023-11-08", "2023-11-15", "Ticket ouvert."),
            ("D012", "2023-12-05", "Bob Johnson", "Proposition commerciale", "PROP003", "2023-12-01", "2023-12-10", "En attente de réponse."),
            ("D013", "2024-01-20", "Jean Dupont", "Renouvellement contrat", "CONTR12", "2024-01-15", "2024-01-25", "Contrat en cours de signature."),
            ("D014", "2024-02-14", "Marie Curie", "Mise à jour données", None, "2024-02-10", "2024-02-20", "Données actualisées."),
            ("D015", "2024-03-25", "Pierre Dubois", "Projet Z finalisation", "PROJZ", "2024-03-20", "2024-03-30", "Projet terminé."),
        ]
        cursor.executemany('''
            INSERT INTO dossiers (numero, date, personne, objet, numero_reference, date_debut, date_fin, observation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', dossiers_data)
        conn.commit()
    conn.close()

def search_dossiers(query, page=1, page_size=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    offset = (page - 1) * page_size

    # Construction de la clause WHERE pour la recherche
    search_term = f'%{query}%'
    sql_where_clause = '''
        WHERE numero LIKE ? OR date LIKE ? OR personne LIKE ? OR objet LIKE ? OR numero_reference LIKE ? OR date_debut LIKE ? OR date_fin LIKE ? OR observation LIKE ?
    '''

    # Requête pour les résultats paginés
    cursor.execute(f'''
        SELECT * FROM dossiers
        {sql_where_clause}
        ORDER BY date DESC
        LIMIT ? OFFSET ?
    ''', (search_term, search_term, search_term, search_term, search_term, search_term, search_term, search_term, page_size, offset))
    results = cursor.fetchall()

    # Requête pour le nombre total de résultats (pour la pagination)
    cursor.execute(f'''
        SELECT COUNT(*) FROM dossiers
        {sql_where_clause}
    ''', (search_term, search_term, search_term, search_term, search_term, search_term, search_term, search_term))
    total_results = cursor.fetchone()[0]

    conn.close()
    return results, total_results

if __name__ == "__main__":
    create_table()
    insert_sample_data()
    print("Base de données 'dossiers.db' créée et remplie avec des données d'exemple.")
    # Test de recherche
    # results, total = search_dossiers("Jean", page=1, page_size=5)
    # for r in results:
    #     print(dict(r))
    # print(f"Total results: {total}")