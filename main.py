import flet as ft
import sqlite3
from datetime import datetime

def main(page: ft.Page):
    # Configuration de la page
    page.title = "Gestion des Dossiers"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.window_min_width = 800
    page.window_min_height = 600

    # Connexion à la base de données avec gestion de contexte
    # Utilisez check_same_thread=False si vous exécutez Flet en mode "web" ou avec plusieurs threads.
    # Pour une application de bureau simple, vous pourriez l'omettre, mais c'est une bonne pratique avec Flet.
    conn = sqlite3.connect('dossiers.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Création de la table avec schéma amélioré
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

    # Variables pour la pagination et recherche
    current_page = 1
    items_per_page = 10  # Augmenté pour meilleure UX
    total_items = 0
    current_search_query = ""

    # Styles réutilisables
    card_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=10)
    )
    text_style = ft.TextStyle(
        size=12,
        color=ft.Colors.GREY_800
    )
    title_style = ft.TextStyle(
        size=14,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_800
    )

    # Composants UI améliorés
    search_field = ft.TextField(
        label="Rechercher par numéro, personne ou objet...",
        prefix_icon=ft.Icons.SEARCH,
        expand=True,
        on_submit=lambda e: search_dossiers(),
        border_radius=10,
        filled=True,
        hint_text="Entrez des mots-clés...",
        text_size=14
    )

    # Boutons avec style cohérent
    button_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=10
    )

    search_button = ft.ElevatedButton(
        "Rechercher",
        icon=ft.Icons.SEARCH,
        on_click=lambda e: search_dossiers(),
        style=button_style
    )

    add_button = ft.ElevatedButton(
        "Ajouter un dossier",
        icon=ft.Icons.ADD,
        on_click=lambda e: open_edit_dialog(None), # Appelle la boîte de dialogue sans dossier pour l'ajout
        style=button_style
    )

    # Conteneurs avec style
    results_container = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
        auto_scroll=False
    )

    pagination_controls = ft.Row(
        [],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=5
    )

    # --- Fonctions CRUD améliorées ---

    def load_dossiers():
        nonlocal total_items, current_search_query
        
        # Si une recherche est en cours, recharge les résultats de la recherche au lieu de tous les dossiers
        if current_search_query:
            search_dossiers()
            return
            
        cursor.execute("SELECT COUNT(*) FROM dossiers")
        total_items = cursor.fetchone()[0]
        
        offset = (current_page - 1) * items_per_page
        cursor.execute(
            "SELECT id, numero, date, personne, objet, numero_reference, date_debut, date_fin, observation FROM dossiers ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (items_per_page, offset)
        )
        display_results(cursor.fetchall())
        update_pagination()

    def search_dossiers():
        nonlocal total_items, current_search_query
        query = search_field.value.strip()
        current_search_query = query # Met à jour la requête de recherche actuelle
        
        if query:
            sql = """
            SELECT id, numero, date, personne, objet, numero_reference, date_debut, date_fin, observation, COUNT(*) OVER() as total 
            FROM dossiers 
            WHERE numero LIKE ? OR personne LIKE ? OR objet LIKE ? OR numero_reference LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            param = f"%{query}%"
            offset = (current_page - 1) * items_per_page
            cursor.execute(sql, (param, param, param, param, items_per_page, offset))
            
            results = cursor.fetchall()
            if results:
                total_items = results[0][-1]  # Récupère le total du COUNT OVER
            else:
                total_items = 0 # Aucun résultat de recherche
            display_results([row[:-1] for row in results])  # Enlève la colonne 'total' pour l'affichage
        else:
            current_search_query = "" # Réinitialise la requête de recherche si vide
            load_dossiers() # Charge tous les dossiers si la recherche est vide
        update_pagination() # Met à jour la pagination pour la recherche

    def display_results(results):
        results_container.controls.clear()
        
        if not results:
            results_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Aucun dossier trouvé",
                        style=ft.TextStyle(size=16, color=ft.Colors.GREY_500)
                    ),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
        else:
            for row in results:
                results_container.controls.append(
                    create_dossier_card(row)
                )
        page.update()

    def create_dossier_card(row):
        # 'row' est un tuple ici, les index correspondent à l'ordre des colonnes dans la table
        # id=row[0], numero=row[1], date=row[2], personne=row[3], objet=row[4],
        # numero_reference=row[5], date_debut=row[6], date_fin=row[7], observation=row[8]
        return ft.Card(
            elevation=5,
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.BLUE_500),
                        title=ft.Text(
                            f"Dossier {row[1]}", # Affiche le numéro du dossier
                            style=title_style
                        ),
                        subtitle=ft.Text(
                            f"Par {row[3]} - {row[4]}", # Affiche personne et objet
                            style=text_style
                        ),
                        trailing=ft.PopupMenuButton(
                            icon=ft.Icons.MORE_VERT,
                            items=[
                                ft.PopupMenuItem(
                                    text="Modifier",
                                    icon=ft.Icons.EDIT,
                                    on_click=lambda e, r=row: open_edit_dialog(r) # Passe l'objet dossier complet
                                ),
                                ft.PopupMenuItem(
                                    text="Supprimer",
                                    icon=ft.Icons.DELETE,
                                    on_click=lambda e, dossier_id=row[0]: delete_dossier(dossier_id) # Passe seulement l'ID
                                ),
                            ]
                        )
                    ),
                    ft.ExpansionTile(
                        title=ft.Text("Détails du dossier"),
                        controls=[
                            ft.ListTile(
                                title=ft.Text("Date"),
                                subtitle=ft.Text(row[2]),
                            ),
                            ft.ListTile(
                                title=ft.Text("Référence"),
                                subtitle=ft.Text(row[5] or "Non spécifié"),
                            ),
                            ft.ListTile(
                                title=ft.Text("Période"),
                                subtitle=ft.Text(
                                    f"{row[6] or 'Non spécifié'} au {row[7] or 'Non spécifié'}"
                                ),
                            ),
                            ft.ListTile(
                                title=ft.Text("Observation"),
                                subtitle=ft.Text(row[8] or "Aucune observation"),
                            )
                        ]
                    )
                ]),
                padding=10,
                border_radius=10
            ),
            margin=5
        )

    def open_edit_dialog(dossier):
        # Fonction interne pour sauvegarder les données du dossier
        def save_dossier(e):
            # Validation des champs obligatoires
            if not numero_field.value or not date_field.value or not personne_field.value or not objet_field.value:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Veuillez remplir tous les champs obligatoires (*)"),
                    action="OK",
                    bgcolor=ft.Colors.RED_700
                )
                page.snack_bar.open = True
                page.update()
                return
            
            # Validation simple du format de date (peut être amélioré)
            try:
                if date_field.value: datetime.strptime(date_field.value, '%Y-%m-%d')
                if debut_field.value: datetime.strptime(debut_field.value, '%Y-%m-%d')
                if fin_field.value: datetime.strptime(fin_field.value, '%Y-%m-%d')
            except ValueError:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Format de date invalide. Utilisez AAAA-MM-JJ."),
                    action="OK",
                    bgcolor=ft.Colors.RED_700
                )
                page.snack_bar.open = True
                page.update()
                return

            # Préparation des données pour l'insertion/mise à jour
            data = (
                numero_field.value,
                date_field.value,
                personne_field.value,
                objet_field.value,
                ref_field.value.strip() if ref_field.value else None, # Utilisez strip() pour éviter les espaces vides
                debut_field.value.strip() if debut_field.value else None,
                fin_field.value.strip() if fin_field.value else None,
                obs_field.value.strip() if obs_field.value else None,
            )
            
            try:
                if dossier:  # Cas de la MODIFICATION
                    # Ajout de l'ID à la fin des données pour la clause WHERE
                    cursor.execute("""
                    UPDATE dossiers SET 
                    numero=?, date=?, personne=?, objet=?, 
                    numero_reference=?, date_debut=?, date_fin=?, observation=?
                    WHERE id=?
                    """, data + (dossier[0],)) # dossier[0] est l'ID du dossier existant
                    message = "Dossier mis à jour avec succès !"
                else:  # Cas de l'AJOUT
                    cursor.execute("""
                    INSERT INTO dossiers (
                        numero, date, personne, objet, 
                        numero_reference, date_debut, date_fin, observation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, data)
                    message = "Nouveau dossier créé avec succès !"
                
                conn.commit() # Valider les changements dans la base de données
                dialog.open = False # Fermer la boîte de dialogue
                page.update() # Mettre à jour la page
                
                # Feedback utilisateur via SnackBar
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(message),
                    action="OK",
                    bgcolor=ft.Colors.GREEN_700 # Couleur verte pour le succès
                )
                page.snack_bar.open = True
                
                load_dossiers() # Recharger les dossiers pour afficher les changements
            except sqlite3.IntegrityError as ex:
                # Gérer les erreurs spécifiques de la base de données, par exemple unicité
                error_msg = f"Erreur de base de données: {str(ex)}"
                if "UNIQUE constraint failed: dossiers.numero" in str(ex):
                     error_msg = "Un dossier avec ce numéro existe déjà."
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(error_msg),
                    action="OK",
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
            except Exception as ex:
                # Gérer les autres erreurs inattendues
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Une erreur est survenue: {str(ex)}"),
                    action="OK",
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
            finally:
                page.update()

        # Champs du formulaire avec pré-remplissage pour l'édition
        # Le 'dossier' est un tuple (id, numero, date, personne, objet, ref, debut, fin, obs, created_at)
        numero_field = ft.TextField(
            label="Numéro*",
            value=dossier[1] if dossier else "",
            text_size=14,
            filled=True,
            border_radius=8,
            autofocus=True # Met le focus sur le premier champ
        )
        
        date_field = ft.TextField(
            label="Date* (AAAA-MM-JJ)",
            value=dossier[2] if dossier else "",
            hint_text="Ex: 2023-01-15",
            text_size=14,
            filled=True,
            border_radius=8
        )
        
        personne_field = ft.TextField(
            label="Personne*",
            value=dossier[3] if dossier else "",
            text_size=14,
            filled=True,
            border_radius=8
        )
        
        objet_field = ft.TextField(
            label="Objet*",
            value=dossier[4] if dossier else "",
            text_size=14,
            filled=True,
            border_radius=8
        )
        
        ref_field = ft.TextField(
            label="Référence (numéro de référence)",
            value=dossier[5] if dossier else "",
            text_size=14,
            filled=True,
            border_radius=8
        )
        
        debut_field = ft.TextField(
            label="Date début (AAAA-MM-JJ)",
            value=dossier[6] if dossier else "",
            hint_text="Ex: 2023-01-01",
            text_size=14,
            filled=True,
            border_radius=8
        )
        
        fin_field = ft.TextField(
            label="Date fin (AAAA-MM-JJ)",
            value=dossier[7] if dossier else "",
            hint_text="Ex: 2023-12-31",
            text_size=14,
            filled=True,
            border_radius=8
        )
        
        obs_field = ft.TextField(
            label="Observation",
            value=dossier[8] if dossier else "",
            multiline=True,
            min_lines=3,
            max_lines=5,
            text_size=14,
            filled=True,
            border_radius=8
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Modifier dossier" if dossier else "Nouveau dossier",
                style=title_style
            ),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("* Champs obligatoires", style=ft.TextStyle(size=12, color=ft.Colors.GREY_600)),
                    numero_field,
                    date_field,
                    personne_field,
                    objet_field,
                    ref_field,
                    ft.Row([debut_field, fin_field], spacing=10, expand=True), # Utilise expand=True pour que les champs prennent l'espace
                    obs_field
                ], 
                scroll=ft.ScrollMode.AUTO,
                height=400, # Hauteur fixe pour le contenu du dialogue, avec défilement
                spacing=10),
                padding=10
            ),
            actions=[
                ft.TextButton(
                    "Annuler",
                    on_click=lambda e: setattr(dialog, 'open', False) or page.update(), # Fermer et update la page
                    style=ft.ButtonStyle(color=ft.Colors.RED)
                ),
                ft.ElevatedButton(
                    "Enregistrer",
                    on_click=save_dossier,
                    icon=ft.Icons.SAVE,
                    style=button_style
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()

    def delete_dossier(dossier_id): # Renommé pour être plus clair
        def confirm_delete(e):
            try:
                cursor.execute("DELETE FROM dossiers WHERE id=?", (dossier_id,))
                conn.commit()
                dialog.open = False
                page.update()
                
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Dossier supprimé avec succès"),
                    action="OK",
                    bgcolor=ft.Colors.GREEN_700
                )
                page.snack_bar.open = True
                
                load_dossiers() # Recharger les dossiers après suppression
            except Exception as ex:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Erreur lors de la suppression: {str(ex)}"),
                    action="OK",
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
            finally:
                page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmer la suppression", style=title_style),
            content=ft.Text("Cette action est irréversible. Voulez-vous vraiment supprimer ce dossier ?"),
            actions=[
                ft.TextButton(
                    "Annuler",
                    on_click=lambda e: setattr(dialog, 'open', False) or page.update(),
                    style=ft.ButtonStyle(color=ft.Colors.GREY)
                ),
                ft.ElevatedButton(
                    "Supprimer",
                    on_click=confirm_delete,
                    icon=ft.Icons.DELETE,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()

    def update_pagination():
        pagination_controls.controls.clear()
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        
        if total_pages <= 1 and current_search_query == "": # N'affiche pas la pagination si pas de recherche et 1 seule page
            return

        # Bouton Première page
        pagination_controls.controls.append(
            ft.IconButton(
                icon=ft.Icons.FIRST_PAGE,
                on_click=lambda e: change_page(1), # Change page directement à 1
                disabled=current_page <= 1,
                tooltip="Première page"
            )
        )
        
        # Bouton Précédent
        pagination_controls.controls.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                on_click=lambda e: change_page(-1),
                disabled=current_page <= 1,
                tooltip="Page précédente"
            )
        )
        
        # Affichage page actuelle
        pagination_controls.controls.append(
            ft.Text(
                f"Page {current_page}/{total_pages} ({total_items} dossiers)", # Ajout du nombre total
                style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD)
            )
        )
        
        # Bouton Suivant
        pagination_controls.controls.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                on_click=lambda e: change_page(1),
                disabled=current_page >= total_pages,
                tooltip="Page suivante"
            )
        )
        
        # Bouton Dernière page
        pagination_controls.controls.append(
            ft.IconButton(
                icon=ft.Icons.LAST_PAGE,
                on_click=lambda e: change_page(total_pages), # Change page directement à la dernière
                disabled=current_page >= total_pages,
                tooltip="Dernière page"
            )
        )
        
        page.update()

    def change_page(delta):
        nonlocal current_page
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        
        new_page = current_page + delta if isinstance(delta, int) else delta # Permet de passer un entier (+1, -1) ou un numéro de page direct
        
        if 1 <= new_page <= total_pages:
            current_page = new_page
            if current_search_query:
                search_dossiers()
            else:
                load_dossiers()
        page.update() # Mettre à jour la page après le changement de page
            
    # Layout principal amélioré
    page.add(
        ft.Column([
            ft.Row([
                ft.Text(
                    "Gestion des Dossiers",
                    style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD),
                    expand=True
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: load_dossiers(),
                    tooltip="Actualiser"
                )
            ]),
            ft.Divider(height=10),
            ft.Row([
                search_field,
                search_button,
                add_button
            ], spacing=10),
            ft.Divider(height=10),
            ft.Container(
                content=results_container,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                expand=True
            ),
            ft.Divider(height=10),
            pagination_controls
        ], expand=True)
    )

    # Chargement initial des dossiers
    load_dossiers()

# Lancement de l'application Flet
if __name__ == "__main__":
    ft.app(target=main)