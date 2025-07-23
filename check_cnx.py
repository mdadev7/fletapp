import flet as ft
import oracledb as cx_Oracle # import cx_Oracle  
ORACLE_USER = "user_dev"
ORACLE_PASSWORD = "user_dev"
ORACLE_DSN = "localhost:1522/XEPDB1"
def main(page: ft.Page):
    def connect_to_oracle(e):
        try:
            # Configuration type (à adapter)
            dsn = cx_Oracle.makedsn(
                host="localhost", 
                port=1522, 
                service_name="XEPDB1"
            )
            connection = cx_Oracle.connect(
                user="user_dev",
                password="user_dev",
                dsn=dsn
            )
            page.add(ft.Text("Connexion réussie à Oracle!"))
        except Exception as e:
            page.add(ft.Text(f"Erreur de connexion: {str(e)}", color="red"))

    page.add(
        ft.ElevatedButton("Tester la connexion Oracle", on_click=connect_to_oracle)
    )

ft.app(target=main)