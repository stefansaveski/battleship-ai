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

def enhanced_target_shot_multi_ship(current_hits, occupied, enemy_hits, enemy_misses, player_ships):
    """Enhanced target mode that handles multiple adjacent ships by tracking unsunk ship hits"""
    directions = [(-1,0),(1,0),(0,-1),(0,1)]
    n = len(occupied)
    
    if not current_hits: 
        return None, current_hits
    
    # First, remove hits from ships that are already sunk
    unsunk_hits = []
    for hit_pos in current_hits:
        # Check if this hit belongs to a ship that is NOT completely sunk
        for ship in player_ships:
            if hit_pos in ship:
                # If this ship is not completely sunk, keep the hit
                if not all(coord in enemy_hits for coord in ship):
                    unsunk_hits.append(hit_pos)
                break
    
    # Update current_hits to only include hits from unsunk ships
    current_hits = unsunk_hits
    
    if not current_hits:
        return None, current_hits
    
    # If we have multiple hits, determine orientation and prioritize line extensions
    if len(current_hits) >= 2:
        # Sort hits to determine orientation
        sorted_hits = sorted(current_hits)
        r0, c0 = sorted_hits[0]
        r1, c1 = sorted_hits[1]
        
        if r0 == r1:  # horizontal line
            # Try extending the line first
            row = r0
            min_c = min(c for _, c in current_hits)
            max_c = max(c for _, c in current_hits)
            
            # Try extending left
            if min_c > 0 and occupied[row][min_c-1] == 0:
                return (row, min_c-1), current_hits
            # Try extending right
            if max_c < n-1 and occupied[row][max_c+1] == 0:
                return (row, max_c+1), current_hits
                
        elif c0 == c1:  # vertical line
            # Try extending the line first
            col = c0
            min_r = min(r for r, _ in current_hits)
            max_r = max(r for r, _ in current_hits)
            
            # Try extending up
            if min_r > 0 and occupied[min_r-1][col] == 0:
                return (min_r-1, col), current_hits
            # Try extending down
            if max_r < n-1 and occupied[max_r+1][col] == 0:
                return (max_r+1, col), current_hits
    
    # For single hit or when line extensions are blocked, systematically try all neighbors
    # Collect all neighbors of all hit positions from unsunk ships
    all_neighbors = set()
    for r, c in current_hits:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and occupied[nr][nc] == 0:
                all_neighbors.add((nr, nc))
    
    if all_neighbors:
        # Convert to list and sort for consistent behavior
        neighbors_list = sorted(list(all_neighbors))
        return neighbors_list[0], current_hits
    
    # If no valid neighbors found, return None to switch back to hunt mode
    return None, current_hits