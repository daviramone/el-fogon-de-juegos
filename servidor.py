# servidor.py
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

from partida_hdp import PartidaHDP

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plataforma_de_juegos_2025'
socketio = SocketIO(app)

lobby_jugadores = {}
partidas_activas = {}
jugadores_en_partida = {}

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
    socketio.emit('actualizar_lobby', {'jugadores': lista_nombres}, to='lobby_principal')

@socketio.on('connect')
def al_conectar():
    print(f"Cliente conectado: {request.sid}")

@socketio.on('disconnect')
def al_desconectar():
    if request.sid in lobby_jugadores:
        nombre = lobby_jugadores.pop(request.sid, None)
        if nombre: print(f"Jugador '{nombre}' desconectado del lobby.")
        emitir_actualizacion_lobby()
    
    if request.sid in jugadores_en_partida:
        info = jugadores_en_partida.pop(request.sid, None)
        if info:
            print(f"Jugador '{info['nombre_jugador']}' desconectado de la partida {info['id_partida']}.")

@socketio.on('unirse_al_lobby')
def manejar_union_lobby(data):
    nombre = data.get('nombre')
    if nombre and request.sid not in lobby_jugadores:
        join_room('lobby_principal')
        lobby_jugadores[request.sid] = nombre
        emitir_actualizacion_lobby()

@socketio.on('crear_partida_hdp')
def crear_partida_hdp(data):
    nombres_seleccionados = data.get('jugadores_seleccionados', [])
    if len(nombres_seleccionados) < 3:
        emit('error_creacion', {'mensaje': 'Se necesitan al menos 3 jugadores para HDP.'}, to=request.sid)
        return

    id_partida = str(uuid.uuid4())[:8]
    nueva_partida = PartidaHDP(nombres_jugadores=nombres_seleccionados, id_partida=id_partida)
    partidas_activas[id_partida] = nueva_partida
    
    # Iniciar la partida correctamente
    if nueva_partida.iniciar_nueva_ronda():
        print(f"Partida de HDP creada y primera ronda iniciada ({id_partida}) con: {', '.join(nombres_seleccionados)}")
        sids_a_redirigir = {}
        for sid, nombre in list(lobby_jugadores.items()):
            if nombre in nombres_seleccionados:
                sids_a_redirigir[sid] = nombre
                lobby_jugadores.pop(sid, None)
                leave_room('lobby_principal', sid)
        emitir_actualizacion_lobby()

        for sid, nombre in sids_a_redirigir.items():
            url = url_for('mesa_de_juego_hdp', id_partida=id_partida, nombre_jugador=nombre)
            emit('partida_creada', {'url': url}, to=sid)
    else:
        # Si no se pudo iniciar (ej. no hay cartas), avisar al creador
        emit('error_creacion', {'mensaje': 'No se pudo iniciar la partida. Faltan cartas en el mazo.'}, to=request.sid)


def emitir_actualizacion_a_todos(id_partida):
    partida = partidas_activas.get(id_partida)
    if not partida: return
    estados_personales = partida.get_estado_para_todos()
    for sid, info in list(jugadores_en_partida.items()):
        if info.get('id_partida') == id_partida:
            nombre = info.get('nombre_jugador')
            estado_personal = estados_personales.get(nombre)
            if estado_personal:
                emit('actualizar_estado_juego', estado_personal, to=sid)

@socketio.on('unirse_a_partida')
def manejar_union_partida(data):
    id_partida = data.get('id_partida')
    nombre_jugador = data.get('nombre_jugador')
    if id_partida in partidas_activas:
        join_room(id_partida)
        jugadores_en_partida[request.sid] = {'id_partida': id_partida, 'nombre_jugador': nombre_jugador}
        print(f"Jugador '{nombre_jugador}' se ha conectado a la mesa {id_partida}")
        emitir_actualizacion_a_todos(id_partida)
    else:
        emit('error_juego', {'mensaje': 'La partida ya no existe.'}, to=request.sid)

@socketio.on('jugar_cartas')
def manejar_jugar_cartas(data):
    info_jugador = jugadores_en_partida.get(request.sid, {})
    id_partida = info_jugador.get('id_partida')
    partida = partidas_activas.get(id_partida)
    if not all([id_partida, info_jugador.get('nombre_jugador'), partida]): return
    
    partida.recibir_respuesta_de_jugador(info_jugador['nombre_jugador'], data.get('indices_cartas', []))
    
    if partida.todos_han_jugado():
        partida.estado_partida = 'esperando_seleccion_hdp'
    emitir_actualizacion_a_todos(id_partida)

@socketio.on('hdp_descartar_cartas')
def hdp_descartar_cartas(data):
    info_jugador = jugadores_en_partida.get(request.sid, {})
    id_partida = info_jugador.get('id_partida')
    nombre_jugador = info_jugador.get('nombre_jugador')
    partida = partidas_activas.get(id_partida)

    if not all([id_partida, nombre_jugador, partida]): return
    
    jugador_obj = partida.get_jugador_por_nombre(nombre_jugador)
    if not jugador_obj or not jugador_obj.es_hdp_actual or jugador_obj.ha_jugado_ronda:
        return emit('error_juego', {'mensaje': 'Acción no permitida.'}, to=request.sid)

    indices_cartas = data.get('indices_cartas', [])
    partida.hdp_descartar_y_robar(nombre_jugador, indices_cartas)
    
    emitir_actualizacion_a_todos(id_partida)

@socketio.on('seleccionar_ganador')
def manejar_seleccion_ganador(data):
    info_jugador = jugadores_en_partida.get(request.sid, {})
    id_partida = info_jugador.get('id_partida')
    nombre_hdp = info_jugador.get('nombre_jugador')
    partida = partidas_activas.get(id_partida)
    if not all([id_partida, nombre_hdp, partida]): return
    if partida.get_hdp_actual().nombre != nombre_hdp:
        return emit('error_juego', {'mensaje': 'Solo el HDP puede elegir al ganador.'}, to=request.sid)

    cartas_ganadoras_dicts = data.get('cartas_ganadoras')
    exito = partida.seleccionar_respuesta_ganadora(cartas_ganadoras_dicts)
    
    if exito:
        ganador_ronda = partida.ganador_ronda_anterior
        frase_completa = partida.get_frase_ganadora_formateada(ganador_ronda.respuestas_enviadas)
        info_ronda = {
            'nombre_ganador': ganador_ronda.nombre,
            'puntos_ganador': len(ganador_ronda.cartas_negras_ganadas),
            'frase_completa': frase_completa
        }
        partida.estado_partida = 'fin_ronda'
        socketio.emit('ronda_terminada', info_ronda, to=id_partida)
    else:
        emit('error_juego', {'mensaje': 'Error al seleccionar el ganador.'}, to=request.sid)

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

@socketio.on('enviar_mensaje_chat')
def manejar_chat(data):
    id_partida = data.get('id_partida')
    if id_partida in partidas_activas:
        emit('recibir_mensaje_chat', data, to=id_partida, include_self=True)

@socketio.on('compartir_premio')
def compartir_premio(data):
    id_partida = data.get('id_partida')
    if id_partida in partidas_activas:
        emit('mostrar_premio', data, to=id_partida)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)