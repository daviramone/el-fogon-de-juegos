# jugador_hdp.py
import uuid

class JugadorHDP:
    def __init__(self, nombre, cartas_por_mano=10):
        self.id_jugador = str(uuid.uuid4())
        self.nombre = nombre
        self.mano = []
        self.cartas_por_mano = cartas_por_mano
        self.respuestas_enviadas = []
        
        # CAMBIO: Ahora coleccionamos las cartas negras ganadas como trofeos
        self.cartas_negras_ganadas = []
        
        # Estado de la ronda
        self.es_hdp_actual = False
        self.ha_jugado_ronda = False

    def reponer_mano(self, mazo):
        """Roba cartas hasta volver a tener el máximo en la mano."""
        while len(self.mano) < self.cartas_por_mano:
            carta = mazo.robar_carta_blanca()
            if carta:
                self.mano.append(carta)
            else:
                break # No hay más cartas en el mazo

    def limpiar_estado_ronda(self):
        self.es_hdp_actual = False
        self.ha_jugado_ronda = False
        self.respuestas_enviadas = []
        
    def get_mano_dict(self):
        return [carta.to_dict() for carta in self.mano]

    def to_dict(self):
        """Genera una representación del jugador para enviar al frontend."""
        return {
            "nombre": self.nombre,
            # CAMBIO: Los puntos ahora son la cantidad de trofeos
            "puntos": len(self.cartas_negras_ganadas), 
            "ha_jugado_ronda": self.ha_jugado_ronda
        }