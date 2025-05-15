import time
import random
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# --- Configuración del Juego ---
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# Definición de los Tetrominós y sus rotaciones
# Cada forma es una lista de listas de (fila, columna) offsets desde un punto pivote
TETROMINOES = {
    'I': {
        'shape': [[[1, 1, 1, 1]], [[1], [1], [1], [1]]],
        'color': 'I'  # Corresponde a la clase CSS
    },
    'L': {
        'shape': [[[0, 0, 1], [1, 1, 1]], [[1, 0], [1, 0], [1, 1]], [[1, 1, 1], [1, 0, 0]], [[1, 1], [0, 1], [0, 1]]],
        'color': 'L'
    },
    'J': {
        'shape': [[[1, 0, 0], [1, 1, 1]], [[1, 1], [1, 0], [1, 0]], [[1, 1, 1], [0, 0, 1]], [[0, 1], [0, 1], [1, 1]]],
        'color': 'J'
    },
    'S': {
        'shape': [[[0, 1, 1], [1, 1, 0]], [[1, 0], [1, 1], [0, 1]]],
        'color': 'S'
    },
    'Z': {
        'shape': [[[1, 1, 0], [0, 1, 1]], [[0, 1], [1, 1], [1, 0]]],
        'color': 'Z'
    },
    'T': {
        'shape': [[[0, 1, 0], [1, 1, 1]], [[1, 0], [1, 1], [1, 0]], [[1, 1, 1], [0, 1, 0]], [[0, 1], [1, 1], [0, 1]]],
        'color': 'T'
    },
    'O': {
        'shape': [[[1, 1], [1, 1]]],
        'color': 'O'
    }
}

# --- Estado del Juego (Global para simplificar, en una app real usarías sesiones o una base de datos) ---
game_state = {}


def init_game():
    global game_state
    board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
    game_state = {
        'board': board,
        'score': 0,
        'level': 1,
        'game_over': False,
        'current_piece': None,
        'piece_x': 0,
        'piece_y': 0,
        'piece_rotation': 0,
        'next_piece_type': random.choice(list(TETROMINOES.keys())),
        'last_fall_time': time.time(),
        'fall_speed': 0.8  # segundos por caída
    }
    spawn_new_piece()


def get_piece_shape(piece_type, rotation):
    return TETROMINOES[piece_type]['shape'][rotation % len(TETROMINOES[piece_type]['shape'])]


def get_piece_color(piece_type):
    return TETROMINOES[piece_type]['color']


def spawn_new_piece():
    global game_state
    if game_state['game_over']:
        return

    game_state['current_piece_type'] = game_state['next_piece_type']
    game_state['next_piece_type'] = random.choice(list(TETROMINOES.keys()))

    game_state['current_piece'] = {
        'type': game_state['current_piece_type'],
        'shape': get_piece_shape(game_state['current_piece_type'], 0),
        'color': get_piece_color(game_state['current_piece_type'])
    }
    game_state['piece_rotation'] = 0
    game_state['piece_x'] = BOARD_WIDTH // 2 - len(game_state['current_piece']['shape'][0]) // 2
    game_state['piece_y'] = 0  # Empezar arriba

    # Comprobar si el juego ha terminado (no hay espacio para la nueva pieza)
    if not is_valid_position(game_state['piece_x'], game_state['piece_y'], game_state['current_piece']['shape']):
        game_state['game_over'] = True


def is_valid_position(x, y, piece_shape):
    for r_offset, row in enumerate(piece_shape):
        for c_offset, cell in enumerate(row):
            if cell:
                board_r, board_c = y + r_offset, x + c_offset
                if not (0 <= board_r < BOARD_HEIGHT and 0 <= board_c < BOARD_WIDTH and \
                        game_state['board'][board_r][board_c] == 0):
                    return False
    return True


def lock_piece():
    global game_state
    piece_shape = game_state['current_piece']['shape']
    piece_color = game_state['current_piece']['color']
    for r_offset, row in enumerate(piece_shape):
        for c_offset, cell in enumerate(row):
            if cell:
                board_r, board_c = game_state['piece_y'] + r_offset, game_state['piece_x'] + c_offset
                if 0 <= board_r < BOARD_HEIGHT and 0 <= board_c < BOARD_WIDTH:  # Seguridad
                    game_state['board'][board_r][board_c] = piece_color  # Usar el color como identificador
    clear_lines()
    spawn_new_piece()


def clear_lines():
    global game_state
    lines_cleared = 0
    new_board = [row for row in game_state['board'] if any(cell == 0 for cell in row)]
    lines_cleared = BOARD_HEIGHT - len(new_board)

    if lines_cleared > 0:
        game_state['score'] += (lines_cleared ** 2) * 100  # Puntuación simple
        # Añadir nuevas líneas vacías en la parte superior
        for _ in range(lines_cleared):
            new_board.insert(0, [0 for _ in range(BOARD_WIDTH)])
        game_state['board'] = new_board

        # Ajustar nivel y velocidad
        # Cada 500 puntos, por ejemplo
        new_level = 1 + game_state['score'] // 500
        if new_level > game_state['level']:
            game_state['level'] = new_level
            game_state['fall_speed'] = max(0.1, 0.8 - (game_state['level'] - 1) * 0.05)


def game_tick():
    global game_state
    if game_state['game_over']:
        return

    current_time = time.time()
    if current_time - game_state['last_fall_time'] > game_state['fall_speed']:
        # Mover pieza hacia abajo
        if is_valid_position(game_state['piece_x'], game_state['piece_y'] + 1, game_state['current_piece']['shape']):
            game_state['piece_y'] += 1
        else:
            lock_piece()
        game_state['last_fall_time'] = current_time


# --- Rutas Flask ---
@app.route('/')
def index():
    if not game_state or game_state.get('game_over'):  # Si no hay juego o terminó, iniciar uno nuevo
        init_game()
    return render_template('index.html')


@app.route('/game_state')
def get_game_state():
    if not game_state:  # Asegurarse que el juego esté inicializado
        init_game()

    game_tick()  # Actualizar el juego cada vez que se pide el estado (simplificación)
    # En una app más robusta, esto sería un bucle de juego independiente.

    # Preparamos la pieza actual y la siguiente para el JSON
    current_piece_data = None
    if game_state.get('current_piece'):
        current_piece_data = {
            'shape': game_state['current_piece']['shape'],
            'color': game_state['current_piece']['color']
        }

    next_piece_data = None
    if game_state.get('next_piece_type'):
        next_piece_shape_data = get_piece_shape(game_state['next_piece_type'], 0)  # Usar rotación 0 para preview
        next_piece_data = {
            'shape': next_piece_shape_data,
            'color': get_piece_color(game_state['next_piece_type'])
        }

    return jsonify({
        'board': game_state['board'],
        'score': game_state['score'],
        'level': game_state['level'],
        'game_over': game_state['game_over'],
        'current_piece': current_piece_data,
        'piece_x': game_state.get('piece_x'),
        'piece_y': game_state.get('piece_y'),
        'next_piece': next_piece_data
    })


@app.route('/action', methods=['POST'])
def handle_action():
    if not game_state or game_state.get('game_over', True):  # No procesar acciones si no hay juego o terminó
        if request.json.get('action') == 'start':  # Permitir 'start' para reiniciar
            init_game()
            return jsonify({'status': 'restarted'})
        return jsonify({'status': 'game over or not initialized'}), 400

    action = request.json.get('action')

    if action == 'start' and not game_state.get('current_piece'):  # Primera inicialización
        init_game()
        return jsonify({'status': 'game initialized'})

    if game_state['game_over']:
        return jsonify({'status': 'game over'}), 400

    current_shape = game_state['current_piece']['shape']
    px, py = game_state['piece_x'], game_state['piece_y']

    if action == 'left':
        if is_valid_position(px - 1, py, current_shape):
            game_state['piece_x'] -= 1
    elif action == 'right':
        if is_valid_position(px + 1, py, current_shape):
            game_state['piece_x'] += 1
    elif action == 'down':  # Soft drop
        if is_valid_position(px, py + 1, current_shape):
            game_state['piece_y'] += 1
            game_state['score'] += 1  # Pequeño bonus por bajar manualmente
            game_state['last_fall_time'] = time.time()  # Resetear timer de caída
        else:
            lock_piece()
    elif action == 'rotate':
        new_rotation = (game_state['piece_rotation'] + 1) % len(TETROMINOES[game_state['current_piece_type']]['shape'])
        new_shape = get_piece_shape(game_state['current_piece_type'], new_rotation)
        if is_valid_position(px, py, new_shape):
            game_state['current_piece']['shape'] = new_shape
            game_state['piece_rotation'] = new_rotation
        # Podrías añadir "wall kick" aquí
    elif action == 'drop':  # Hard drop
        while is_valid_position(px, py + 1, game_state['current_piece']['shape']):
            py += 1
            game_state['score'] += 2  # Bonus por hard drop
        game_state['piece_y'] = py
        lock_piece()
        game_state['last_fall_time'] = time.time()

    return jsonify({'status': 'ok'})


@app.route('/restart_game', methods=['POST'])
def restart_game():
    init_game()
    return jsonify({'status': 'game restarted'})


if __name__ == '__main__':
    init_game()  # Inicializa el juego al arrancar el servidor de desarrollo
    app.run(debug=True, host='0.0.0.0', port=5000)