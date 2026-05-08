import tkinter as tk
import chess



CHECKMATE_SCORE = 1_000_000
PIECE_VALUES = {
    chess.PAWN: 100,   # 3askary
    chess.KNIGHT: 320,  # 7osan
    chess.BISHOP: 330,  #fil
    chess.ROOK: 500,   #tabya
    chess.QUEEN: 900,   #wazir
    chess.KING: 10_000,  #malek
}


def terminal_score(board, ply):
    if board.is_checkmate():
        # Side to move is checkmated.
        return -CHECKMATE_SCORE + ply if board.turn == chess.WHITE else CHECKMATE_SCORE - ply
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    return None

def evaluate(board):
    terminal = terminal_score(board, 0)
    if terminal is not None:
        return terminal

    # Heuristic 1: material
    material = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            value = PIECE_VALUES[piece.piece_type]
            if piece.color == chess.WHITE:
                material += value
            else:
                material -= value

    # Heuristic 2: center control
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    center_bonus = 0
    for sq in center_squares:
        piece = board.piece_at(sq)
        if piece is not None:
            if piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.QUEEN]:
                mult = 5 if piece.color == chess.WHITE else -5
                center_bonus += mult
    # Mobility encourages active positions and faster development.
    white_mobility = len(list(board.legal_moves)) if board.turn == chess.WHITE else 0 
    black_mobility = len(list(board.legal_moves)) if board.turn == chess.BLACK else 0 
    board.push(chess.Move.null()) 
    if board.turn == chess.WHITE:
        white_mobility = len(list(board.legal_moves))
    else:
        black_mobility = len(list(board.legal_moves))
    board.pop()
    mobility_bonus = 2 * (white_mobility - black_mobility)

    check_bonus = 20 if board.is_check() and board.turn == chess.BLACK else 0
    check_bonus -= 20 if board.is_check() and board.turn == chess.WHITE else 0

    return material + center_bonus + mobility_bonus + check_bonus


def move_order_score(board, move):
    score = 0
    if board.is_capture(move):
        captured = board.piece_at(move.to_square)   #3askary
        attacker = board.piece_at(move.from_square)  #fil
        if captured and attacker:
            score += 10 * PIECE_VALUES[captured.piece_type] - PIECE_VALUES[attacker.piece_type]
        else:
            score += 100

    if move.promotion:
        score += PIECE_VALUES.get(move.promotion, 0)

    if board.gives_check(move):
        score += 50

    return score


# =====================================
# 2. ALPHA–BETA SEARCH
# =====================================

BOT_SEARCH_DEPTH = 3

def alpha_beta(board, depth, alpha, beta, is_maximizing, ply=0):
    terminal = terminal_score(board, ply)
    if terminal is not None:
        return terminal

    if depth == 0:
        return evaluate(board)

    # move ordering: captures first
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: move_order_score(board, m), reverse=True)
    
    if is_maximizing:
        max_eval = -float("inf")
        for move in moves:
            board.push(move)
            eval_score = alpha_beta(board, depth - 1, alpha, beta, False, ply + 1)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float("inf")
        for move in moves:
            board.push(move)
            eval_score = alpha_beta(board, depth - 1, alpha, beta, True, ply + 1)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def get_best_move(board, depth=2):
    maximizing_player = board.turn == chess.WHITE
    best_move = None
    best_value = -float("inf") if maximizing_player else float("inf")

    moves = list(board.legal_moves)
    moves.sort(key=lambda m: move_order_score(board, m), reverse=True)

    for move in moves:
        board.push(move)
        val = alpha_beta(board, depth - 1, -float("inf"), float("inf"), not maximizing_player, 1)
        board.pop()

        if maximizing_player:
            if val > best_value:
                best_value = val
                best_move = move
        else:
            if val < best_value:
                best_value = val
                best_move = move

    return best_move


# =====================================
# 3. GUI (tkinter)
# =====================================

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Bot (Alpha_Beta)")
        self.board = chess.Board()
        self.human_color = chess.WHITE
        self.bot_color = chess.BLACK
        self.bot_move_pending = False
        self.selected_square = None
        self.last_bot_move = None
        self.square_size = 60
        self.selected_color = "#4444ff"
        self.valid_move_color = "#00aa33"
        self.check_color = "#ff4d4d"
        self.bot_from_color = "#4da6ff"
        self.bot_to_color = "#ffd24d"

        # Create canvas
        self.canvas = tk.Canvas(
            root,
            width= 8 * self.square_size,
            height=8 * self.square_size,
            bg="white",
        )
        self.canvas.pack(fill="both", expand=True)

        # turn label
        self.status_label = tk.Label(root, text="White to move", font=("Arial", 12))
        self.status_label.pack(pady=5)

        # reset button
        self.button = tk.Button(root, text="Reset Game", command=self.reset_game)
        self.button.pack(pady=5)

        # bind click
        self.canvas.bind("<Button-1>", self.on_click)

        self.draw_board()

    def reset_game(self):
        self.board = chess.Board()
        self.selected_square = None
        self.bot_move_pending = False
        self.last_bot_move = None
        self.draw_board()
        self.update_status()

    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#f0d9b5", "#b58863"]

        # Draw squares
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                x1, y1 = col * self.square_size, row * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="square")

        # Highlight last bot move (from and to squares).
        if self.last_bot_move is not None:
            from_square, to_square = self.last_bot_move
            from_col = chess.square_file(from_square)
            from_row = 7 - chess.square_rank(from_square)
            to_col = chess.square_file(to_square)
            to_row = 7 - chess.square_rank(to_square)

            fx1, fy1 = from_col * self.square_size, from_row * self.square_size
            fx2, fy2 = fx1 + self.square_size, fy1 + self.square_size
            self.canvas.create_rectangle(
                fx1,
                fy1,
                fx2,
                fy2,
                fill=self.bot_from_color,
                stipple="gray50",
                tags="highlight",
            )

            tx1, ty1 = to_col * self.square_size, to_row * self.square_size
            tx2, ty2 = tx1 + self.square_size, ty1 + self.square_size
            self.canvas.create_rectangle(
                tx1,
                ty1,
                tx2,
                ty2,
                fill=self.bot_to_color,
                stipple="gray50",
                tags="highlight",
            )

        # Highlight king square when side to move is in check.
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            if king_square is not None:
                king_col = chess.square_file(king_square)
                king_row = 7 - chess.square_rank(king_square)
                x1, y1 = king_col * self.square_size, king_row * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=self.check_color,
                    stipple="gray50",
                    tags="highlight",
                )

        # Highlight selected square
        if self.selected_square is not None:
            row, col = self.selected_square
            x1, y1 = col * self.square_size, row * self.square_size
            x2, y2 = x1 + self.square_size, y1 + self.square_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.selected_color, stipple="gray50")

            # Show legal move targets as dots.
            from_sq = chess.square(col, 7 - row)
            for move in self.board.legal_moves:
                if move.from_square != from_sq:
                    continue

                target_col = chess.square_file(move.to_square)
                target_row = 7 - chess.square_rank(move.to_square)
                cx = target_col * self.square_size + self.square_size // 2
                cy = target_row * self.square_size + self.square_size // 2
                dot_r = max(6, self.square_size // 10)
                self.canvas.create_oval(
                    cx - dot_r,
                    cy - dot_r,
                    cx + dot_r,
                    cy + dot_r,
                    fill=self.valid_move_color,
                    outline="",
                    tags="highlight",
                )

        # Draw pieces
        piece_syms = {
            "P": "♙",
            "N": "♘",
            "B": "♗",
            "R": "♖",
            "Q": "♕",
            "K": "♔",
            "p": "♟",
            "n": "♞",
            "b": "♝",
            "r": "♜",
            "q": "♛",
            "k": "♚",
        }

        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                if piece is not None:
                    sym = piece_syms[piece.symbol()]
                    x = col * self.square_size + self.square_size // 2
                    y = row * self.square_size + self.square_size // 2
                    self.canvas.create_text(
                        x,
                        y,
                        text=sym,
                        font=("Arial", 32, "bold"),
                        tags="piece",
                    )

        self.update_status()

    def update_status(self):
        if self.board.is_checkmate():
            text = "Game over! Checkmate."
        elif self.board.is_stalemate():
            text = "Stalemate!"
        elif self.board.is_check():
            text = f"{'White' if self.board.turn else 'Black'} in check"
        else:
            text = f"{'White' if self.board.turn else 'Black'} to move"
        self.status_label.config(text=text)

    def on_click(self, event):
        if self.bot_move_pending or self.board.turn != self.human_color:
            return

        col = event.x // self.square_size
        row = event.y // self.square_size

        if not (0 <= col < 8 and 0 <= row < 8):
            return

        square = chess.square(col, 7 - row)

        # if no square selected yet
        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = (row, col)
                self.draw_board()
            return

        # if same square, deselect
        old_row, old_col = self.selected_square
        if row == old_row and col == old_col:
            self.selected_square = None
            self.draw_board()
            return

        # try move
        from_sq = chess.square(old_col, 7 - old_row)
        piece = self.board.piece_at(from_sq)
        try_move = chess.Move(from_sq, square)

        if piece is not None and piece.piece_type == chess.PAWN:
            target_rank = chess.square_rank(square)
            if (piece.color == chess.WHITE and target_rank == 7) or (
                piece.color == chess.BLACK and target_rank == 0
            ):
                try_move = chess.Move(from_sq, square, promotion=chess.QUEEN)

        if try_move in self.board.legal_moves:
            self.board.push(try_move)
            self.selected_square = None
            self.draw_board()
            self.update_status()

            # Bot plays as Black (you can change side)
            if not self.board.is_game_over() and self.board.turn == self.bot_color:
                self.bot_move_pending = True
                self.root.after(500, self.bot_move)

        else:
            # not a legal move, just deselect
            self.selected_square = None
            self.draw_board()

    def bot_move(self):
        self.bot_move_pending = False

        if self.board.is_game_over() or self.board.turn != self.bot_color:
            self.draw_board()
            return

        move = get_best_move(self.board, depth=BOT_SEARCH_DEPTH)
        if move:
            self.last_bot_move = (move.from_square, move.to_square)
            self.board.push(move)
            self.draw_board()
            self.update_status()


# 4. LAUNCH

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()
