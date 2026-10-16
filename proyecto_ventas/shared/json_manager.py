import json
import os


class GestorJSON:
    """Lee y guarda una lista de diccionarios. Es la única parte que toca el disco."""

    def __init__(self, ruta):
        self.ruta = ruta
        carpeta = os.path.dirname(ruta)
        if carpeta and not os.path.exists(carpeta):
            os.makedirs(carpeta)

    def leer(self):
        # Devuelve SIEMPRE una lista: vacía si el archivo no existe o está dañado
        if not os.path.exists(self.ruta):
            return []
        try:
            with open(self.ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
        except (json.JSONDecodeError, OSError):
            # Capturamos errores concretos, nunca un "except:" pelado
            return []

    def guardar(self, datos):
        try:
            with open(self.ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
            return True
        except (TypeError, OSError):
            return False
if __name__ == "__main__":
    import sys

    # Carpeta del proyecto = una carpeta arriba de shared/
    carpeta_proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, carpeta_proyecto)   # para poder hacer "import main"
    os.chdir(carpeta_proyecto)             # para que "data/..." apunte al lugar correcto

    import main
    main.ejecutar_menu("CLIENTES", main.MENU_CLIENTES)