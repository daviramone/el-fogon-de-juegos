# jugador_hdp.py

import uuid

LIMITE_CARTAS_MANO = 10

class JugadorHDP:
    """Representa a un jugador en la partida de HDP."""
    def __init__(self, nombre, sid=None):
        self.id_jugador = str(uuid.uuid4())
        self.nombre = nombre
        self.sid = sid  # Session ID de SocketIO
        self.mano = []
        self.cartas_negras_ganadas = []
        
        # Estado de la ronda
        self.es_hdp_actual = False
        self.ha_jugado_ronda = False
        self.respuestas_enviadas = [] # Guarda las cartas que jugó en la ronda

    def limpiar_estado_ronda(self):
        """Reinicia el estado del jugador para la siguiente ronda."""
        self.es_hdp_actual = False
        self.ha_jugado_ronda = False
        self.respuestas_enviadas = []

    def reponer_mano(self, mazo):
        """Roba cartas del mazo hasta tener el límite en mano."""
        while len(self.mano) < LIMITE_CARTAS_MANO:
            carta = mazo.robar_carta_blanca()
            if carta:
                self.mano.append(carta)
            else:
                # No hay más cartas en el mazo
                break

    def get_mano_dict(self):
        """Devuelve la mano del jugador como una lista de diccionarios."""
        return [carta.to_dict() for carta in self.mano]

    def to_dict(self):
        """Devuelve una representación pública del jugador."""
        return {
            "id_jugador": self.id_jugador,
            "nombre": self.nombre,
            "puntos": len(self.cartas_negras_ganadas),
            "es_hdp_actual": self.es_hdp_actual,
            "ha_jugado_ronda": self.ha_jugado_ronda
        }

    def __repr__(self):
        return f"JugadorHDP(nombre='{self.nombre}', puntos={len(self.cartas_negras_ganadas)})"