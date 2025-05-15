const BOARD_WIDTH = 10;
const BOARD_HEIGHT = 20;
const gameBoardElement = document.getElementById('game-board');
const scoreElement = document.getElementById('score');
const levelElement = document.getElementById('level');
const nextPieceElement = document.getElementById('next-piece-preview'); // Necesitarás un div para esto en HTML
const gameOverMessageElement = document.getElementById('game-over-message');

let gameLoopInterval;

function createBoard() {
    gameBoardElement.innerHTML = ''; // Limpiar tablero existente
    gameBoardElement.style.gridTemplateColumns = `repeat(${BOARD_WIDTH}, 1fr)`;
    for (let i = 0; i < BOARD_HEIGHT * BOARD_WIDTH; i++) {
        const cell = document.createElement('div');
        cell.classList.add('cell');
        cell.classList.add('empty'); // Clase inicial para celdas vacías
        gameBoardElement.appendChild(cell);
    }
}

function drawBoard(board, currentPiece, pieceX, pieceY) {
    const cells = gameBoardElement.children;
    // 1. Reset all cells to empty or their fixed block color
    for (let r = 0; r < BOARD_HEIGHT; r++) {
        for (let c = 0; c < BOARD_WIDTH; c++) {
            const cellIndex = r * BOARD_WIDTH + c;
            cells[cellIndex].className = 'cell'; // Reset classes
            if (board[r][c] !== 0) {
                cells[cellIndex].classList.add(board[r][c]); // Color del bloque fijado
            } else {
                cells[cellIndex].classList.add('empty');
            }
        }
    }

    // 2. Draw the current falling piece
    if (currentPiece && currentPiece.shape) {
        currentPiece.shape.forEach((row, r_offset) => {
            row.forEach((value, c_offset) => {
                if (value !== 0) {
                    const boardR = pieceY + r_offset;
                    const boardC = pieceX + c_offset;
                    if (boardR >= 0 && boardR < BOARD_HEIGHT && boardC >= 0 && boardC < BOARD_WIDTH) {
                        const cellIndex = boardR * BOARD_WIDTH + boardC;
                         // Sobrescribir clase si hay pieza, incluso si había un bloque fijado (no debería pasar si la lógica de colisión es correcta)
                        cells[cellIndex].className = 'cell';
                        cells[cellIndex].classList.add(currentPiece.color);
                    }
                }
            });
        });
    }
}

// Función para dibujar la vista previa de la siguiente pieza (simplificada)
function drawNextPiece(nextPiece) {
    nextPieceElement.innerHTML = ''; // Limpiar vista previa
    if (nextPiece && nextPiece.shape) {
        nextPieceElement.style.gridTemplateColumns = `repeat(4, 1fr)`; // Asumir max 4 de ancho
        nextPiece.shape.forEach(row => {
            row.forEach(value => {
                const cell = document.createElement('div');
                cell.classList.add('cell');
                if (value !== 0) {
                    cell.classList.add(nextPiece.color);
                } else {
                    cell.classList.add('empty'); // O un color de fondo para la vista previa
                }
                nextPieceElement.appendChild(cell);
            });
        });
    }
}


async function updateGame() {
    try {
        const response = await fetch('/game_state');
        if (!response.ok) {
            console.error("Error fetching game state:", response.status);
            if (gameLoopInterval) clearInterval(gameLoopInterval); // Detener si hay error grave
            return;
        }
        const gameState = await response.json();

        drawBoard(gameState.board, gameState.current_piece, gameState.piece_x, gameState.piece_y);
        scoreElement.textContent = gameState.score;
        levelElement.textContent = gameState.level;
        drawNextPiece(gameState.next_piece);


        if (gameState.game_over) {
            gameOverMessageElement.style.display = 'block';
            if (gameLoopInterval) clearInterval(gameLoopInterval);
            document.removeEventListener('keydown', handleKeyPress); // Detener escucha de teclas
            // Aquí podrías ofrecer un botón de "Jugar de Nuevo"
            const restartButton = document.createElement('button');
            restartButton.textContent = 'Jugar de Nuevo';
            restartButton.onclick = () => {
                fetch('/restart_game', { method: 'POST' })
                    .then(() => window.location.reload()); // O una lógica más sofisticada
            };
            gameOverMessageElement.appendChild(restartButton);
        } else {
            gameOverMessageElement.style.display = 'none';
        }
    } catch (error) {
        console.error("Error in updateGame:", error);
        if (gameLoopInterval) clearInterval(gameLoopInterval);
    }
}

async function sendAction(action) {
    const response = await fetch('/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
    });
    if (response.ok) {
        // El estado se actualizará en el próximo ciclo de updateGame()
        // O podrías forzar una actualización inmediata si es necesario:
        await updateGame();
    } else {
        console.error("Error sending action:", response.status);
    }
}

function handleKeyPress(event) {
    if (gameOverMessageElement.style.display === 'block') return; // No procesar teclas si es game over

    switch (event.key) {
        case 'ArrowLeft':
            sendAction('left');
            break;
        case 'ArrowRight':
            sendAction('right');
            break;
        case 'ArrowDown':
            sendAction('down');
            break;
        case 'ArrowUp': // Rotar
            sendAction('rotate');
            break;
        case ' ': // Espacio para hard drop
            sendAction('drop');
            event.preventDefault(); // Evitar que la página haga scroll
            break;
    }
}

// Iniciar el juego
document.addEventListener('DOMContentLoaded', () => {
    createBoard(); // Crear la estructura del tablero una vez

    // Enviar una acción inicial para configurar el juego si es necesario o obtener el estado
    fetch('/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'start' }) // O simplemente llamar a /game_state
    }).then(() => {
        updateGame(); // Primera actualización para dibujar el estado inicial
        gameLoopInterval = setInterval(updateGame, 200); // Actualizar el estado del juego periódicamente
    });

    document.addEventListener('keydown', handleKeyPress);

    // Controles en pantalla (opcional)
    document.getElementById('btn-left')?.addEventListener('click', () => sendAction('left'));
    document.getElementById('btn-right')?.addEventListener('click', () => sendAction('right'));
    document.getElementById('btn-rotate')?.addEventListener('click', () => sendAction('rotate'));
    document.getElementById('btn-down')?.addEventListener('click', () => sendAction('down'));
    document.getElementById('btn-drop')?.addEventListener('click', () => sendAction('drop'));
});