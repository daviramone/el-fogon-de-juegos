# servidor.py

from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import os

# --- CORRECCIÓN DE IMPORTACIÓN ---
from juegos.hdp.partida_hdp import PartidaHDP
app = Flask(__name__)
# --- CORRECCIÓN DE SEGURIDAD ---
# Usamos una clave secreta aleatoria y más segura
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)

lobby_jugadores = {}
partidas_activas = {}
jugadores_en_partida = {} # Mapea sid -> {'id_partida': ..., 'nombre_jugador': ...}

@app.route('/', methods=['GET', 'POST'])
def inicio():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        if nombre:
            return redirect(url_for('lobby', nombre=nombre))
    return render_template('inicio.html')

@app.route('/lobby/<nombre>')
def lobby(nombre):
    return render_template('lobby.html', nombre_jugador=nombre)

@app.route('/juego/hdp/<id_partida>/<nombre_jugador>')
def mesa_de_juego_hdp(id_partida, nombre_jugador):
    if id_partida in partidas_activas:
        return render_template('hdp_juego.html', id_partida=id_partida, nombre_jugador=nombre_jugador)
    return redirect(url_for('lobby', nombre=nombre_jugador))

def emitir_actualizacion_lobby():
    lista_nombres = list(lobby_jugadores.values())
    socketio.emit('actualizar_lobby', {'jugadores': lista_nombres})

@socketio.on('connect')
def al_conectar():
    print(f"Cliente conectado: {request.sid}")

@socketio.on('disconnect')
def al_desconectar():
    if request.sid in lobby_jugadores:
        lobby_jugadores.pop(request.sid, None)
        emitir_actualizacion_lobby()
    
    if request.sid in jugadores_en_partida:
        info = jugadores_en_partida.pop(request.sid, None)
        # Aquí se podría añadir lógica para manejar la desconexión en plena partida

@socketio.on('unirse_al_lobby')
def manejar_union_lobby(data):
    nombre = data.get('nombre')
    if nombre:
        lobby_jugadores[request.sid] = nombre
        emitir_actualizacion_lobby()

@socketio.on('crear_partida_hdp')
def crear_partida_hdp(data):
    nombres_seleccionados = data.get('jugadores_seleccionados', [])
    if len(nombres_seleccionados) < 3:
        emit('error_creacion', {'mensaje': 'Se necesitan al menos 3 jugadores.'}, to=request.sid)
        return

    id_partida = str(uuid.uuid4())[:8]
    try:
        nueva_partida = PartidaHDP(nombres_jugadores=nombres_seleccionados, id_partida=id_partida)
        partidas_activas[id_partida] = nueva_partida
    except Exception as e:
        emit('error_creacion', {'mensaje': f'Error al crear la partida: {e}'}, to=request.sid)
        return

    if nueva_partida.iniciar_nueva_ronda():
        sids_a_redirigir = {sid: nombre for sid, nombre in lobby_jugadores.items() if nombre in nombres_seleccionados}
        
        for sid in sids_a_redirigir:
            lobby_jugadores.pop(sid, None)
        emitir_actualizacion_lobby()

        for sid, nombre in sids_a_redirigir.items():
            url = url_for('mesa_de_juego_hdp', id_partida=id_partida, nombre_jugador=nombre)
            emit('partida_creada', {'url': url}, to=sid)
    else:
        emit('error_creacion', {'mensaje': 'No se pudo iniciar la partida. ¿Faltan cartas en el mazo?'}, to=request.sid)

def emitir_actualizacion_a_todos(id_partida):
    partida = partidas_activas.get(id_partida)
    if not partida: return
    
    estados_personales = partida.get_estado_para_todos()
    for sid, info in list(jugadores_en_partida.items()):
        if info.get('id_partida') == id_partida:
            nombre = info.get('nombre_jugador')
            if nombre in estados_personales:
                emit('actualizar_estado_juego', estados_personales[nombre], to=sid)

@socketio.on('unirse_a_partida')
def manejar_union_partida(data):
    id_partida = data.get('id_partida')
    nombre_jugador = data.get('nombre_jugador')
    if id_partida in partidas_activas:
        join_room(id_partida)
        jugadores_en_partida[request.sid] = {'id_partida': id_partida, 'nombre_jugador': nombre_jugador}
        emitir_actualizacion_a_todos(id_partida)
    else:
        emit('error_juego', {'mensaje': 'La partida ya no existe.'}, to=request.sid)

@socketio.on('jugar_cartas')
def manejar_jugar_cartas(data):
    info_jugador = jugadores_en_partida.get(request.sid, {})
    id_partida = info_jugador.get('id_partida')
    partida = partidas_activas.get(id_partida)
    if not all([id_partida, info_jugador.get('nombre_jugador'), partida]): return
    
    # --- CORRECCIÓN DE LÓGICA ---
    # Ahora se envían los IDs de las cartas, no los índices
    partida.recibir_respuesta_de_jugador(info_jugador['nombre_jugador'], data.get('ids_cartas', []))
    
    if partida.todos_han_jugado():
        partida.estado_partida = 'esperando_seleccion_hdp'
    emitir_actualizacion_a_todos(id_partida)

@socketio.on('hdp_descartar_cartas')
def hdp_descartar_cartas(data):
    info_jugador = jugadores_en_partida.get(request.sid, {})
    id_partida = info_jugador.get('id_partida')
    partida = partidas_activas.get(id_partida)
    if not all([id_partida, info_jugador.get('nombre_jugador'), partida]): return

    partida.hdp_descartar_y_robar(info_jugador['nombre_jugador'], data.get('ids_cartas', []))
    emitir_actualizacion_a_todos(id_partida)

@socketio.on('seleccionar_ganador')
def manejar_seleccion_ganador(data):
    info_jugador = jugadores_en_partida.get(request.sid, {})
    id_partida = info_jugador.get('id_partida')
    partida = partidas_activas.get(id_partida)
    if not all([id_partida, info_jugador.get('nombre_jugador'), partida]): return
    
    if partida.get_hdp_actual().nombre != info_jugador['nombre_jugador']:
        return emit('error_juego', {'mensaje': 'Solo el HDP puede elegir.'}, to=request.sid)

    # --- CORRECCIÓN DE LÓGICA DE GANADOR ---
    # Ahora se recibe el ID de la combinación ganadora, que es el nombre del jugador
    combo_id_ganador = data.get('combo_id_ganador')
    if partida.seleccionar_respuesta_ganadora(combo_id_ganador):
        info_ronda = {
            'nombre_ganador': partida.ganador_ronda_anterior.nombre,
            'puntos_ganador': len(partida.ganador_ronda_anterior.cartas_negras_ganadas),
            'frase_completa': partida.get_frase_ganadora_formateada()
        }
        socketio.emit('ronda_terminada', info_ronda, to=id_partida)
    else:
        emit('error_juego', {'mensaje': 'Error al seleccionar ganador.'}, to=request.sid)

@socketio.on('iniciar_siguiente_ronda')
def iniciar_siguiente_ronda(data):
    id_partida = data.get('id_partida')
    partida = partidas_activas.get(id_partida)
    if not partida: return
    
    if partida.ganador_del_juego:
        partida.estado_partida = "juego_terminado"
    else:
        partida.iniciar_nueva_ronda()
    
    emitir_actualizacion_a_todos(id_partida)

# Funciones de chat y otras se mantienen igual...
@socketio.on('enviar_mensaje_chat')
def manejar_chat(data):
    id_partida = data.get('id_partida')
    if id_partida in partidas_activas:
        emit('recibir_mensaje_chat', data, to=id_partida)

@socketio.on('compartir_premio')
def compartir_premio(data):
    id_partida = data.get('id_partida')
    if id_partida in partidas_activas:
        emit('mostrar_premio', data, to=id_partida)

if __name__ == '__main__':
    # El allow_unsafe_werkzeug es solo para desarrollo, en producción no es ideal
    socketio.run(app, debug=True)