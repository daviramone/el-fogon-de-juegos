# carta.py

import uuid

class Carta:
    """Clase base para todas las cartas del juego."""
    def __init__(self, texto, id_carta=None):
        self.id = id_carta if id_carta else str(uuid.uuid4())
        self.texto = texto

    def to_dict(self):
        """Serializa la carta a un diccionario para enviarlo al frontend."""
        return {
            "id": self.id,
            "texto": self.texto
        }

    def __repr__(self):
        return f"Carta({self.texto})"

class CartaBlanca(Carta):
    """Representa una carta blanca de respuesta."""
    pass

class CartaNegra(Carta):
    """Representa una carta negra de pregunta o frase a completar."""
    def __init__(self, texto, espacios_requeridos=1, id_carta=None):
        super().__init__(texto, id_carta)
        self.espacios_requeridos = espacios_requeridos

    def to_dict(self):
        """Serializa la carta negra a un diccionario."""
        data = super().to_dict()
        data['espacios_requeridos'] = self.espacios_requeridos
        return data