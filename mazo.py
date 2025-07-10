# backend/game_logic/mazo.py
import random
import os
import json
from carta import CartaBlanca, CartaNegra

class Mazo:
    def __init__(self):
        self.cartas_blancas = []
        self.descarte_blancas = []
        self.cartas_negras = []
        self.descarte_negras = []

        # --- INICIO DE LA CORRECCIÓN ---
        # Usamos la ruta COMPLETA y EXACTA a tus archivos.
        # La 'r' al principio es MUY IMPORTANTE para que Windows entienda bien la ruta.
        ruta_blancas_json = r"C:\Users\Davi\Desktop\python\clue\Juegos terminados\PlataformaDeJuegos\data\cartas_blancas.json"
        ruta_negras_json = r"C:\Users\Davi\Desktop\python\clue\Juegos terminados\PlataformaDeJuegos\data\cartas_negras.json"
        # --- FIN DE LA CORRECCIÓN ---
        
        # Cargar cartas desde JSON
        self._cargar_cartas_json(ruta_blancas_json, CartaBlanca, self.cartas_blancas)
        self._cargar_cartas_json(ruta_negras_json, CartaNegra, self.cartas_negras)
        
        self.mezclar_mazos()

    def _cargar_cartas_json(self, archivo, clase_carta, lista_destino):
        """
        Carga cartas desde un archivo JSON.
        """
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos_cartas = json.load(f)
                for item in datos_cartas:
                    texto = item.get('texto')
                    if not texto:
                        continue

                    if clase_carta == CartaNegra:
                        espacios = item.get('espacios_requeridos', 1)
                        lista_destino.append(clase_carta(texto, espacios))
                    else:
                        lista_destino.append(clase_carta(texto))
        except FileNotFoundError:
            print(f"ADVERTENCIA: Archivo JSON de cartas no encontrado en {archivo}. El mazo estará vacío.")
        except json.JSONDecodeError:
            print(f"ERROR: No se pudo parsear el archivo JSON en {archivo}. Asegúrate de que el formato sea válido.")
        except Exception as e:
            print(f"ERROR inesperado al cargar cartas de {archivo}: {e}")

    def mezclar_mazos(self):
        random.shuffle(self.cartas_blancas)
        random.shuffle(self.cartas_negras)

    def _reponer_mazo_desde_descarte(self, mazo, descarte, tipo):
        """Si un mazo está vacío, lo repone desde su descarte."""
        if not mazo and descarte:
            print(f"Mezclando descarte de cartas {tipo} de vuelta al mazo.")
            mazo.extend(descarte)
            descarte.clear()
            random.shuffle(mazo)

    def robar_carta_blanca(self):
        self._reponer_mazo_desde_descarte(self.cartas_blancas, self.descarte_blancas, "blancas")
        if not self.cartas_blancas:
            return None
        return self.cartas_blancas.pop()

    def robar_carta_negra(self):
        self._reponer_mazo_desde_descarte(self.cartas_negras, self.descarte_negras, "negras")
        if not self.cartas_negras:
            return None
        return self.cartas_negras.pop()