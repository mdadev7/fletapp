import flet as ft
import sqlite3
from datetime import datetime

# --- SQLite Configuration ---
DB_NAME = "cars.db"

def main(page: ft.Page):
    page.title = "Recherche Véhicules & Propriétaires"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = ft.ScrollMode.ADAPTIVE
    
    # État de l'application
    search_results = []
    selected_item = None
    
    # Fonctions de base de données SQLite
    def connect_to_sqlite():
        try:
            connection = sqlite3.connect(DB_NAME, check_same_thread=False)
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.Error as e:
            print("Erreur de connexion à SQLite:", e)
            return None

    def initialize_db():
        conn = connect_to_sqlite()
        if conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicule (
                    id_vehicule INTEGER PRIMARY KEY AUTOINCREMENT,
                    immatriculation TEXT NOT NULL UNIQUE,
                    marque TEXT NOT NULL,
                    modele TEXT NOT NULL,
                    annee INTEGER,
                    couleur TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proprietaire (
                    id_proprietaire INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_proprietaire TEXT NOT NULL CHECK(type_proprietaire IN ('PHYSIQUE', 'MORALE')),
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
                    id_historique INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_vehicule INTEGER NOT NULL,
                    id_proprietaire INTEGER NOT NULL,
                    date_debut TEXT NOT NULL,
                    date_fin TEXT,
                    FOREIGN KEY (id_vehicule) REFERENCES vehicule(id_vehicule),
                    FOREIGN KEY (id_proprietaire) REFERENCES proprietaire(id_proprietaire)
                )
            ''')
            conn.commit()
            conn.close()
            print("Base de données SQLite initialisée et tables créées (si elles n'existaient pas).")
        else:
            print("Impossible d'initialiser la base de données.")

    initialize_db()

    def show_snackbar(message):
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()
    
    def execute_search(e):
        nonlocal search_results
        query = search_field.value.strip()
        
        # Clear previous state
        search_results.clear()
        results_list.controls.clear()
        details_container.controls.clear()
        details_container.visible = False
        page.update() # Update to clear visible elements

        if not query:
            return
            
        connection = connect_to_sqlite()
        if not connection:
            show_snackbar("Erreur de connexion à la base de données")
            return
            
        try:
            cursor = connection.cursor()
            
            # --- STEP 1: Check for exact vehicle immatriculation match ---
            cursor.execute("SELECT id_vehicule FROM vehicule WHERE UPPER(immatriculation) = UPPER(?)", (query,))
            exact_vehicule_match = cursor.fetchone()

            if exact_vehicule_match:
                # If exact match found, display its details directly
                show_details(('VEHICULE', exact_vehicule_match['id_vehicule'], query)) # Pass type, id, and libelle
                return # Exit function as we've handled the search
            
            # --- STEP 2: If no exact vehicle match, perform combined broad search ---
            param = f'%{query}%'

            cursor.execute(f"""
                SELECT 'VEHICULE' as type, id_vehicule as id, immatriculation as libelle
                FROM vehicule 
                WHERE UPPER(immatriculation) LIKE UPPER(?) 
                   OR UPPER(marque) LIKE UPPER(?) 
                   OR UPPER(modele) LIKE UPPER(?)
                UNION ALL
                SELECT 'PROPRIETAIRE' as type, id_proprietaire as id, 
                       CASE 
                         WHEN type_proprietaire = 'PHYSIQUE' THEN nom || ' ' || prenom
                         ELSE raison_sociale
                       END as libelle
                FROM proprietaire 
                WHERE (type_proprietaire = 'PHYSIQUE' AND (UPPER(nom) LIKE UPPER(?) OR UPPER(prenom) LIKE UPPER(?)))
                   OR (type_proprietaire = 'MORALE' AND UPPER(raison_sociale) LIKE UPPER(?))
                ORDER BY type, libelle
            """, (param, param, param, param, param, param))
            
            search_results = [tuple(row) for row in cursor.fetchall()]
            display_results()
            
        except sqlite3.Error as e:
            print("Erreur de requête:", e)
            show_snackbar("Erreur lors de la recherche")
        finally:
            if connection:
                connection.close()
    
    def display_results():
        results_list.controls.clear()
        
        if not search_results:
            results_list.controls.append(
                ft.ListTile(title=ft.Text("Aucun résultat trouvé"))
            )
        else:
            for item in search_results:
                icon = ft.Icons.DIRECTIONS_CAR if item[0] == 'VEHICULE' else ft.Icons.PERSON
                results_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(icon),
                        title=ft.Text(item[2]),
                        subtitle=ft.Text(f"Type: {item[0]}"),
                        on_click=lambda e, item=item: show_details(item)
                    )
                )
        
        # Keep details container hidden until an item is selected, or if results are displayed
        if search_results: # Only show list if there are actual results to display
            details_container.visible = False
        else: # If no results, hide both
            details_container.visible = False

        page.update()
    
    def show_details(item):
        nonlocal selected_item
        selected_item = item
        details_container.controls.clear()
        details_container.visible = True
        
        connection = connect_to_sqlite()
        if not connection:
            show_snackbar("Erreur de connexion à la base de données")
            return
            
        try:
            cursor = connection.cursor()
            
            if item[0] == 'VEHICULE':
                # Use a specific, more prominent title for direct vehicle details
                details_container.controls.append(
                    ft.Text(f"Détails du Véhicule: {item[2]}", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
                )
                show_vehicle_details(cursor, item[1])
            elif item[0] == 'PROPRIETAIRE':
                details_container.controls.append(
                    ft.Text(f"Détails du Propriétaire: {item[2]}", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
                )
                show_owner_details(cursor, item[1])
            
        except sqlite3.Error as e:
            print("Erreur de requête:", e)
            show_snackbar("Erreur lors du chargement des détails")
        finally:
            if connection:
                connection.close()
        
        page.update()
    
    def show_vehicle_details(cursor, vehicle_id):
        cursor.execute("""
            SELECT v.*, 
                   CASE 
                     WHEN p.type_proprietaire = 'PHYSIQUE' THEN p.nom || ' ' || p.prenom
                     ELSE p.raison_sociale
                   END as proprietaire_actuel,
                   hp.date_debut
            FROM vehicule v
            LEFT JOIN historique_proprietaires hp ON v.id_vehicule = hp.id_vehicule
            LEFT JOIN proprietaire p ON hp.id_proprietaire = p.id_proprietaire
            WHERE v.id_vehicule = ?
            AND (hp.date_fin IS NULL OR hp.date_fin > CURRENT_DATE)
            ORDER BY hp.date_debut DESC LIMIT 1
        """, (vehicle_id,))
        vehicule = cursor.fetchone()
        
        if vehicule:
            # Removed the generic "Détails du Véhicule" title here as it's added in show_details now
            details = [
                ("Immatriculation", vehicule["immatriculation"]),
                ("Marque", vehicule["marque"]),
                ("Modèle", vehicule["modele"]),
                ("Année", vehicule["annee"]),
                ("Couleur", vehicule["couleur"]),
                ("Propriétaire actuel", vehicule["proprietaire_actuel"] or "N/A"),
                ("Depuis le", datetime.strptime(vehicule["date_debut"], '%Y-%m-%d').strftime("%d/%m/%Y") if vehicule["date_debut"] else "N/A")
            ]
            
            for label, value in details:
                details_container.controls.append(
                    ft.Text(f"{label}: {value}", size=16)
                )
            
            cursor.execute("""
                SELECT 
                    CASE 
                      WHEN p.type_proprietaire = 'PHYSIQUE' THEN p.nom || ' ' || p.prenom
                      ELSE p.raison_sociale
                    END as nom_proprietaire,
                    p.type_proprietaire,
                    hp.date_debut, hp.date_fin
                FROM historique_proprietaires hp
                JOIN proprietaire p ON hp.id_proprietaire = p.id_proprietaire
                WHERE hp.id_vehicule = ?
                ORDER BY hp.date_debut DESC
            """, (vehicle_id,))
            historiques = cursor.fetchall()
            
            if historiques:
                details_container.controls.append(
                    ft.Text("\nHistorique des Propriétaires:", size=18, weight=ft.FontWeight.BOLD)
                )
                
                for hist in historiques:
                    date_fin_str = hist["date_fin"]
                    date_debut_str = hist["date_debut"]

                    date_fin_formatted = datetime.strptime(date_fin_str, '%Y-%m-%d').strftime("%d/%m/%Y") if date_fin_str else "Présent"
                    date_debut_formatted = datetime.strptime(date_debut_str, '%Y-%m-%d').strftime("%d/%m/%Y") if date_debut_str else "N/A"
                    
                    type_owner = " (Personne morale)" if hist["type_proprietaire"] == "MORALE" else ""
                    details_container.controls.append(
                        ft.Text(
                            f"{hist['nom_proprietaire']}{type_owner} - Du {date_debut_formatted} au {date_fin_formatted}",
                            size=14
                        )
                    )
    
    def show_owner_details(cursor, owner_id):
        cursor.execute("""
            SELECT * FROM proprietaire WHERE id_proprietaire = ?
        """, (owner_id,))
        proprietaire = cursor.fetchone()
        
        if not proprietaire:
            return
            
        # Removed the generic "Détails du Propriétaire" title here
        
        owner_type = "Personne morale" if proprietaire["type_proprietaire"] == "MORALE" else "Personne physique"
        details_container.controls.append(
            ft.Text(f"Type: {owner_type}", size=16, color=ft.Colors.BLUE)
        )
        
        common_details = [
            ("Adresse", proprietaire["adresse"]),
            ("Téléphone", proprietaire["telephone"]),
            ("Email", proprietaire["email"])
        ]
        
        if proprietaire["type_proprietaire"] == "PHYSIQUE":
            specific_details = [
                ("Nom", proprietaire["nom"]),
                ("Prénom", proprietaire["prenom"]),
                ("Date de naissance", datetime.strptime(proprietaire["date_naissance"], '%Y-%m-%d').strftime("%d/%m/%Y") if proprietaire["date_naissance"] else "N/A")
            ]
        else:
            specific_details = [
                ("Raison sociale", proprietaire["raison_sociale"]),
                ("SIRET", proprietaire["siret"]),
                ("Représentant légal", proprietaire["representant_legal"])
            ]
        
        for label, value in common_details + specific_details:
            if value:
                details_container.controls.append(
                    ft.Text(f"{label}: {value}", size=16)
                )
        
        cursor.execute("""
            SELECT v.immatriculation, v.marque, v.modele,
                   hp.date_debut, hp.date_fin
            FROM historique_proprietaires hp
            JOIN vehicule v ON hp.id_vehicule = v.id_vehicule
            WHERE hp.id_proprietaire = ?
            ORDER BY hp.date_debut DESC
        """, (owner_id,))
        vehicules = cursor.fetchall()
        
        if vehicules:
            details_container.controls.append(
                ft.Text("\nVéhicules associés:", size=18, weight=ft.FontWeight.BOLD)
            )
            
            for veh in vehicules:
                date_fin_str = veh["date_fin"]
                date_debut_str = veh["date_debut"]

                date_fin_formatted = datetime.strptime(date_fin_str, '%Y-%m-%d').strftime("%d/%m/%Y") if date_fin_str else "Présent"
                date_debut_formatted = datetime.strptime(date_debut_str, '%Y-%m-%d').strftime("%d/%m/%Y") if date_debut_str else "N/A"

                details_container.controls.append(
                    ft.Text(
                        f"{veh['immatriculation']} - {veh['marque']} {veh['modele']} (Du {date_debut_formatted} au {date_fin_formatted})",
                        size=14
                    )
                )
    
    # Widgets principaux
    search_field = ft.TextField(
        label="Rechercher par immatriculation, marque, modèle ou nom du propriétaire...",
        autofocus=True,
        expand=True,
        on_submit=execute_search,
        prefix_icon=ft.Icons.SEARCH
    )
    
    search_button = ft.ElevatedButton(
        text="Rechercher",
        icon=ft.Icons.SEARCH,
        on_click=execute_search
    )

    results_list = ft.ListView(
        expand=1,
        spacing=10,
        padding=ft.padding.only(top=10)
    )

    details_container = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=2,
        visible=False,
        #border=ft.border.all(1, ft.Colors.GREY_300),
        #border_radius=10,
        #padding=15,
        spacing=10
    )
    
    # Disposition de la page
    page.add(
        ft.Column([
            ft.Row([
                search_field,
                search_button
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Column([
                    ft.Text("Résultats de recherche", size=18, weight=ft.FontWeight.BOLD),
                    results_list
                ], expand=1),
                details_container
            ], expand=True, spacing=20)
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)