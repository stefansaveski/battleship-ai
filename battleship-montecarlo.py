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
            print(f"Last 5 games: {ai_shot_counts[-5:]}")
            print("=====================================\n")
    else:
        print(f"\n=== GAME {games_played} COMPLETE ===")
        print(f"Winner: {winner} (Player won!)")
        print(f"AI shots taken: {ai_shots_this_game}")
        print("=====================================\n")

def monte_carlo_ai_turn(occupied, current_hits, enemy_hits, enemy_misses, simulations=20):
    """Monte Carlo AI that simulates possible ship configurations (optimized with checkerboard)"""
    global mode
    
    # Determine mode
    if not current_hits:
        mode = "hunt"
    else:
        mode = "target"
    
    # If in target mode, prioritize adjacent shots to current hits
    if mode == "target":
        shot = target_shot(current_hits, occupied)
        if shot is not None:
            return execute_shot(shot[0], shot[1])
        else:
            # No valid target shots, clear current hits and go back to hunt
            current_hits.clear()
            mode = "hunt"
    
    # Hunt mode: Only consider checkerboard positions + Monte Carlo
    available_shots = []
    checkerboard_shots = []
    
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if occupied[r][c] == 0:
                available_shots.append((r, c))
                # Checkerboard pattern: only cells where (r + c) is even
                if (r + c) % 2 == 0:
                    checkerboard_shots.append((r, c))
    
    if not available_shots:
        return mode
    
    # If we still have checkerboard positions available, only use those
    shots_to_evaluate = checkerboard_shots if checkerboard_shots else available_shots
    
    if not shots_to_evaluate:
        return mode
    
    print(f"Evaluating {len(shots_to_evaluate)} checkerboard positions (of {len(available_shots)} total)")
    
    # Calculate ship sizes still in play
    remaining_ship_sizes = get_remaining_ship_sizes()
    
    # Reduced simulation count and smarter evaluation
    shot_scores = {}
    
    # Pre-generate a small number of valid configurations to reuse
    valid_configs = []
    for _ in range(min(simulations // 2, 10)):  # Generate fewer configurations
        config = generate_random_ship_configuration(remaining_ship_sizes, enemy_hits, enemy_misses)
        if config:
            valid_configs.append(config)
    
    if not valid_configs:
        # Fallback to random shot from checkerboard positions if no valid configurations found
        best_shot = random.choice(shots_to_evaluate)
        print(f"Fallback checkerboard shot: {best_shot}")
        return execute_shot(best_shot[0], best_shot[1])
    
    # Evaluate shots against pre-generated configurations
    for shot in shots_to_evaluate:
        hits = sum(1 for config in valid_configs if shot in config)
        shot_scores[shot] = hits / len(valid_configs)
    
    # Choose the shot with highest score
    best_shot = max(shot_scores.keys(), key=lambda s: shot_scores[s])
    is_checkerboard = (best_shot[0] + best_shot[1]) % 2 == 0
    print(f"Monte Carlo chose {'checkerboard' if is_checkerboard else 'regular'} shot {best_shot} with score {shot_scores[best_shot]:.3f}")
    
    return execute_shot(best_shot[0], best_shot[1])

def get_remaining_ship_sizes():
    """Get sizes of ships that aren't completely sunk"""
    remaining_sizes = []
    for ship in player_ships:
        if not all(coord in enemy_hits for coord in ship):
            remaining_sizes.append(len(ship))
    return remaining_sizes

def evaluate_shot_monte_carlo(shot, remaining_ship_sizes, known_hits, known_misses, simulations):
    """Evaluate a shot using Monte Carlo simulation"""
    hit_count = 0
    total_simulations = 0
    
    for _ in range(simulations):
        # Generate a random configuration of remaining ships
        ship_config = generate_random_ship_configuration(remaining_ship_sizes, known_hits, known_misses)
        if ship_config is None:
            continue
            
        total_simulations += 1
        
        # Check if this shot would hit in this configuration
        if shot in ship_config:
            hit_count += 1
    
    if total_simulations == 0:
        return 0.0
    
    return hit_count / total_simulations

def generate_random_ship_configuration(ship_sizes, known_hits, known_misses):
    """Generate a random ship configuration consistent with known information (optimized)"""
    max_attempts = 20  # Reduced from 100
    
    for attempt in range(max_attempts):
        ship_coords = set()
        ships = []
        
        # Place each remaining ship randomly
        for size in ship_sizes:
            placed = False
            placement_attempts = 0
            
            while not placed and placement_attempts < 20:  # Reduced from 50
                start_r = random.randint(0, GRID_SIZE - 1)
                start_c = random.randint(0, GRID_SIZE - 1)
                orientation = random.choice([0, 1])  # 0=horizontal, 1=vertical
                
                # Generate ship coordinates
                ship = []
                valid = True
                
                for i in range(size):
                    if orientation == 0:  # horizontal
                        r, c = start_r, start_c + i
                    else:  # vertical
                        r, c = start_r + i, start_c
                    
                    if r >= GRID_SIZE or c >= GRID_SIZE:
                        valid = False
                        break
                    
                    if (r, c) in ship_coords or (r, c) in known_misses:
                        valid = False
                        break
                        
                    ship.append((r, c))
                
                if valid and len(ship) == size:
                    ships.append(ship)
                    ship_coords.update(ship)
                    placed = True
                
                placement_attempts += 1
            
            if not placed:
                break  # Failed to place this ship, try a new configuration
        
        # Quick validation - just check that we placed all ships
        if len(ships) == len(ship_sizes):
            config_coords = set()
            for ship in ships:
                config_coords.update(ship)
            
            # Simple check - all known hits should be covered
            if known_hits.issubset(config_coords):
                return config_coords
    
    return None  # Failed to generate valid configuration

def execute_shot(r, c):
    """Execute a shot and update game state"""
    global mode
    
    player_coords = set()
    for ship in player_ships:
        player_coords.update(ship)
    
    if (r, c) in player_coords:
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
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_over:
                # Space to start a new game
                reset_game()
            elif event.key == pygame.K_r:
                # R to reset at any time
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
        # Update occupied array with all previous shots
        for r, c in enemy_hits | enemy_misses:
            occupied[r][c] = 1
            
        mode = monte_carlo_ai_turn(occupied, current_hits, enemy_hits, enemy_misses, simulations=15)
        
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
            update_statistics()
        else:
            print("DEBUG: all_ships_sunk returned False - game continues")
            player_turn=True

    screen.fill(WHITE)
    draw_grid(screen, LEFT_GRID_X, GRID_Y, "My Ships")
    draw_grid(screen, RIGHT_GRID_X, GRID_Y, "Enemy Waters (Monte Carlo AI)")
    ship_colors=[ORANGE,GREEN,BLUE,YELLOW,PURPLE]
    for i,ship in enumerate(player_ships):
        color = ship_colors[i%len(ship_colors)]
        for r,c in ship:
            pygame.draw.rect(screen, color, (LEFT_GRID_X + c*CELL_SIZE +2, GRID_Y + r*CELL_SIZE +2, CELL_SIZE-4, CELL_SIZE-4))
    draw_hits_misses(screen, LEFT_GRID_X, GRID_Y, enemy_hits, enemy_misses)
    draw_hits_misses(screen, RIGHT_GRID_X, GRID_Y, player_hits, player_misses)
    font=pygame.font.Font(None,48)
    small_font=pygame.font.Font(None,24)
    if game_over:
        text=font.render(f"{winner} Wins!", True, BLACK)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2,50))
        
        # Show game statistics
        if winner == "AI" and len(ai_shot_counts) > 0:
            avg_text = small_font.render(f"AI took {len(enemy_hits) + len(enemy_misses)} shots", True, BLACK)
            screen.blit(avg_text, (screen.get_width()//2 - avg_text.get_width()//2, 90))
            
            if len(ai_shot_counts) > 1:
                avg_shots = sum(ai_shot_counts) / len(ai_shot_counts)
                stats_text = small_font.render(f"Average: {avg_shots:.1f} shots over {len(ai_shot_counts)} wins", True, BLACK)
                screen.blit(stats_text, (screen.get_width()//2 - stats_text.get_width()//2, 110))
        
        # Instructions
        instruction_text = small_font.render("Press SPACE for new game, R to reset", True, BLACK)
        screen.blit(instruction_text, (screen.get_width()//2 - instruction_text.get_width()//2, 650))
    else:
        turn_text="Your Turn" if player_turn else "AI Turn"
        text=font.render(turn_text, True, BLACK)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2,50))
        
        # Show current game stats
        if games_played > 0:
            current_shots = len(enemy_hits) + len(enemy_misses)
            current_text = small_font.render(f"AI shots this game: {current_shots}", True, BLACK)
            screen.blit(current_text, (10, 10))
            
            if ai_wins > 0:
                avg_shots = sum(ai_shot_counts) / len(ai_shot_counts)
                avg_text = small_font.render(f"AI average: {avg_shots:.1f} shots ({ai_wins} wins)", True, BLACK)
                screen.blit(avg_text, (10, 30))
        
        # Instructions
        instruction_text = small_font.render("Press R to reset game", True, BLACK)
        screen.blit(instruction_text, (10, 650))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
