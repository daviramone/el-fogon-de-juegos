# backend/game_logic/carta.py
class Carta:
    """Clase base para las cartas."""
    def __init__(self, texto):
        self.texto = texto

    def to_dict(self):
        """Serializa la carta a un diccionario para JSON."""
        return {"texto": self.texto}

class CartaBlanca(Carta):
    """Representa una carta blanca de respuesta."""
    pass # No necesita atributos adicionales por ahora

class CartaNegra(Carta):
    """Representa una carta negra de pregunta/frase a completar."""
    def __init__(self, texto, espacios_requeridos=1):
        super().__init__(texto)
        self.espacios_requeridos = espacios_requeridos

    def to_dict(self):
        """Serializa la carta negra a un diccionario para JSON."""
        return {
            "texto": self.texto,
            "espacios_requeridos": self.espacios_requeridos
        }