from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import chess
import uuid
from typing import Dict, List
from pydantic import BaseModel
from models import GameConfig, NewGameResponse, MoveRequest, GameStateResponse, SetPersonaRequest
from engine import ChessEngine, ReasoningEngine

app = FastAPI()

# CORS configuration
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory game store
games: Dict[str, dict] = {}

def get_game_state_str(board: chess.Board) -> str:
    if board.is_checkmate():
        return "checkmate"
    if board.is_stalemate():
        return "stalemate"
    if board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return "draw"
    return "ongoing"

def get_winner(board: chess.Board) -> str:
    if board.is_checkmate():
        # If it's checkmate and current turn is White, then Black won
        return "black" if board.turn == chess.WHITE else "white"
    return None

def get_legal_moves_list(board: chess.Board) -> List[dict]:
    moves = []
    for move in board.legal_moves:
        moves.append({
            "from": chess.square_name(move.from_square),
            "to": chess.square_name(move.to_square)
        })
    return moves

@app.post("/new-game", response_model=NewGameResponse)
async def new_game(config: GameConfig):
    game_id = str(uuid.uuid4())
    board = chess.Board()
    
    engine_color_chess = chess.BLACK if config.engine_color.lower() == "black" else chess.WHITE
    
    # Map difficulty to depth
    depth_map = {"easy": 2, "medium": 3, "hard": 4}
    depth = depth_map.get(config.difficulty.lower(), 3)
    
    engine = ChessEngine(color=engine_color_chess, depth=depth)
    
    games[game_id] = {
        "board": board,
        "engine": engine,
        "move_log": [],
        "config": config
    }
    
    message = "Game started. You are White."
    
    # If engine is White, it makes the first move
    if engine_color_chess == chess.WHITE:
        move, comment = engine.get_best_move(board)
        if move:
            board.push(move)
            games[game_id]["move_log"].append(board.peek().uci())
            message = f"Game started. Engine (White) played {move.uci()}."

    return NewGameResponse(
        game_id=game_id,
        board_fen=board.fen(),
        engine_color=config.engine_color,
        message=message,
        legal_moves=get_legal_moves_list(board)
    )

@app.post("/move", response_model=GameStateResponse)
async def make_move(req: MoveRequest):
    if req.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[req.game_id]
    board = game["board"]
    engine = game["engine"]
    
    # 1. Validate Human Move
    try:
        # Handle promotion (default to Queen if not specified but needed)
        # Simple heuristic: if pawn moves to last rank, promote to queen
        move_uci = f"{req.from_square}{req.to_square}"
        move = chess.Move.from_uci(move_uci)
        
        # Check for promotion
        if move not in board.legal_moves:
            # Try adding promotion to queen
            move_uci_promo = move_uci + "q"
            move_promo = chess.Move.from_uci(move_uci_promo)
            if move_promo in board.legal_moves:
                move = move_promo
            else:
                # If still not legal, it's illegal
                pass
        
        if move not in board.legal_moves:
             return GameStateResponse(
                status="illegal_move",
                board_fen=board.fen(),
                game_state=get_game_state_str(board),
                move_log=game["move_log"],
                message="Illegal move",
                legal_moves=get_legal_moves_list(board)
            )
            
        board.push(move)
        game["move_log"].append(move.uci())
        
    except ValueError:
        return GameStateResponse(
            status="error",
            board_fen=board.fen(),
            game_state=get_game_state_str(board),
            move_log=game["move_log"],
            message="Invalid move format",
            legal_moves=get_legal_moves_list(board)
        )

    # 2. Check Game Over after Human Move
    if board.is_game_over():
        return GameStateResponse(
            status="game_over",
            board_fen=board.fen(),
            game_state=get_game_state_str(board),
            winner=get_winner(board),
            move_log=game["move_log"],
            message="Game Over",
            legal_moves=[]
        )

    # 3. Engine Move
    engine_move, eval_comment = engine.get_best_move(board)
    engine_move_uci = None
    engine_comment = eval_comment # Default to eval if no reasoning

    if engine_move:
        # Generate reasoning before pushing the move
        persona_name = game.get("persona", "teacher")
        reasoning_engine = ReasoningEngine(persona_name=persona_name)
        explanation = reasoning_engine.explain_move(board, engine_move)
        engine_comment = f"{explanation} ({eval_comment})"
        
        board.push(engine_move)
        engine_move_uci = engine_move.uci()
        game["move_log"].append(engine_move_uci)
    else:
        # Should be game over if no move found, but double check
        pass

    # 4. Check Game Over after Engine Move
    game_state = get_game_state_str(board)
    winner = get_winner(board)

    return GameStateResponse(
        status="ok",
        board_fen=board.fen(),
        game_state=game_state,
        winner=winner,
        move_log=game["move_log"],
        engine_move=engine_move_uci,
        engine_comment=engine_comment,
        legal_moves=get_legal_moves_list(board)
    )

class SetPersonaRequest(BaseModel):
    game_id: str
    persona: str

@app.post("/set-persona")
async def set_persona(req: SetPersonaRequest):
    if req.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    games[req.game_id]["persona"] = req.persona
    return {"status": "ok", "persona": req.persona}

@app.post("/self-play")
async def self_play(req: SetPersonaRequest):
    # Trigger an engine move for the current side
    if req.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[req.game_id]
    board = game["board"]
    engine = game["engine"]
    
    if board.is_game_over():
        return {"status": "game_over"}

    # Engine makes a move for the current side
    # We need to temporarily set engine color to current turn or just force a move
    # The engine class has a color, but get_best_move calculates for the board.turn
    # However, our minimax implementation might be tied to self.color?
    # Let's check engine.py. 
    # minimax: if depth == 0 or game_over: return score if board.turn == self.color else -score
    # This implies the engine always evaluates from its own perspective.
    # If we want it to play for the other side, we might need a new engine instance or update color.
    
    current_turn = board.turn
    # Create a temporary engine for this turn
    temp_engine = ChessEngine(color=current_turn, depth=engine.depth)
    
    move, eval_comment = temp_engine.get_best_move(board)
    
    if move:
        persona_name = req.persona
        reasoning_engine = ReasoningEngine(persona_name=persona_name)
        explanation = reasoning_engine.explain_move(board, move)
        engine_comment = f"{explanation} ({eval_comment})"
        
        board.push(move)
        game["move_log"].append(move.uci())
        
        return GameStateResponse(
            status="ok",
            board_fen=board.fen(),
            game_state=get_game_state_str(board),
            winner=get_winner(board),
            move_log=game["move_log"],
            engine_move=move.uci(),
            engine_comment=engine_comment,
            legal_moves=get_legal_moves_list(board)
        )
    return {"status": "error", "message": "No move found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
