#!/usr/bin/env python3
import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _AQUI]

import argparse
import time
from datetime import datetime

try:
    import chess
    import chess.polyglot
    if not hasattr(chess, "Board"):
        raise ImportError
except ImportError:
    print("Biblioteca python-chess nao encontrada. Rode: pip install -r requirements.txt")
    sys.exit(1)

MATE = 100000
INF = 10 ** 9
EXACT, LOWER, UPPER = 0, 1, 2

VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

PAWN_T = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
]
KNIGHT_T = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]
BISHOP_T = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
ROOK_T = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0,
]
QUEEN_T = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
]
KING_MID_T = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
]
KING_END_T = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]
PST = {
    chess.PAWN: PAWN_T,
    chess.KNIGHT: KNIGHT_T,
    chess.BISHOP: BISHOP_T,
    chess.ROOK: ROOK_T,
    chess.QUEEN: QUEEN_T,
}


def evaluate(board):
    """Pontuacao do ponto de vista de quem joga (positivo = bom para quem joga)."""
    pieces = board.piece_map()
    material = 0
    for p in pieces.values():
        if p.piece_type not in (chess.PAWN, chess.KING):
            material += VALUES[p.piece_type]
    endgame = material < 2600

    score = 0
    for sq, p in pieces.items():
        idx = sq ^ 56 if p.color == chess.WHITE else sq
        if p.piece_type == chess.KING:
            table = KING_END_T if endgame else KING_MID_T
        else:
            table = PST[p.piece_type]
        v = VALUES[p.piece_type] + table[idx]
        score += v if p.color == chess.WHITE else -v

    for color in (chess.WHITE, chess.BLACK):
        if len(board.pieces(chess.BISHOP, color)) >= 2:
            score += 30 if color == chess.WHITE else -30

    return score if board.turn == chess.WHITE else -score


class Timeout(Exception):
    pass


class Engine:
    def __init__(self):
        self.tt = {}
        self.nodes = 0
        self.deadline = 0.0
        self.prev_best = None

    # ordenacao
    def order(self, board, tt_move=None):
        def key(m):
            if m == tt_move:
                return 10 ** 7
            s = 0
            if board.is_capture(m):
                victim = board.piece_type_at(m.to_square) or chess.PAWN
                attacker = board.piece_type_at(m.from_square)
                s += 10000 + 10 * VALUES[victim] - VALUES[attacker]
            if m.promotion:
                s += 9000 + VALUES[m.promotion]
            if board.gives_check(m):
                s += 50
            return s

        return sorted(board.legal_moves, key=key, reverse=True)

    # busca de quietude
    def quiesce(self, board, alpha, beta, ply):
        self.nodes += 1
        if self.nodes & 2047 == 0 and time.time() > self.deadline:
            raise Timeout
        stand = evaluate(board)
        if stand >= beta:
            return stand
        if stand > alpha:
            alpha = stand
        if ply > 40:
            return alpha

        def mvv(m):
            victim = board.piece_type_at(m.to_square) or chess.PAWN
            attacker = board.piece_type_at(m.from_square)
            return 10 * VALUES[victim] - VALUES[attacker] + (VALUES[m.promotion] if m.promotion else 0)

        caps = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
        caps.sort(key=mvv, reverse=True)
        for m in caps:
            board.push(m)
            sc = -self.quiesce(board, -beta, -alpha, ply + 1)
            board.pop()
            if sc >= beta:
                return sc
            if sc > alpha:
                alpha = sc
        return alpha

    # busca principal
    def negamax(self, board, depth, alpha, beta, ply):
        self.nodes += 1
        if self.nodes & 2047 == 0 and time.time() > self.deadline:
            raise Timeout

        if ply > 0 and (
            board.is_repetition(2)
            or board.halfmove_clock >= 100
            or board.is_insufficient_material()
        ):
            return 0

        alpha0, beta0 = alpha, beta
        key = chess.polyglot.zobrist_hash(board)
        entry = self.tt.get(key)
        tt_move = None
        if entry is not None:
            d, flag, sc, mv = entry
            tt_move = mv
            if d >= depth and ply > 0:
                if flag == EXACT:
                    return sc
                if flag == LOWER:
                    alpha = max(alpha, sc)
                else:
                    beta = min(beta, sc)
                if alpha >= beta:
                    return sc

        in_check = board.is_check()
        if in_check and ply < 20:
            depth += 1
        if depth <= 0:
            return self.quiesce(board, alpha, beta, ply)

        moves = self.order(board, tt_move)
        if not moves:
            return -MATE + ply if in_check else 0

        best = -INF
        best_move = None
        for m in moves:
            board.push(m)
            sc = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()
            if sc > best:
                best, best_move = sc, m
            if sc > alpha:
                alpha = sc
            if alpha >= beta:
                break

        if best <= alpha0:
            flag = UPPER
        elif best >= beta0:
            flag = LOWER
        else:
            flag = EXACT
        if len(self.tt) > 2_000_000:
            self.tt.clear()
        self.tt[key] = (depth, flag, best, best_move)
        return best

    def root(self, board, depth):
        alpha, beta = -INF, INF
        best, best_score = None, -INF
        for m in self.order(board, self.prev_best):
            board.push(m)
            sc = -self.negamax(board, depth - 1, -beta, -alpha, 1)
            board.pop()
            if sc > best_score:
                best, best_score = m, sc
            if sc > alpha:
                alpha = sc
        return best, best_score

    def search(self, board, seconds, max_depth=64):
        """Retorna (lance, pontuacao, profundidade, nos)."""
        start = time.time()
        self.deadline = start + seconds
        self.nodes = 0
        self.prev_best = None
        legal = list(board.legal_moves)
        if len(legal) == 1:
            return legal[0], 0, 0, 0

        best_move, best_score, reached = None, 0, 0
        for depth in range(1, max_depth + 1):
            try:
                move, score = self.root(board.copy(), depth)
            except Timeout:
                break
            best_move, best_score, reached = move, score, depth
            self.prev_best = move
            if abs(score) > MATE - 100:
                break
            if time.time() - start > seconds * 0.5:
                break

        if best_move is None:
            best_move = self.order(board)[0]
        return best_move, best_score, reached, self.nodes


# variante principal
def principal_variation(eng, board, first_move, max_len=10):
    """PV: lance escolhido + continuacao guardada na tabela de transposicao."""
    b = board.copy()
    pv = [first_move]
    b.push(first_move)
    seen = set()
    while len(pv) < max_len:
        key = chess.polyglot.zobrist_hash(b)
        entry = eng.tt.get(key)
        if key in seen or entry is None or entry[3] is None or entry[3] not in b.legal_moves:
            break
        seen.add(key)
        pv.append(entry[3])
        b.push(entry[3])
    return pv


# tabuleiro no terminal
GLIFOS = {chess.PAWN: "♟", chess.KNIGHT: "♞", chess.BISHOP: "♝",
          chess.ROOK: "♜", chess.QUEEN: "♛", chess.KING: "♚"}
NOMES = {chess.PAWN: "peao", chess.KNIGHT: "cavalo", chess.BISHOP: "bispo",
         chess.ROOK: "torre", chess.QUEEN: "dama", chess.KING: "rei"}


FUNDO_CLARO, FUNDO_ESCURO = 180, 137
DEST_CLARO, DEST_ESCURO = 229, 185     
FUNDO_XEQUE = 160
PECA_BRANCA, PECA_PRETA = 231, 16


def cor(fundo, frente=None, negrito=False):
    s = f"\x1b[48;5;{fundo}m"
    if frente is not None:
        s += f"\x1b[38;5;{frente}m"
    if negrito:
        s += "\x1b[1m"
    return s


RESET = "\x1b[0m"


def desenhar_tabuleiro(board, virar, ultimo, simples):
    """Devolve as linhas do tabuleiro. 'virar' mostra do lado das pretas."""
    colunas = list(range(7, -1, -1)) if virar else list(range(8))
    linhas_ = list(range(8)) if virar else list(range(7, -1, -1))
    rei_xeque = board.king(board.turn) if board.is_check() else None
    marcadas = {ultimo.from_square, ultimo.to_square} if ultimo else set()
    out = []

    if simples:
        out.append("     " + "  ".join(chess.FILE_NAMES[c] for c in colunas))
        for r in linhas_:
            cel = []
            for c in colunas:
                p = board.piece_at(chess.square(c, r))
                cel.append(p.symbol() if p else ".")
            out.append(f"  {r + 1}  " + "  ".join(cel) + f"  {r + 1}")
        out.append("     " + "  ".join(chess.FILE_NAMES[c] for c in colunas))
        out.append("  MAIUSCULA = brancas | minuscula = pretas | . = vazia")
        return out

    def letras():
        return "    " + "".join(f"  {chess.FILE_NAMES[c]}  " for c in colunas)

    out.append(letras())
    for r in linhas_:
        for sub in (0, 1):
            linha = f" {r + 1} " if sub == 0 else "   "
            for c in colunas:
                sq = chess.square(c, r)
                clara = (c + r) % 2 == 1
                if sq == rei_xeque:
                    fundo = FUNDO_XEQUE
                elif sq in marcadas:
                    fundo = DEST_CLARO if clara else DEST_ESCURO
                else:
                    fundo = FUNDO_CLARO if clara else FUNDO_ESCURO
                p = board.piece_at(sq)
                if sub == 0 and p:
                    f = PECA_BRANCA if p.color == chess.WHITE else PECA_PRETA
                    linha += cor(fundo, f, True) + f"  {GLIFOS[p.piece_type]}  " + RESET
                else:
                    linha += cor(fundo) + "     " + RESET
            if sub == 0:
                linha += f" {r + 1}"
            out.append(linha)
    out.append(letras())
    return out


def descrever_lance(board, move):
    """Explica o lance em portugues para mover no tabuleiro fisico."""
    de, para = chess.square_name(move.from_square), chess.square_name(move.to_square)
    peca = board.piece_at(move.from_square)
    nome = NOMES[peca.piece_type]
    if board.is_castling(move):
        curto = chess.square_file(move.to_square) > chess.square_file(move.from_square)
        r = chess.square_rank(move.from_square) + 1
        if curto:
            txt = f"ROQUE CURTO: rei de e{r} para g{r} e torre de h{r} para f{r}"
        else:
            txt = f"ROQUE LONGO: rei de e{r} para c{r} e torre de a{r} para d{r}"
    else:
        txt = f"mova o {nome} de {de} para {para}"
        if board.is_en_passant(move):
            cap = chess.square_name(chess.square(chess.square_file(move.to_square),
                                                 chess.square_rank(move.from_square)))
            txt += f" (en passant: retire tambem o peao de {cap})"
        elif board.is_capture(move):
            txt += f" (captura {NOMES[board.piece_type_at(move.to_square)]})"
        if move.promotion:
            txt += f" e PROMOVA para {NOMES[move.promotion]}"
    board.push(move)
    if board.is_checkmate():
        txt += "  -> XEQUE-MATE!"
    elif board.is_check():
        txt += "  -> xeque!"
    board.pop()
    return txt


# utilitarios
def parse_move(board, text):
    """Aceita UCI (e2e4, e7e8q) e tambem notacao algebrica (Nf3, O-O)."""
    text = text.strip()
    try:
        m = chess.Move.from_uci(text.lower())
        if m in board.legal_moves:
            return m
    except ValueError:
        pass
    try:
        return board.parse_san(text)
    except ValueError:
        return None


def move_budget(clock, increment, max_seconds, overhead):
    """Tempo (s) para pensar neste lance: fracao do relogio + parte do incremento."""
    usable = max(0.0, clock - overhead)
    budget = usable / 35 + increment * 0.8
    return max(0.3, min(budget, usable * 0.2, max_seconds))


def log_line(f, text):
    f.write(text + "\n")
    f.flush()


def fmt_clock(clock):
    clock = max(0, clock)
    return f"{int(clock // 60)}:{int(clock % 60):02d}"


AJUDA = [
    "Comandos:",
    "  e2e4      lance do adversario em UCI (de-para; promocao: e7e8q)",
    "  desfazer  volta o ultimo lance nosso e o do adversario",
    "  tempo 600 acerta o nosso relogio (segundos restantes)",
    "  sair      encerra a partida",
]


def mostrar_tela(board, engine_color, ultimo, clock, mensagens, simples, limpar):
    if limpar:
        print("\x1b[2J\x1b[H", end="")
    lado = "BRANCAS" if engine_color == chess.WHITE else "PRETAS"
    print(f"=== CHESS CHALLENGE III === Nosso time joga de {lado} "
          f"(tabuleiro visto do nosso lado)\n")
    for linha in desenhar_tabuleiro(board, engine_color == chess.BLACK, ultimo, simples):
        print(linha)
    vez = "BRANCAS" if board.turn == chess.WHITE else "PRETAS"
    print(f"\n  Vez das {vez}   |   Nosso relogio: {fmt_clock(clock)}"
          + ("   <<< POUCO TEMPO!" if clock < 60 else ""))
    if board.move_stack:
        ultimos = []
        tmp = chess.Board()
        for m in board.move_stack:
            ultimos.append(m.uci())
        print("  Ultimos lances: " + " ".join(ultimos[-8:]))
    print()
    for m in mensagens:
        print(m)


def play(engine_color, minutes, increment, max_seconds, overhead, log_path,
         read=None, simples=False, limpar=False):
    """Joga uma partida. 'read(board)' devolve o texto do lance do adversario."""
    if read is None:
        read = lambda board: input("  Lance do adversario (UCI, ex: e2e4) > ").strip()

    board = chess.Board()
    eng = Engine()
    clock = minutes * 60
    mensagens = list(AJUDA)
    ultimo = None

    with open(log_path, "a", encoding="utf-8") as log:
        cor_txt = "brancas" if engine_color == chess.WHITE else "pretas"
        log_line(log, f"# Chess Challenge III | motor joga de {cor_txt} | "
                      f"relogio {minutes:g}min + {increment:g}s/lance")
        log_line(log, "# aval = centipeoes (pontos/100) do ponto de vista de quem joga")

        while not board.is_game_over(claim_draw=True):
            mostrar_tela(board, engine_color, ultimo, clock, mensagens, simples, limpar)
            mensagens = []

            if board.turn == engine_color:
                budget = move_budget(clock, increment, max_seconds, overhead)
                print(f"  Pensando (ate {budget:.0f}s)...")
                t0 = time.time()
                try:
                    move, score, depth, nodes = eng.search(board, budget)
                except Exception as exc:  # nunca travar: joga um lance legal
                    log_line(log, f"# ERRO na busca: {exc!r} - lance de emergencia")
                    move, score, depth, nodes = eng.order(board)[0], 0, 0, 0
                elapsed = time.time() - t0
                pv = principal_variation(eng, board, move)
                clock = clock - elapsed - overhead + increment

                cor_lance = "brancas" if board.turn == chess.WHITE else "pretas"
                log_line(
                    log,
                    f"lance={board.fullmove_number} cor={cor_lance} uci={move.uci()} "
                    f"prof={depth} nos={nodes} aval={score / 100:+.2f} "
                    f"pv={' '.join(m.uci() for m in pv)} tempo={elapsed:.2f}s",
                )
                mensagens = [
                    "  ############################################",
                    f"  #  NOSSO LANCE (diga em voz alta):  {move.uci()}",
                    "  ############################################",
                    f"  Como mover: {descrever_lance(board, move)}",
                    "  Depois: mova a peca no tabuleiro e aperte o relogio.",
                    f"  (profundidade {depth}, avaliacao {score / 100:+.2f} para nos)",
                ]
                board.push(move)
                ultimo = move
            else:
                txt = read(board).strip()
                if txt in ("sair", "quit", "q"):
                    log_line(log, "# partida encerrada manualmente")
                    return board
                if txt in ("ajuda", "?", "help"):
                    mensagens = list(AJUDA)
                    continue
                if txt == "desfazer":
                    for _ in range(2):
                        if board.move_stack:
                            board.pop()
                    ultimo = board.move_stack[-1] if board.move_stack else None
                    log_line(log, "# ultimos lances desfeitos (correcao manual)")
                    mensagens = ["  Lances desfeitos."]
                    continue
                if txt.startswith("tempo"):
                    try:
                        clock = float(txt.split()[1])
                        mensagens = [f"  Relogio ajustado para {fmt_clock(clock)}."]
                    except (IndexError, ValueError):
                        mensagens = ["  Use assim: tempo 600  (segundos que sobram)"]
                    continue
                m = parse_move(board, txt)
                if m is None:
                    mensagens = ["  Lance invalido ou ilegal. Digite em UCI: "
                                 "casa de origem + destino, ex: e2e4, g1f3, e7e8q"]
                    continue
                log_line(log, f"adversario lance={board.fullmove_number} uci={m.uci()}")
                board.push(m)
                ultimo = m

        result = board.result(claim_draw=True)
        mostrar_tela(board, engine_color, ultimo, clock, [], simples, limpar)
        print("  FIM DE JOGO:", result, "-", board.outcome(claim_draw=True))
        log_line(log, f"# resultado: {result}")
    return board


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=25, help="relogio do nosso lado (min)")
    ap.add_argument("--increment", type=float, default=0, help="incremento por lance (s)")
    ap.add_argument("--max-seconds", type=float, default=20, help="teto de tempo por lance (s)")
    ap.add_argument("--overhead", type=float, default=6,
                    help="segundos gastos por lance anunciando/digitando (descontados do relogio)")
    ap.add_argument("--simples", action="store_true",
                    help="tabuleiro so com letras, sem cores (se o terminal nao suportar)")
    ap.add_argument("--log", default=None, help="arquivo de log (padrao: log_partida_<data>.txt)")
    args = ap.parse_args()

    if os.name == "nt":
        os.system("")  # ativa cores ANSI no terminal do Windows

    ans = ""
    while ans not in ("b", "p"):
        ans = input("O nosso time joga de (b)rancas ou (p)retas? ").strip().lower()[:1]
    engine_color = chess.WHITE if ans == "b" else chess.BLACK

    log_path = args.log or f"log_partida_{datetime.now():%Y%m%d_%H%M%S}.txt"
    print(f"Log desta partida: {log_path}")
    play(engine_color, args.minutes, args.increment, args.max_seconds, args.overhead,
         log_path, simples=args.simples, limpar=sys.stdout.isatty() and not args.simples)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
