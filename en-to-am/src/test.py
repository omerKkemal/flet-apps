import flet as ft

def main(page: ft.Page):
    page.services.append(ft.FilePicker())
    page.add(ft.Text("Hello"))

ft.run(main)
