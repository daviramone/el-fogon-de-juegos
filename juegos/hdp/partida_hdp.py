# partida_hdp.py

import random
import uuid
from .mazo import Mazo
from .jugador_hdp import JugadorHDP

PUNTOS_PARA_GANAR_DEFAULT = 10

class PartidaHDP:
    def __init__(self, nombres_jugadores, puntos_para_ganar=PUNTOS_PARA_GANAR_DEFAULT, id_partida=None):
        if not nombres_jugadores or len(nombres_jugadores) < 3:
            raise ValueError("Se necesitan al menos 3 jugadores.")
        
        self.id_partida = id_partida if id_partida else str(uuid.uuid4())
        self.mazo = Mazo()
        self.jugadores = [JugadorHDP(nombre) for nombre in nombres_jugadores]
        random.shuffle(self.jugadores)
        
        self.puntos_para_ganar = puntos_para_ganar
        self.ronda_actual = 0
        self.hdp_actual_idx = -1
        self.carta_negra_actual = None
        self.respuestas_ronda_actual = {}  # Almacena {nombre_jugador: [lista_de_objetos_CartaBlanca]}
        self.estado_partida = "iniciando"
        self.ganador_ronda_anterior = None
        self.ganador_del_juego = None
        self._repartir_cartas_iniciales()

    def _repartir_cartas_iniciales(self):
        for jugador in self.jugadores:
            jugador.reponer_mano(self.mazo)

    def get_hdp_actual(self):
        return self.jugadores[self.hdp_actual_idx] if 0 <= self.hdp_actual_idx < len(self.jugadores) else None
    
    def get_jugador_por_nombre(self, nombre):
        return next((j for j in self.jugadores if j.nombre == nombre), None)

    def iniciar_nueva_ronda(self):
        if self.ganador_del_juego: return False

        self.ronda_actual += 1
        self.respuestas_ronda_actual = {}
        self.ganador_ronda_anterior = None
        
        self.hdp_actual_idx = (self.hdp_actual_idx + 1) % len(self.jugadores)
        
        for i, p in enumerate(self.jugadores):
            p.limpiar_estado_ronda()
            p.es_hdp_actual = (i == self.hdp_actual_idx)

        self.carta_negra_actual = self.mazo.robar_carta_negra()
        if not self.carta_negra_actual:
            self.estado_partida = "juego_terminado"
            self.ganador_del_juego = self._determinar_ganador_por_puntos()
            return False
            
        self.estado_partida = "esperando_respuestas"
        return True

    def recibir_respuesta_de_jugador(self, nombre_jugador, ids_cartas_jugadas):
        jugador = self.get_jugador_por_nombre(nombre_jugador)
        if not jugador or jugador.es_hdp_actual or jugador.ha_jugado_ronda: return False

        cartas_jugadas_obj = [carta for carta in jugador.mano if carta.id in ids_cartas_jugadas]

        if len(cartas_jugadas_obj) != self.carta_negra_actual.espacios_requeridos:
            return False

        jugador.ha_jugado_ronda = True
        jugador.respuestas_enviadas = cartas_jugadas_obj
        self.respuestas_ronda_actual[jugador.nombre] = cartas_jugadas_obj
        jugador.mano = [carta for carta in jugador.mano if carta.id not in ids_cartas_jugadas]
        
        jugador.reponer_mano(self.mazo)
        return True

    def hdp_descartar_y_robar(self, nombre_jugador, ids_cartas_a_descartar):
        jugador = self.get_jugador_por_nombre(nombre_jugador)
        if not jugador or not jugador.es_hdp_actual or jugador.ha_jugado_ronda: return False
        
        jugador.ha_jugado_ronda = True
        
        cartas_descartadas = [c for c in jugador.mano if c.id in ids_cartas_a_descartar]
        for carta in cartas_descartadas:
            self.mazo.descarte_blancas.append(carta)

        jugador.mano = [c for c in jugador.mano if c.id not in ids_cartas_a_descartar]
        
        jugador.reponer_mano(self.mazo)
        return True

    def todos_han_jugado(self):
        jugadores_que_deben_jugar = [j for j in self.jugadores if not j.es_hdp_actual]
        return all(j.ha_jugado_ronda for j in jugadores_que_deben_jugar)

    def seleccionar_respuesta_ganadora(self, nombre_jugador_ganador):
        # --- LÓGICA DE GANADOR CORREGIDA ---
        # Ahora es mucho más simple y seguro.
        if nombre_jugador_ganador not in self.respuestas_ronda_actual:
            return False

        jugador_ganador = self.get_jugador_por_nombre(nombre_jugador_ganador)
        if jugador_ganador:
            jugador_ganador.cartas_negras_ganadas.append(self.carta_negra_actual)
            self.ganador_ronda_anterior = jugador_ganador
            
            if len(jugador_ganador.cartas_negras_ganadas) >= self.puntos_para_ganar:
                self.ganador_del_juego = jugador_ganador
            
            self.estado_partida = "fin_ronda"
            return True
        return False

    def _determinar_ganador_por_puntos(self):
        if not self.jugadores: return None
        return max(self.jugadores, key=lambda j: len(j.cartas_negras_ganadas))

    def get_frase_ganadora_formateada(self):
        if not self.carta_negra_actual or not self.ganador_ronda_anterior: return ""
        
        combo_cartas_obj = self.ganador_ronda_anterior.respuestas_enviadas
        texto_frase = self.carta_negra_actual.texto
        
        if '_' not in texto_frase:
            return texto_frase + " " + " / ".join([f"<strong>{c.texto}</strong>" for c in combo_cartas_obj])

        for carta in combo_cartas_obj:
            texto_frase = texto_frase.replace('_', f"<strong>{carta.texto}</strong>", 1)
        return texto_frase
# PEGAR ESTE CÓDIGO NUEVO
    def get_estado_para_todos(self):
        estados_completos = {}
        hdp_actual_obj = self.get_hdp_actual()

        # Preparamos la lista de respuestas una sola vez
        respuestas_para_hdp = []
        if self.estado_partida == 'esperando_seleccion_hdp':
            respuestas_mezcladas = list(self.respuestas_ronda_actual.items())
            random.shuffle(respuestas_mezcladas)
            for nombre_jugador, combo in respuestas_mezcladas:
                respuestas_para_hdp.append({
                    "combo_id": nombre_jugador,
                    "cartas": [carta.to_dict() for carta in combo]
                })

        # Creamos un estado personalizado para cada jugador
        for jugador in self.jugadores:
            estado_personal = {
                "id_partida": self.id_partida,
                "estado_partida": self.estado_partida,
                "ronda_actual": self.ronda_actual,
                "nombre_hdp_actual": hdp_actual_obj.nombre if hdp_actual_obj else None,
                "carta_negra_actual": self.carta_negra_actual.to_dict() if self.carta_negra_actual else None,
                "jugadores": [p.to_dict() for p in self.jugadores],
                "mi_mano": jugador.get_mano_dict(),
                "soy_hdp": jugador.es_hdp_actual,
                "ya_jugue": jugador.ha_jugado_ronda,
                "ganador_del_juego": self.ganador_del_juego.nombre if self.ganador_del_juego else None,
                # Por defecto, la lista está vacía
                "respuestas_para_elegir": [] 
            }

            # SOLO si el jugador es el HDP y estamos en el estado correcto,
            # le añadimos la lista de respuestas.
            if jugador.es_hdp_actual and self.estado_partida == 'esperando_seleccion_hdp':
                estado_personal["respuestas_para_elegir"] = respuestas_para_hdp

            estados_completos[jugador.nombre] = estado_personal

        return estados_completos
