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

# AI parameters
MAX_DEPTH = 3     # max search depth
TOP_K = 8         # expand only top-k candidate moves
GAMMA = 0.9       # discount factor

# Statistics tracking
games_played = 0
ai_wins = 0
total_ai_shots = 0
ai_shot_counts = []

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

def compute_heatmap(occupied, remaining_ships):
    heatmap = create_board()
    for ship in remaining_ships:
        mark_ship_positions(heatmap, occupied, len(ship))
    return heatmap

def remaining_ships(enemy_hits):
    rem = []
    for ship in player_ships:
        if not all(coord in enemy_hits for coord in ship):
            rem.append(ship)
    return rem

def heuristic_value(occupied, current_hits, enemy_hits, enemy_misses):
    # basic heuristic = number of hits minus misses
    return len(enemy_hits) - 0.2*len(enemy_misses)

def expectimax(occupied, current_hits, enemy_hits, enemy_misses, depth, max_depth):
    if depth == 0 or all_ships_sunk(player_ships, enemy_hits):
        return heuristic_value(occupied, current_hits, enemy_hits, enemy_misses), None

    rem_ships = remaining_ships(enemy_hits)
    heatmap = compute_heatmap(occupied, rem_ships)

    candidates = [(r,c,heatmap[r][c]) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if occupied[r][c]==0]
    if not candidates:
        return heuristic_value(occupied, current_hits, enemy_hits, enemy_misses), None

    candidates.sort(key=lambda x: x[2], reverse=True)
    candidates = candidates[:TOP_K]

    max_heat = max(val for _,_,val in candidates) or 1
    best_val = -1e9
    best_move = None

    for r,c,val in candidates:
        p_hit = val / max_heat
        # simulate hit
        occ_hit = [row[:] for row in occupied]
        hits_hit = set(enemy_hits); misses_hit = set(enemy_misses); ch_hit = list(current_hits)
        hits_hit.add((r,c)); ch_hit.append((r,c))
        sunk = False
        for ship in player_ships:
            if (r,c) in ship and all(coord in hits_hit for coord in ship):
                ch_hit.clear(); sunk = True
        occ_hit[r][c] = 1
        val_hit,_ = expectimax(occ_hit, ch_hit, hits_hit, misses_hit, depth-1, max_depth)

        # simulate miss
        occ_miss = [row[:] for row in occupied]
        hits_miss = set(enemy_hits); misses_miss = set(enemy_misses)
        misses_miss.add((r,c)); occ_miss[r][c] = 1
        val_miss,_ = expectimax(occ_miss, list(current_hits), hits_miss, misses_miss, depth-1, max_depth)

        exp_val = p_hit * (1 + GAMMA*val_hit) + (1-p_hit) * (GAMMA*val_miss)

        if exp_val > best_val:
            best_val = exp_val
            best_move = (r,c)

    return best_val, best_move

def ai_turn(ships, occupied, current_hits, enemy_hits, enemy_misses):
    global mode
    if not current_hits:
        mode = "hunt"
    else:
        mode = "target"

    if mode == "target":
        shot = target_shot(current_hits, occupied)
        if shot is None:
            current_hits.clear()
            mode = "hunt"
        else:
            r,c = shot
            if (r,c) in {pos for ship in player_ships for pos in ship}:
                enemy_hits.add((r,c)); current_hits.append((r,c))
                for ship in player_ships:
                    if (r,c) in ship and all(coord in enemy_hits for coord in ship):
                        current_hits.clear(); mode = "hunt"
            else:
                enemy_misses.add((r,c))
            return mode

    # hunt mode -> expectimax
    _, shot = expectimax(occupied, current_hits, enemy_hits, enemy_misses, MAX_DEPTH, MAX_DEPTH)
    if shot is None:
        return mode
    r,c = shot
    if (r,c) in {pos for ship in player_ships for pos in ship}:
        enemy_hits.add((r,c)); current_hits.append((r,c))
        for ship in player_ships:
            if (r,c) in ship and all(coord in enemy_hits for coord in ship):
                current_hits.clear(); mode = "hunt"
    else:
        enemy_misses.add((r,c))
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

def update_statistics():
    """Update game statistics when a game ends"""
    global games_played, ai_wins, total_ai_shots, ai_shot_counts
    
    games_played += 1
    ai_shots_this_game = len(enemy_hits) + len(enemy_misses)
    total_ai_shots += ai_shots_this_game
    
    if winner == "AI":
        ai_wins += 1
        ai_shot_counts.append(ai_shots_this_game)
        
        print(f"\n=== GAME {games_played} COMPLETE ===")
        print(f"Winner: {winner}")
        print(f"AI shots this game: {ai_shots_this_game}")
        
        if len(ai_shot_counts) > 0:
            avg_shots = sum(ai_shot_counts) / len(ai_shot_counts)
            min_shots = min(ai_shot_counts)
            max_shots = max(ai_shot_counts)
            
            print(f"\n--- AI STATISTICS (when AI wins) ---")
            print(f"AI wins: {ai_wins}/{games_played} ({ai_wins/games_played*100:.1f}%)")
            print(f"Average shots to win: {avg_shots:.1f}")
            print(f"Best game (fewest shots): {min_shots}")
            print(f"Worst game (most shots): {max_shots}")
    else:
        print(f"\n=== GAME {games_played} COMPLETE ===")
        print(f"Winner: {winner}")
        print(f"AI shots this game: {ai_shots_this_game}")

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
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game()
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
                        update_statistics()
                    else:
                        player_turn=False

    # AI turn
    if not player_turn and not game_over:
        for r,c in enemy_hits | enemy_misses:
            occupied[r][c] = 1
        mode = ai_turn(player_ships, occupied, current_hits, enemy_hits, enemy_misses)
        if all_ships_sunk(player_ships, enemy_hits):
            game_over=True
            winner="AI"
            update_statistics()
        else:
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
    
    # Show game statistics
    small_font = pygame.font.Font(None, 32)
    if games_played > 0:
        stats_y = 600
        stats_text = f"Games: {games_played} | AI Wins: {ai_wins} ({ai_wins/games_played*100:.1f}%)"
        if len(ai_shot_counts) > 0:
            avg_shots = sum(ai_shot_counts) / len(ai_shot_counts)
            stats_text += f" | Avg Shots: {avg_shots:.1f}"
        stats_surface = small_font.render(stats_text, True, BLACK)
        screen.blit(stats_surface, (10, stats_y))
        
        # Instructions
        instructions = small_font.render("Press R to reset game", True, GRAY)
        screen.blit(instructions, (10, stats_y + 30))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
