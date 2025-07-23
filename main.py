import flet as ft
import oracledb as cx_Oracle
from datetime import datetime

# Configuration de la connexion Oracle
ORACLE_USER = "user_dev"
ORACLE_PASSWORD = "user_dev"
ORACLE_DSN = "localhost:1522/XEPDB1"

def main(page: ft.Page):
    page.title = "Consultation Véhicules & Propriétaires"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # État de l'application
    search_results = []
    selected_item = None
    
    # Fonctions
    def connect_to_oracle():
        try:
            connection = cx_Oracle.connect(
                user=ORACLE_USER,
                password=ORACLE_PASSWORD,
                dsn=ORACLE_DSN
            )
            return connection
        except cx_Oracle.DatabaseError as e:
            print("Erreur de connexion à Oracle:", e)
            return None
    
    def show_snackbar(message):
        page.snack_bar = ft.SnackBar(ft.Text(message))
        page.snack_bar.open = True
        page.update()
    
    def execute_search(e):
        nonlocal search_results
        query = search_field.value.strip()
        
        if not query:
            return
            
        connection = connect_to_oracle()
        if not connection:
            show_snackbar("Erreur de connexion à la base de données")
            return
            
        try:
            cursor = connection.cursor()
            
            # Recherche dans les véhicules
            cursor.execute("""
                SELECT 'VEHICULE' as type, id_vehicule as id, immatriculation as libelle
                FROM vehicule 
                WHERE UPPER(immatriculation) LIKE UPPER(:query) 
                   OR UPPER(marque) LIKE UPPER(:query) 
                   OR UPPER(modele) LIKE UPPER(:query)
            """, {'query': f'%{query}%'})
            vehicules = cursor.fetchall()
            
            # Recherche dans les propriétaires
            cursor.execute("""
                SELECT 'PROPRIETAIRE' as type, id_proprietaire as id, 
                       CASE 
                         WHEN type_proprietaire = 'PHYSIQUE' THEN nom || ' ' || prenom
                         ELSE raison_sociale
                       END as libelle
                FROM proprietaire 
                WHERE (type_proprietaire = 'PHYSIQUE' AND (UPPER(nom) LIKE UPPER(:query) OR UPPER(prenom) LIKE UPPER(:query)))
                   OR (type_proprietaire = 'MORALE' AND UPPER(raison_sociale) LIKE UPPER(:query))
            """, {'query': f'%{query}%'})
            proprietaires = cursor.fetchall()
            
            search_results = vehicules + proprietaires
            display_results()
            
        except cx_Oracle.DatabaseError as e:
            print("Erreur de requête:", e)
            show_snackbar("Erreur lors de la recherche")
        finally:
            cursor.close()
            connection.close()
    
    def display_results():
        results_list.controls.clear()
        
        if not search_results:
            results_list.controls.append(
                ft.ListTile(title=ft.Text("Aucun résultat trouvé"))
            )
        else:
            for item in search_results:
                results_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(item[2]),
                        subtitle=ft.Text(item[0]),
                        on_click=lambda e, item=item: show_details(item)
                    )
                )
        
        details_container.visible = False
        page.update()
    
    def show_details(item):
        nonlocal selected_item
        selected_item = item
        details_container.controls.clear()
        details_container.visible = True
        
        connection = connect_to_oracle()
        if not connection:
            show_snackbar("Erreur de connexion à la base de données")
            return
            
        try:
            cursor = connection.cursor()
            
            if item[0] == 'VEHICULE':
                show_vehicle_details(cursor, item[1])
            elif item[0] == 'PROPRIETAIRE':
                show_owner_details(cursor, item[1])
            
        except cx_Oracle.DatabaseError as e:
            print("Erreur de requête:", e)
            show_snackbar("Erreur lors du chargement des détails")
        finally:
            cursor.close()
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
            WHERE v.id_vehicule = :id
            AND (hp.date_fin IS NULL OR hp.date_fin > SYSDATE)
        """, {'id': vehicle_id})
        vehicule = cursor.fetchone()
        
        if vehicule:
            details_container.controls.append(
                ft.Text("Détails du Véhicule", size=20, weight=ft.FontWeight.BOLD)
            )
            
            details = [
                ("Immatriculation", vehicule[1]),
                ("Marque", vehicule[2]),
                ("Modèle", vehicule[3]),
                ("Année", vehicule[4]),
                ("Couleur", vehicule[5]),
                ("Propriétaire actuel", vehicule[6]),
                ("Depuis le", vehicule[7].strftime("%d/%m/%Y") if vehicule[7] else "N/A")
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
                WHERE hp.id_vehicule = :id
                ORDER BY hp.date_debut DESC
            """, {'id': vehicle_id})
            historiques = cursor.fetchall()
            
            if historiques:
                details_container.controls.append(
                    ft.Text("\nHistorique des Propriétaires:", size=18, weight=ft.FontWeight.BOLD)
                )
                
                for hist in historiques:
                    date_fin = hist[3].strftime("%d/%m/%Y") if hist[3] else "Présent"
                    type_owner = " (Personne morale)" if hist[1] == "MORALE" else ""
                    details_container.controls.append(
                        ft.Text(
                            f"{hist[0]}{type_owner} - Du {hist[2].strftime('%d/%m/%Y')} au {date_fin}",
                            size=14
                        )
                    )
    
    def show_owner_details(cursor, owner_id):
        cursor.execute("""
            SELECT * FROM proprietaire WHERE id_proprietaire = :id
        """, {'id': owner_id})
        proprietaire = cursor.fetchone()
        
        if not proprietaire:
            return
            
        details_container.controls.append(
            ft.Text("Détails du Propriétaire", size=20, weight=ft.FontWeight.BOLD)
        )
        
        owner_type = "Personne morale" if proprietaire[1] == "MORALE" else "Personne physique"
        details_container.controls.append(
            ft.Text(f"Type: {owner_type}", size=16, color=ft.Colors.BLUE)
        )
        
        common_details = [
            ("Adresse", proprietaire[2]),
            ("Téléphone", proprietaire[3]),
            ("Email", proprietaire[4])
        ]
        
        if proprietaire[1] == "PHYSIQUE":
            specific_details = [
                ("Nom", proprietaire[5]),
                ("Prénom", proprietaire[6]),
                ("Date de naissance", proprietaire[7].strftime("%d/%m/%Y") if proprietaire[7] else "N/A")
            ]
        else:
            specific_details = [
                ("Raison sociale", proprietaire[8]),
                ("SIRET", proprietaire[9]),
                ("Représentant légal", proprietaire[10])
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
            WHERE hp.id_proprietaire = :id
            ORDER BY hp.date_debut DESC
        """, {'id': owner_id})
        vehicules = cursor.fetchall()
        
        if vehicules:
            details_container.controls.append(
                ft.Text("\nVéhicules associés:", size=18, weight=ft.FontWeight.BOLD)
            )
            
            for veh in vehicules:
                date_fin = veh[4].strftime("%d/%m/%Y") if veh[4] else "Présent"
                details_container.controls.append(
                    ft.Text(
                        f"{veh[0]} - {veh[1]} {veh[2]} (Du {veh[3].strftime('%d/%m/%Y')} au {date_fin})",
                        size=14
                    )
                )
    
    # Widgets principaux (définis APRÈS les fonctions qu'ils utilisent)
    search_field = ft.TextField(
        label="Rechercher un véhicule ou propriétaire...",
        autofocus=True,
        on_submit=execute_search  # Maintenant la fonction est définie
    )
    
    results_list = ft.ListView(expand=True)
    details_container = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        visible=False
    )
    
    # Disposition de la page
    page.add(
        ft.Column([
            ft.Row([
                search_field,
                ft.IconButton(icon=ft.Icons.SEARCH, on_click=execute_search)
            ]),
            ft.Row([
                ft.Container(results_list, width=400),
                ft.Container(details_container, width=400, padding=10)
            ], spacing=20)
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)