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

    # Connexion à la base de données
    conn = sqlite3.connect('dossiers.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Création de la table
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
    items_per_page = 10
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

    # Composants UI
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
        on_click=lambda e: open_edit_dialog(None),
        style=button_style
    )

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

    # Date pickers (defined at the main level)
    date_picker = ft.DatePicker(
        first_date=datetime(2000, 1, 1),
        last_date=datetime(2100, 12, 31)
    )
    
    debut_picker = ft.DatePicker(
        first_date=datetime(2000, 1, 1),
        last_date=datetime(2100, 12, 31)
    )
    
    fin_picker = ft.DatePicker(
        first_date=datetime(2000, 1, 1),
        last_date=datetime(2100, 12, 31)
    )
    
    # Add date pickers to page overlay
    page.overlay.extend([date_picker, debut_picker, fin_picker])

    def load_dossiers():
        nonlocal total_items, current_search_query
        
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
        current_search_query = query
        
        if query:
            sql = """
            SELECT id, numero, date, personne, objet, numero_reference, date_debut, date_fin, observation, COUNT(*) OVER() as total 
            FROM dossiers 
            WHERE numero LIKE ? OR personne LIKE ? OR objet LIKE ? OR numero_reference LIKE ? OR date LIKE ? OR date_debut LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """
            param = f"%{query}%"
            offset = (current_page - 1) * items_per_page
            cursor.execute(sql, (param, param, param, param, param, param, items_per_page, offset))
            
            results = cursor.fetchall()
            if results:
                total_items = results[0][-1]
            else:
                total_items = 0
            display_results([row[:-1] for row in results])
        else:
            current_search_query = ""
            load_dossiers()
        update_pagination()

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
        return ft.Card(
            elevation=5,
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.BLUE_500),
                        title=ft.Text(
                            f"Dossier {row[1]}",
                            style=title_style
                        ),
                        subtitle=ft.Text(
                            f"Par {row[3]} - {row[4]}",
                            style=text_style
                        ),
                        trailing=ft.PopupMenuButton(
                            icon=ft.Icons.MORE_VERT,
                            items=[
                                ft.PopupMenuItem(
                                    text="Modifier",
                                    icon=ft.Icons.EDIT,
                                    on_click=lambda e, r=row: open_edit_dialog(r)
                                ),
                                ft.PopupMenuItem(
                                    text="Supprimer",
                                    icon=ft.Icons.DELETE,
                                    on_click=lambda e, dossier_id=row[0]: delete_dossier(dossier_id)
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
        def save_dossier(e):
            if not numero_field.value or not date_field.value or not personne_field.value or not objet_field.value:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Veuillez remplir tous les champs obligatoires (*)"),
                    action="OK",
                    bgcolor=ft.Colors.RED_700
                )
                page.snack_bar.open = True
                page.update()
                return
            
            try:
                if dossier:
                    cursor.execute("""
                    UPDATE dossiers SET 
                    numero=?, date=?, personne=?, objet=?, 
                    numero_reference=?, date_debut=?, date_fin=?, observation=?
                    WHERE id=?
                    """, (
                        numero_field.value,
                        date_field.value,
                        personne_field.value,
                        objet_field.value,
                        ref_field.value.strip() if ref_field.value else None,
                        debut_field.value.strip() if debut_field.value else None,
                        fin_field.value.strip() if fin_field.value else None,
                        obs_field.value.strip() if obs_field.value else None,
                        dossier[0]
                    ))
                    message = "Dossier mis à jour avec succès !"
                else:
                    cursor.execute("""
                    INSERT INTO dossiers (
                        numero, date, personne, objet, 
                        numero_reference, date_debut, date_fin, observation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        numero_field.value,
                        date_field.value,
                        personne_field.value,
                        objet_field.value,
                        ref_field.value.strip() if ref_field.value else None,
                        debut_field.value.strip() if debut_field.value else None,
                        fin_field.value.strip() if fin_field.value else None,
                        obs_field.value.strip() if obs_field.value else None
                    ))
                    message = "Nouveau dossier créé avec succès !"
                
                conn.commit()
                dialog.open = False
                page.update()
                
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(message),
                    action="OK",
                    bgcolor=ft.Colors.GREEN_700
                )
                page.snack_bar.open = True
                
                load_dossiers()
            except sqlite3.IntegrityError as ex:
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
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Une erreur est survenue: {str(ex)}"),
                    action="OK",
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
            finally:
                page.update()

        # Fonctions pour les date pickers
        def open_date_picker(e):
            date_picker.pick_date_dialog()
            
        def open_debut_picker(e):
            debut_picker.pick_date_dialog()
            
        def open_fin_picker(e):
            fin_picker.pick_date_dialog()
            
        def update_date_field(e):
            date_field.value = date_picker.value.strftime("%Y-%m-%d") if date_picker.value else ""
            page.update()
            
        def update_debut_field(e):
            debut_field.value = debut_picker.value.strftime("%Y-%m-%d") if debut_picker.value else ""
            page.update()
            
        def update_fin_field(e):
            fin_field.value = fin_picker.value.strftime("%Y-%m-%d") if fin_picker.value else ""
            page.update()

        # Set up date picker change handlers
        date_picker.on_change = update_date_field
        debut_picker.on_change = update_debut_field
        fin_picker.on_change = update_fin_field

        # Set initial values if editing
        if dossier:
            if dossier[2]:  # Date
                try:
                    date_picker.value = datetime.strptime(dossier[2], "%Y-%m-%d")
                except:
                    pass
            if dossier[6]:  # Date début
                try:
                    debut_picker.value = datetime.strptime(dossier[6], "%Y-%m-%d")
                except:
                    pass
            if dossier[7]:  # Date fin
                try:
                    fin_picker.value = datetime.strptime(dossier[7], "%Y-%m-%d")
                except:
                    pass

        # Champs du formulaire
        numero_field = ft.TextField(
            label="Numéro*",
            value=dossier[1] if dossier else "",
            text_size=14,
            filled=True,
            border_radius=8,
            autofocus=True
        )
        
        date_field = ft.TextField(
            label="Date*",
            value=dossier[2] if dossier else "",
            hint_text="Sélectionnez une date",
            text_size=14,
            filled=True,
            border_radius=8,
            read_only=True,
            suffix=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                on_click=open_date_picker,
                tooltip="Sélectionner une date"
            )
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
            label="Date début",
            value=dossier[6] if dossier else "",
            hint_text="Sélectionnez une date",
            text_size=14,
            filled=True,
            border_radius=8,
            read_only=True,
            suffix=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                on_click=open_debut_picker,
                tooltip="Sélectionner une date"
            )
        )
        
        fin_field = ft.TextField(
            label="Date fin",
            value=dossier[7] if dossier else "",
            hint_text="Sélectionnez une date",
            text_size=14,
            filled=True,
            border_radius=8,
            read_only=True,
            suffix=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                on_click=open_fin_picker,
                tooltip="Sélectionner une date"
            )
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
                    ft.Row([debut_field, fin_field], spacing=10, expand=True),
                    obs_field
                ], 
                scroll=ft.ScrollMode.AUTO,
                height=400,
                spacing=10),
                padding=10
            ),
            actions=[
                ft.TextButton(
                    "Annuler",
                    on_click=lambda e: setattr(dialog, 'open', False) or page.update(),
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
        
        #page.dialog = dialog
        #dialog.open = True
        #page.update()
        print("--- Opening dialog with page.open() ---") # DEBUG PRINT
        page.open(dialog) # <--- ADD THIS LINE INSTEAD
        print("--- Exiting open_edit_dialog ---") # DEBUG PRINT
    def delete_dossier(dossier_id):
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
                
                load_dossiers()
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
        
        if total_pages <= 1 and current_search_query == "":
            return

        pagination_controls.controls.append(
            ft.IconButton(
                icon=ft.Icons.FIRST_PAGE,
                on_click=lambda e: change_page(1),
                disabled=current_page <= 1,
                tooltip="Première page"
            )
        )
        
        pagination_controls.controls.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                on_click=lambda e: change_page(-1),
                disabled=current_page <= 1,
                tooltip="Page précédente"
            )
        )
        
        pagination_controls.controls.append(
            ft.Text(
                f"Page {current_page}/{total_pages} ({total_items} dossiers)",
                style=ft.TextStyle(size=14, weight=ft.FontWeight.BOLD)
            )
        )
        
        pagination_controls.controls.append(
            ft.IconButton(
                icon=ft.Icons.CHEVRON_RIGHT,
                on_click=lambda e: change_page(1),
                disabled=current_page >= total_pages,
                tooltip="Page suivante"
            )
        )
        
        pagination_controls.controls.append(
            ft.IconButton(
                icon=ft.Icons.LAST_PAGE,
                on_click=lambda e: change_page(total_pages),
                disabled=current_page >= total_pages,
                tooltip="Dernière page"
            )
        )
        
        page.update()

    def change_page(delta):
        nonlocal current_page
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        
        new_page = current_page + delta if isinstance(delta, int) else delta
        
        if 1 <= new_page <= total_pages:
            current_page = new_page
            if current_search_query:
                search_dossiers()
            else:
                load_dossiers()
        page.update()
            
    # Layout principal
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

if __name__ == "__main__":
    ft.app(target=main)