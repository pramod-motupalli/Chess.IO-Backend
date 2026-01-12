from pydantic import BaseModel
from typing import Optional, List

class GameConfig(BaseModel):
    engine_color: str = "black"  # "white" or "black"
    difficulty: str = "medium"   # "easy", "medium", "hard"

class NewGameResponse(BaseModel):
    game_id: str
    board_fen: str
    engine_color: str
    message: str
    legal_moves: Optional[List[dict]] = None

class MoveRequest(BaseModel):
    game_id: str
    from_square: str
    to_square: str
    promotion: Optional[str] = None

class MoveLogItem(BaseModel):
    move_number: int
    white_move: str
    black_move: Optional[str] = None
    engine_comment: Optional[str] = None

class GameStateResponse(BaseModel):
    status: str  # "ok", "illegal_move", "game_over", "error"
    board_fen: str
    game_state: str # "ongoing", "checkmate", "stalemate", "draw"
    winner: Optional[str] = None # "white", "black", "draw", None
    move_log: List[str] # Simplified list of SAN moves for now, or structured
    engine_move: Optional[str] = None
    engine_comment: Optional[str] = None
    message: Optional[str] = None
    legal_moves: Optional[List[dict]] = None # [{"from": "e2", "to": "e4"}, ...]

class SetPersonaRequest(BaseModel):
    game_id: str
    persona: str
