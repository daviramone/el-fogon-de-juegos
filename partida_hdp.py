# partida_hdp.py
import random
import uuid
from mazo import Mazo
from jugador_hdp import JugadorHDP

PUNTOS_PARA_GANAR_DEFAULT = 7

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
        self.respuestas_ronda_actual = {}
        self.estado_partida = "iniciando"
        self.ganador_ronda_anterior = None
        self.ganador_del_juego = None
        self._repartir_cartas_iniciales()

    def _repartir_cartas_iniciales(self):
        for jugador in self.jugadores:
            jugador.reponer_mano(self.mazo)

    def get_hdp_actual(self):
        if 0 <= self.hdp_actual_idx < len(self.jugadores):
            return self.jugadores[self.hdp_actual_idx]
        return None
    
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

    def recibir_respuesta_de_jugador(self, nombre_jugador, indices_cartas):
        jugador = self.get_jugador_por_nombre(nombre_jugador)
        if not jugador or jugador.es_hdp_actual or jugador.ha_jugado_ronda: return False

        if any(i < 0 or i >= len(jugador.mano) for i in indices_cartas) or \
           len(indices_cartas) != self.carta_negra_actual.espacios_requeridos:
            return False

        cartas_jugadas_obj = [jugador.mano[i] for i in indices_cartas]
        jugador.ha_jugado_ronda = True
        jugador.respuestas_enviadas = cartas_jugadas_obj
        self.respuestas_ronda_actual[jugador.nombre] = cartas_jugadas_obj
        jugador.mano = [carta for i, carta in enumerate(jugador.mano) if i not in indices_cartas]
        
        jugador.reponer_mano(self.mazo)
        print(f"Jugador {jugador.nombre} ha jugado sus cartas.")
        return True

    def hdp_descartar_y_robar(self, nombre_jugador, indices_a_descartar):
        jugador = self.get_jugador_por_nombre(nombre_jugador)
        if not jugador or not jugador.es_hdp_actual or jugador.ha_jugado_ronda: return False
        
        jugador.ha_jugado_ronda = True
        
        indices_a_descartar.sort(reverse=True)
        for indice in indices_a_descartar:
            if 0 <= indice < len(jugador.mano):
                carta_descartada = jugador.mano.pop(indice)
                self.mazo.descarte_blancas.append(carta_descartada)
        
        jugador.reponer_mano(self.mazo)
        print(f"HDP {jugador.nombre} descartó {len(indices_a_descartar)} cartas y robó nuevas.")
        return True

    def todos_han_jugado(self):
        jugadores_que_deben_jugar = [j for j in self.jugadores if not j.es_hdp_actual]
        return all(j.ha_jugado_ronda for j in jugadores_que_deben_jugar)

    def seleccionar_respuesta_ganadora(self, cartas_ganadoras_dicts):
        if not cartas_ganadoras_dicts: return False
            
        textos_ganadores = [c['texto'] for c in cartas_ganadoras_dicts]
        nombre_jugador_ganador = None

        for nombre_jugador, combo_cartas_obj in self.respuestas_ronda_actual.items():
            textos_jugados = [c.texto for c in combo_cartas_obj]
            if sorted(textos_jugados) == sorted(textos_ganadores):
                nombre_jugador_ganador = nombre_jugador
                break
        
        if not nombre_jugador_ganador: return False

        jugador_ganador = self.get_jugador_por_nombre(nombre_jugador_ganador)
        if jugador_ganador:
            jugador_ganador.cartas_negras_ganadas.append(self.carta_negra_actual)
            self.ganador_ronda_anterior = jugador_ganador
            
            if len(jugador_ganador.cartas_negras_ganadas) >= self.puntos_para_ganar:
                self.ganador_del_juego = jugador_ganador
                self.estado_partida = "juego_terminado"
            else:
                self.estado_partida = "fin_ronda"
            
            return True
        return False

    def _determinar_ganador_por_puntos(self):
        if not self.jugadores: return None
        return max(self.jugadores, key=lambda j: len(j.cartas_negras_ganadas))

    def get_frase_ganadora_formateada(self, combo_cartas_obj):
        if not self.carta_negra_actual or not combo_cartas_obj: return ""
        
        texto_frase = self.carta_negra_actual.texto
        if texto_frase.count('_') != len(combo_cartas_obj):
            return texto_frase + " " + " / ".join([f"<strong>{c.texto}</strong>" for c in combo_cartas_obj])

        for carta in combo_cartas_obj:
            texto_frase = texto_frase.replace('_', f"<strong>{carta.texto}</strong>", 1)
        return texto_frase

    def get_estado_para_todos(self):
        estados_completos = {}
        hdp_actual_obj = self.get_hdp_actual()
        
        respuestas_para_hdp = []
        if self.estado_partida == 'esperando_seleccion_hdp':
            respuestas_mezcladas = list(self.respuestas_ronda_actual.values())
            random.shuffle(respuestas_mezcladas)
            respuestas_para_hdp = [[carta.to_dict() for carta in combo] for combo in respuestas_mezcladas]

        for jugador in self.jugadores:
            estado_base = {
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
                "respuestas_para_elegir": []
            }
            if jugador.es_hdp_actual and self.estado_partida == 'esperando_seleccion_hdp':
                estado_base["respuestas_para_elegir"] = respuestas_para_hdp
            
            estados_completos[jugador.nombre] = estado_base
        return estados_completos