"""
Game utilities for battleship - core game logic functions
"""
import random

# Grid settings
GRID_SIZE = 10

def generate_ships():
    """Generate random ship positions for a new game"""
    ship_sizes = [5, 4, 3, 3, 2]
    ships = []
    for ship_size in ship_sizes:
        placed = False
        attempts = 0
        while not placed and attempts < 100:
            start_row = random.randint(0, GRID_SIZE - 1)
            start_col = random.randint(0, GRID_SIZE - 1)
            orientation = random.randint(0, 1)
            if is_valid_placement(ships, start_row, start_col, ship_size, orientation):
                ship_coords = []
                for i in range(ship_size):
                    if orientation == 0:
                        ship_coords.append((start_row, start_col + i))
                    else:
                        ship_coords.append((start_row + i, start_col))
                ships.append(ship_coords)
                placed = True
            attempts += 1
    return ships

def is_valid_placement(existing_ships, start_row, start_col, ship_size, orientation):
    """Check if a ship placement is valid (doesn't overlap with existing ships)"""
    if orientation == 0 and start_col + ship_size > GRID_SIZE:
        return False
    if orientation == 1 and start_row + ship_size > GRID_SIZE:
        return False
    new_ship_coords = [(start_row, start_col + i) if orientation == 0 else (start_row + i, start_col) for i in range(ship_size)]
    for ship in existing_ships:
        if any(c in new_ship_coords for c in ship):
            return False
    return True

def get_grid_pos(mouse_x, mouse_y, grid_x, grid_y, cell_size, grid_width, grid_height):
    """Convert mouse coordinates to grid position"""
    if grid_x <= mouse_x <= grid_x + grid_width and grid_y <= mouse_y <= grid_y + grid_height:
        col = (mouse_x - grid_x) // cell_size
        row = (mouse_y - grid_y) // cell_size
        return row, col
    return None

def is_hit(row, col, ships):
    """Check if a shot at (row, col) hits any ship"""
    return any((row, col) in ship for ship in ships)

def all_ships_sunk(ships, hits):
    """Check if all ships have been sunk"""
    return all(all(coord in hits for coord in ship) for ship in ships)

def create_board(n=GRID_SIZE):
    return [[0 for _ in range(n)] for _ in range(n)]

def can_place_ship(occupied, x, y, ship_len, horizontal):
    n = len(occupied)
    if horizontal:
        if y + ship_len > n: return False
        for k in range(ship_len):
            if occupied[x][y + k] == 1: return False
    else:
        if x + ship_len > n: return False
        for k in range(ship_len):
            if occupied[x + k][y] == 1: return False
    return True

def mark_ship_positions(board, occupied, ship_len):
    n = len(board)
    for i in range(n):
        for j in range(n - ship_len + 1):
            if can_place_ship(occupied, i, j, ship_len, True):
                for k in range(ship_len):
                    board[i][j + k] += 1
    for i in range(n - ship_len + 1):
        for j in range(n):
            if can_place_ship(occupied, i, j, ship_len, False):
                for k in range(ship_len):
                    board[i + k][j] += 1

def target_shot(current_hits, occupied):
    directions = [(-1,0),(1,0),(0,-1),(0,1)]
    n = len(occupied)
    if not current_hits: return None
    if len(current_hits) == 1:
        r,c = current_hits[0]
        for dr,dc in directions:
            nr,nc = r+dr, c+dc
            if 0 <= nr < n and 0 <= nc < n and occupied[nr][nc]==0:
                return (nr,nc)
    else:
        r0,c0 = current_hits[0]
        r1,c1 = current_hits[1]
        if r0 == r1:  # horizontal
            row = r0
            min_c = min(c for _,c in current_hits)-1
            max_c = max(c for _,c in current_hits)+1
            if 0 <= min_c < n and occupied[row][min_c]==0: return (row,min_c)
            if 0 <= max_c < n and occupied[row][max_c]==0: return (row,max_c)
        else:  # vertical
            col = c0
            min_r = min(r for r,_ in current_hits)-1
            max_r = max(r for r,_ in current_hits)+1
            if 0 <= min_r < n and occupied[min_r][col]==0: return (min_r,col)
            if 0 <= max_r < n and occupied[max_r][col]==0: return (max_r,col)
    # fallback adjacent
    for r,c in current_hits:
        for dr,dc in directions:
            nr,nc = r+dr, c+dc
            if 0 <= nr < n and 0 <= nc < n and occupied[nr][nc]==0:
                return (nr,nc)
    return None

def player_ships_flat():
    coords = set()
    for ship in player_ships:
        coords.update(ship)
    return coords

def reset_game():
    """Reset the game state for a new game"""
    global player_ships, enemy_ships, player_hits, player_misses
    global enemy_hits, enemy_misses, occupied, current_hits, mode
    global player_turn, game_over, winner
    
    player_ships = generate_ships()
    enemy_ships = generate_ships()
    player_hits = set()
    player_misses = set()
    enemy_hits = set()
    enemy_misses = set()
    occupied = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    current_hits = []
    mode = "hunt"
    player_turn = True
    game_over = False
    winner = None