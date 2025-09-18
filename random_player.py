import sys
import time
import random
import copy


TIME_LIMIT = 1.0


VALID_SPACES = [
    "a1", "d1", "g1",
    "b2", "d2", "f2",
    "c3", "d3", "e3",
    "a4", "b4", "c4", "e4", "f4", "g4",
    "c5", "d5", "e5",
    "b6", "d6", "f6",
    "a7", "d7", "g7"
]

ADJACENCY = {
    "a1": ["d1", "a4"],
    "d1": ["a1", "g1", "d2"],
    "g1": ["d1", "g4"],
    "b2": ["d2", "b4"],
    "d2": ["b2", "f2", "d1", "d3"],
    "f2": ["d2", "f4"],
    "c3": ["d3", "c4"],
    "d3": ["c3", "e3", "d2"],
    "e3": ["d3", "e4"],
    "a4": ["a1", "a7", "b4"],
    "b4": ["a4", "c4", "b2", "b6"],
    "c4": ["b4", "c3", "c5"],
    "g4": ["g1", "g7", "f4"],
    "f4": ["g4", "f2", "f6", "e4"],
    "e4": ["e3", "e5", "f4"],
    "a7": ["a4", "d7"],
    "d7": ["a7", "g7", "d6"],
    "g7": ["d7", "g4"],
    "b6": ["b4", "d6"],
    "d6": ["b6", "f6", "d7", "d5"],
    "f6": ["d6", "f4"],
    "c5": ["c4", "d5"],
    "d5": ["c5", "e5", "d6"],
    "e5": ["d5", "e4"]
}

MILLS = [
    ["a1", "d1", "g1"],
    ["a7", "d7", "g7"],
    ["b2", "d2", "f2"],
    ["b6", "d6", "f6"],
    ["c3", "d3", "e3"],
    ["c5", "d5", "e5"],
    ["a1", "a4", "a7"],
    ["g1", "g4", "g7"],
    ["b2", "b4", "b6"],
    ["f2", "f4", "f6"],
    ["c3", "c4", "c5"],
    ["e3", "e4", "e5"],
    ["d1", "d2", "d3"],
    ["d5", "d6", "d7"],
    ["a4", "b4", "c4"],
    ["e4", "f4", "g4"]
]

def log_debug(message):
    with open("randomdebug.txt", "a") as f:
        f.write(message + "\n")

def initial_state():
    state = {
        "board": {pos: None for pos in VALID_SPACES},
        "hand": {"blue": 10, "orange": 10},
        "mill_counter": 0,
        "turn": None
    }
    return state

def forms_mill(board, pos, color):
    for mill in MILLS:
        if pos in mill:
            if all(board[p] == color or p == pos for p in mill):
                if all((p == pos) or (board[p] == color) for p in mill):
                    return True
    return False

def get_mill_removals(state, opponent_color):
    board = state["board"]
    candidates = [pos for pos, occ in board.items() if occ == opponent_color and not forms_mill(board, pos, opponent_color)]
    if candidates:
        return candidates
    return [pos for pos, occ in board.items() if occ == opponent_color]

def copy_state(state):
    return {
        "board": state["board"].copy(),
        "hand": state["hand"].copy(),
        "mill_counter": state["mill_counter"],
        "turn": state["turn"]
    }

def change_turn(state):
    state["turn"] = "blue" if state["turn"] == "orange" else "orange"

def count_board_pieces(state, color):
    return sum(1 for occ in state["board"].values() if occ == color)

def generate_moves(state, color):
    moves = []
    board = state["board"]
    opponent_color = "blue" if color == "orange" else "orange"
    pieces_on_board = count_board_pieces(state, color)
    
    if state["hand"][color] > 0:
        for pos in VALID_SPACES:
            if board[pos] is None:
                new_board = board.copy()
                new_board[pos] = color
                mill_formed = forms_mill(new_board, pos, color)
                if mill_formed:
                    removals = get_mill_removals(state, opponent_color)
                    for rem in removals:
                        moves.append(("h", pos, rem))
                else:
                    moves.append(("h", pos, "r0"))
    
    player_positions = [pos for pos, occ in board.items() if occ == color]
    for src in player_positions:
        if pieces_on_board == 3 and state["hand"][color] == 0:
            possible_dests = [p for p in VALID_SPACES if board[p] is None]
        else:
            possible_dests = [p for p in ADJACENCY[src] if board[p] is None]
        for dest in possible_dests:
            new_board = board.copy()
            new_board[src] = None
            new_board[dest] = color
            mill_formed = forms_mill(new_board, dest, color)
            if mill_formed:
                removals = get_mill_removals(state, opponent_color)
                for rem in removals:
                    moves.append((src, dest, rem))
            else:
                moves.append((src, dest, "r0"))
    return moves

def apply_move(state, move):
    new_state = copy_state(state)
    board = new_state["board"]
    source, dest, removal = move
    color = state["turn"]
    opponent_color = "blue" if color == "orange" else "orange"
    mill_formed = False

    if source.startswith("h"):
        new_state["hand"][color] -= 1
        board[dest] = color
        if forms_mill(board, dest, color):
            mill_formed = True
    else:
        board[source] = None
        board[dest] = color
        if forms_mill(board, dest, color):
            mill_formed = True

    if mill_formed and removal != "r0":
        board[removal] = None
        new_state["mill_counter"] = 0
    else:
        new_state["mill_counter"] += 1

    change_turn(new_state)
    return new_state

def is_terminal(state):
    for color in ["blue", "orange"]:
        if count_board_pieces(state, color) + state["hand"][color] < 3:
            return True
    if not generate_moves(state, state["turn"]):
        return True
    if state["mill_counter"] >= 20:
        return True
    return False

# The main difference from the smart player
def get_random_move(state, player):
    legal_moves = generate_moves(state, state["turn"])
    if not legal_moves:
        return None
    return random.choice(legal_moves)

def parse_move(move_str):
    parts = move_str.strip().split()
    if len(parts) != 3:
        raise ValueError("Invalid move format")
    return tuple(parts)

def move_to_string(move, player_color):
    source, dest, removal = move
    if source == "h":
        source = "h1" if player_color == "blue" else "h2"
    return f"{source} {dest} {removal}"


# def main():
#     player_color = input().strip().lower()
#     opponent_color = "blue" if player_color == "orange" else "orange"
    
#     state = initial_state()
#     state["turn"] = "blue" 
    
#     if player_color == "blue":
#         move = get_random_move(state, player_color)
#         if move is None:
#             sys.exit("No valid move found")
#         state = apply_move(state, move)
#         log_debug("Our move: {} and color {}".format(move, player_color))
#         print(move_to_string(move, player_color), flush=True)
#         log_debug("Our move: {} and color {}".format(move_to_string(move, player_color), player_color))
    
#     while True:
#         try:
#             game_input = input().strip()
#             log_debug("TEST RANDOM {} game input: {}".format(player_color, game_input))
#             if game_input.startswith("END"):
#                 break

#             opp_move = parse_move(game_input)
#             state = apply_move(state, opp_move)

#             if is_terminal(state):
#                 break

#             move = get_random_move(state, player_color)
#             if move is None:
#                 break
#             state = apply_move(state, move)
#             print(move_to_string(move, player_color), flush=True)

#             if is_terminal(state):
#                 break

#         except EOFError:
#             break

# if __name__ == "__main__":
#     main()
