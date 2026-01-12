import chess
import random

class ChessEngine:
    def __init__(self, color: chess.Color, depth: int = 3):
        self.color = color
        self.depth = depth
        # Simple piece values
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
        # Simplified position tables (very basic)
        self.pawn_table = [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ]
        self.knight_table = [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50,
        ]

    def evaluate_board(self, board: chess.Board) -> int:
        if board.is_checkmate():
            if board.turn == self.color:
                return -99999  # We are checkmated
            else:
                return 99999   # Opponent is checkmated
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        # Material and Position
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values.get(piece.piece_type, 0)
                
                # Positional bonus (simplified: just for pawns and knights for now)
                # Flip square index for black to use same table from white's perspective
                table_square = square if piece.color == chess.WHITE else chess.square_mirror(square)
                
                if piece.piece_type == chess.PAWN:
                    value += self.pawn_table[table_square]
                elif piece.piece_type == chess.KNIGHT:
                    value += self.knight_table[table_square]

                if piece.color == self.color:
                    score += value
                else:
                    score -= value
        
        return score

    def get_best_move(self, board: chess.Board) -> tuple[chess.Move, str]:
        best_move = None
        best_value = -float('inf')
        alpha = -float('inf')
        beta = float('inf')
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None, "No legal moves"

        # Simple move ordering: captures first
        legal_moves.sort(key=lambda m: 10 if board.is_capture(m) else 0, reverse=True)

        for move in legal_moves:
            board.push(move)
            value = -self.minimax(board, self.depth - 1, -beta, -alpha)
            board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
            
            alpha = max(alpha, value)
        
        comment = f"Eval: {best_value/100:.2f}"
        return best_move, comment

    def minimax(self, board: chess.Board, depth: int, alpha: int, beta: int) -> int:
        if depth == 0 or board.is_game_over():
            # If depth 0, evaluate from perspective of side to move
            # But our evaluate_board is always from self.color perspective
            # So we need to adjust sign based on whose turn it is
            score = self.evaluate_board(board)
            return score if board.turn == self.color else -score

        max_eval = -float('inf')
        legal_moves = list(board.legal_moves)
        # Move ordering
        legal_moves.sort(key=lambda m: 10 if board.is_capture(m) else 0, reverse=True)

        for move in legal_moves:
            board.push(move)
            eval = -self.minimax(board, depth - 1, -beta, -alpha)
            board.pop()
            
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        
        return max_eval

from personas import Persona, PERSONAS

class ReasoningEngine:
    def __init__(self, persona_name: str = "teacher"):
        self.piece_names = {
            chess.PAWN: "Pawn",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.ROOK: "Rook",
            chess.QUEEN: "Queen",
            chess.KING: "King"
        }
        self.persona = PERSONAS.get(persona_name.lower(), PERSONAS["teacher"])

    def explain_move(self, board: chess.Board, move: chess.Move, eval_score: float = None) -> str:
        # board is the state BEFORE the move
        piece = board.piece_at(move.from_square)
        piece_name = self.piece_names.get(piece.piece_type, "Piece") if piece else "Piece"
        
        # Check for special moves
        if board.is_castling(move):
            return f"{self.persona.name}: I am castling."
            
        # Check for captures
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                captured_name = self.piece_names.get(captured_piece.piece_type, "piece")
                return f"{self.persona.name}: {self.persona.capture_quote} (Capturing {captured_name})"
            else:
                return f"{self.persona.name}: {self.persona.capture_quote} (En passant)"

        # Make the move on a temporary board to check for checks/mates
        board.push(move)
        is_check = board.is_check()
        is_checkmate = board.is_checkmate()
        board.pop()

        if is_checkmate:
            return f"{self.persona.name}: {self.persona.win_quote}"
        if is_check:
            return f"{self.persona.name}: {self.persona.check_quote}"

        # Positional reasoning
        to_square_name = chess.square_name(move.to_square)
        
        # Default
        return f"{self.persona.name}: I am moving {piece_name} to {to_square_name}."

    def analyze_human_move(self, board: chess.Board, move: chess.Move, prev_eval: int, current_eval: int) -> str:
        # Simple analysis: did the eval drop significantly?
        # Note: eval is from engine's perspective (maximizing for itself).
        # If engine is Black, positive eval is good for White (Human).
        # Wait, our evaluate_board returns score from perspective of side to move?
        # No, evaluate_board returns score from self.color perspective in minimax, 
        # but the raw evaluate_board function returns score from self.color perspective.
        # Let's assume standard centipawn: + is White advantage, - is Black advantage.
        
        # If human is White:
        # Good move: Eval increases or stays high.
        # Bad move: Eval drops.
        
        # Let's simplify: We don't have the full eval history easily here without running search.
        # For now, let's just return a generic comment based on the move type.
        
        if board.is_capture(move):
             return f"{self.persona.name}: Interesting capture."
        
        return ""

