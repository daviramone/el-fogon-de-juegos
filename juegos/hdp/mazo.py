# mazo.py CORREGIDO

import random
import os
import json
# Esta importación es correcta para la nueva estructura. El punto significa "desde la misma carpeta".
from .carta import CartaBlanca, CartaNegra

class Mazo:
    def __init__(self):
        self.cartas_blancas = []
        self.descarte_blancas = []
        self.cartas_negras = []
        self.descarte_negras = []

        # --- CORRECCIÓN DE RUTA ---
        # 1. Obtenemos la ruta del directorio de este archivo (juegos/hdp)
        directorio_archivo_actual = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Subimos dos niveles para llegar a la raíz del proyecto
        directorio_proyecto = os.path.dirname(os.path.dirname(directorio_archivo_actual))

        # 3. Construimos la ruta a la carpeta 'data' desde la raíz del proyecto
        ruta_blancas_json = os.path.join(directorio_proyecto, 'data', 'cartas_blancas.json')
        ruta_negras_json = os.path.join(directorio_proyecto, 'data', 'cartas_negras.json')
        
        # Cargar cartas desde JSON (el resto del código no cambia)
        self._cargar_cartas_json(ruta_blancas_json, CartaBlanca, self.cartas_blancas)
        self._cargar_cartas_json(ruta_negras_json, CartaNegra, self.cartas_negras)
        
        self.mezclar_mazos()

    def _cargar_cartas_json(self, archivo, clase_carta, lista_destino):
        """Carga cartas desde un archivo JSON, asignando IDs."""
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cartas = json.load(f)
                for item in datos_cartas:
                    texto = item.get('texto')
                    if not texto:
                        continue

                    if clase_carta == CartaNegra:
                        espacios = item.get('respuestas_necesarias', 1)
                        lista_destino.append(clase_carta(texto, espacios))
                    else:
                        lista_destino.append(clase_carta(texto))
        except FileNotFoundError:
            print(f"ADVERTENCIA: Archivo JSON no encontrado en {archivo}.")
        except Exception as e:
            print(f"ERROR inesperado al cargar cartas de {archivo}: {e}")

    def mezclar_mazos(self):
        random.shuffle(self.cartas_blancas)
        random.shuffle(self.cartas_negras)

    def _reponer_mazo_desde_descarte(self, mazo, descarte, tipo):
        """Si un mazo está vacío, lo repone desde su descarte."""
        if not mazo and descarte:
            mazo.extend(descarte)
            descarte.clear()
            random.shuffle(mazo)

    def robar_carta_blanca(self):
        self._reponer_mazo_desde_descarte(self.cartas_blancas, self.descarte_blancas, "blancas")
        return self.cartas_blancas.pop() if self.cartas_blancas else None

    def robar_carta_negra(self):
        self._reponer_mazo_desde_descarte(self.cartas_negras, self.descarte_negras, "negras")
        return self.cartas_negras.pop() if self.cartas_negras else None