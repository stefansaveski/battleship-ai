import pygame
import random

pygame.init()

# -----------------------------
# Window & constants
# -----------------------------
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Battleship")
clock = pygame.time.Clock()
running = True

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 200)
GRAY = (128, 128, 128)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
YELLOW = (200, 200, 0)
PURPLE = (150, 0, 150)
ORANGE = (255, 165, 0)

# Grid settings
GRID_SIZE = 10
CELL_SIZE = 40
GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE
LEFT_GRID_X = 200
RIGHT_GRID_X = 700
GRID_Y = 100

# Game state
player_ships = []
enemy_ships = []
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

# -----------------------------
# Functions
# -----------------------------
def draw_grid(surface, x, y, title):
    font = pygame.font.Font(None, 36)
    text = font.render(title, True, BLACK)
    surface.blit(text, (x, y - 60))
    for i in range(GRID_SIZE + 1):
        pygame.draw.line(surface, BLACK, (x + i * CELL_SIZE, y), (x + i * CELL_SIZE, y + GRID_HEIGHT), 2)
        pygame.draw.line(surface, BLACK, (x, y + i * CELL_SIZE), (x + GRID_WIDTH, y + i * CELL_SIZE), 2)
    small_font = pygame.font.Font(None, 24)
    for i in range(GRID_SIZE):
        label = small_font.render(str(i + 1), True, BLACK)
        surface.blit(label, (x - 25, y + i * CELL_SIZE + 12))
        label = small_font.render(chr(ord('A') + i), True, BLACK)
        surface.blit(label, (x + i * CELL_SIZE + 15, y - 25))

def generate_ships():
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
    if orientation == 0 and start_col + ship_size > GRID_SIZE:
        return False
    if orientation == 1 and start_row + ship_size > GRID_SIZE:
        return False
    new_ship_coords = [(start_row, start_col + i) if orientation == 0 else (start_row + i, start_col) for i in range(ship_size)]
    for ship in existing_ships:
        if any(c in new_ship_coords for c in ship):
            return False
    return True

def get_grid_pos(mouse_x, mouse_y, grid_x, grid_y):
    if grid_x <= mouse_x <= grid_x + GRID_WIDTH and grid_y <= mouse_y <= grid_y + GRID_HEIGHT:
        col = (mouse_x - grid_x) // CELL_SIZE
        row = (mouse_y - grid_y) // CELL_SIZE
        return row, col
    return None

def is_hit(row, col, ships):
    return any((row, col) in ship for ship in ships)

def all_ships_sunk(ships, hits):
    ship_coords = set()
    for ship in ships:
        ship_coords.update(ship)
    return ship_coords.issubset(hits)

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

def ai_turn(ships, occupied, current_hits, enemy_hits, enemy_misses):
    """Perform AI turn"""
    global mode
    
    # Determine mode: hunt if no current hits, target if we have hits
    if not current_hits:
        mode = "hunt"
    else:
        mode = "target"
    
    # Calculate remaining ships (unsunk ships only)
    remaining_ships = []
    for ship in player_ships:
        if not all(coord in enemy_hits for coord in ship):
            remaining_ships.append(ship)
    
    heatmap = create_board()
    # Use remaining ship lengths for heatmap calculation
    for ship in remaining_ships:
        mark_ship_positions(heatmap, occupied, len(ship))

    shot = None
    
    if mode == "hunt":
        # Hunt mode: find highest probability cell
        max_val = -1
        for i in range(len(heatmap)):
            for j in range(len(heatmap[0])):
                if heatmap[i][j] > max_val and occupied[i][j] == 0:
                    max_val = heatmap[i][j]
                    shot = (i, j)
        
        # Fallback: if no shot found, pick any unoccupied cell
        if shot is None:
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    if occupied[i][j] == 0:
                        shot = (i, j)
                        break
                if shot is not None:
                    break
    else:
        # Target mode: try to finish off the ship
        shot = target_shot(current_hits, occupied)
        if shot is None:
            # No valid target shots, clear current hits and go back to hunt
            current_hits.clear()
            mode = "hunt"
            return ai_turn(ships, occupied, current_hits, enemy_hits, enemy_misses)

    if shot is None:
        return mode
        
    r, c = shot
    # Don't modify the occupied array here - it will be updated next turn
    
    # Check if we hit a ship
    hit = False
    hit_ship = None
    player_coords = set()
    for ship in player_ships:
        player_coords.update(ship)
    
    if (r, c) in player_coords:
        hit = True
        enemy_hits.add((r, c))
        current_hits.append((r, c))
        
        # Check if ship is completely sunk
        for ship in player_ships:
            if (r, c) in ship:
                ship_sunk = all(coord in enemy_hits for coord in ship)
                if ship_sunk:
                    # Ship is sunk, clear current hits and go back to hunt
                    current_hits.clear()
                    mode = "hunt"
                break
    else:
        enemy_misses.add((r, c))
    
    return mode

def draw_hits_misses(surface, x, y, hits, misses):
    for row,col in misses:
        cx = x + col*CELL_SIZE + CELL_SIZE//2
        cy = y + row*CELL_SIZE + CELL_SIZE//2
        pygame.draw.circle(surface, BLUE, (cx,cy),8)
    for row,col in hits:
        cell_x = x + col*CELL_SIZE + 5
        cell_y = y + row*CELL_SIZE + 5
        pygame.draw.line(surface, RED, (cell_x,cell_y),(cell_x+CELL_SIZE-10,cell_y+CELL_SIZE-10),4)
        pygame.draw.line(surface, RED, (cell_x+CELL_SIZE-10,cell_y),(cell_x,cell_y+CELL_SIZE-10),4)

# -----------------------------
# Setup
# -----------------------------
player_ships = generate_ships()
enemy_ships = generate_ships()

# -----------------------------
# Game loop
# -----------------------------
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running=False
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over and player_turn:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            grid_pos = get_grid_pos(mouse_x, mouse_y, RIGHT_GRID_X, GRID_Y)
            if grid_pos:
                row,col = grid_pos
                if (row,col) not in player_hits and (row,col) not in player_misses:
                    if is_hit(row,col,enemy_ships):
                        player_hits.add((row,col))
                    else:
                        player_misses.add((row,col))
                    if all_ships_sunk(enemy_ships, player_hits):
                        game_over=True
                        winner="Player"
                    else:
                        player_turn=False

    # AI turn
    if not player_turn and not game_over:
        # Update occupied array with all previous shots
        for r, c in enemy_hits | enemy_misses:
            occupied[r][c] = 1
            
        mode = ai_turn(player_ships, occupied, current_hits, enemy_hits, enemy_misses)
        
        # Check win condition - count sunk ships with detailed debug
        sunk_ships = 0
        total_ship_coords = 0
        total_hit_coords = len(enemy_hits)
        
        print(f"Debug: Current enemy_hits = {sorted(enemy_hits)}")
        
        for i, ship in enumerate(player_ships):
            total_ship_coords += len(ship)
            ship_hits = [coord for coord in ship if coord in enemy_hits]
            if all(coord in enemy_hits for coord in ship):
                sunk_ships += 1
                print(f"Ship {i+1} (size {len(ship)}): SUNK - coords {ship}, hits {ship_hits}")
            else:
                hits_on_ship = len(ship_hits)
                missing_coords = [coord for coord in ship if coord not in enemy_hits]
                print(f"Ship {i+1} (size {len(ship)}): {hits_on_ship}/{len(ship)} hit - missing {missing_coords}")
        
        print(f"AI has sunk {sunk_ships}/5 ships. Total hits: {total_hit_coords}/{total_ship_coords}")
        
        if all_ships_sunk(player_ships, enemy_hits):
            print("DEBUG: all_ships_sunk returned True - GAME OVER")
            game_over=True
            winner="AI"
        else:
            print("DEBUG: all_ships_sunk returned False - game continues")
            player_turn=True

    screen.fill(WHITE)
    draw_grid(screen, LEFT_GRID_X, GRID_Y, "My Ships")
    draw_grid(screen, RIGHT_GRID_X, GRID_Y, "Enemy Waters")
    ship_colors=[ORANGE,GREEN,BLUE,YELLOW,PURPLE]
    for i,ship in enumerate(player_ships):
        color = ship_colors[i%len(ship_colors)]
        for r,c in ship:
            pygame.draw.rect(screen, color, (LEFT_GRID_X + c*CELL_SIZE +2, GRID_Y + r*CELL_SIZE +2, CELL_SIZE-4, CELL_SIZE-4))
    draw_hits_misses(screen, LEFT_GRID_X, GRID_Y, enemy_hits, enemy_misses)
    draw_hits_misses(screen, RIGHT_GRID_X, GRID_Y, player_hits, player_misses)
    font=pygame.font.Font(None,48)
    if game_over:
        text=font.render(f"{winner} Wins!", True, BLACK)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2,50))
    else:
        turn_text="Your Turn" if player_turn else "AI Turn"
        text=font.render(turn_text, True, BLACK)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2,50))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
