import pygame
import random

# Import utility modules
from game_utils import generate_ships, is_valid_placement, get_grid_pos, is_hit, all_ships_sunk, create_board, can_place_ship, mark_ship_positions, target_shot, enhanced_target_shot_multi_ship
from graphics_utils import draw_grid, draw_hits_misses, draw_statistics
from statistics_utils import create_statistics_globals, reset_game_state, update_statistics

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

# Game state - using dictionary structure for easier management
game_state = reset_game_state()
statistics = create_statistics_globals()

# Extract commonly used variables for backward compatibility
player_ships = game_state['player_ships']
enemy_ships = game_state['enemy_ships']
player_hits = game_state['player_hits']
player_misses = game_state['player_misses']
enemy_hits = game_state['enemy_hits']
enemy_misses = game_state['enemy_misses']
occupied = game_state['occupied']
current_hits = game_state['current_hits']
mode = game_state['mode']
player_turn = game_state['player_turn']
game_over = game_state['game_over']
winner = game_state['winner']

# Statistics - extract for backward compatibility
games_played = statistics['games_played']
ai_wins = statistics['ai_wins']
total_ai_shots = statistics['total_ai_shots']
ai_shot_counts = statistics['ai_shot_counts']

# -----------------------------
# Functions
# -----------------------------

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
        shot, updated_current_hits = enhanced_target_shot_multi_ship(current_hits, occupied, enemy_hits, enemy_misses, player_ships)
        current_hits[:] = updated_current_hits  # Update the list in place
        
        if shot is not None:
            return execute_shot(shot[0], shot[1])
        else:
            # No valid target shots remaining (all neighbors tried), clear current hits and go back to hunt
            print(f"Monte Carlo multi-ship target mode complete: all neighbors of remaining unsunk ships have been tried, switching to hunt mode")
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
                    # Ship is sunk, but don't clear current_hits yet
                    # The enhanced_target_shot_multi_ship function will filter out hits from sunk ships
                    print(f"Monte Carlo: Ship sunk! But continuing target mode to check for adjacent unsunk ships. Current hits: {current_hits}")
                    # Stay in target mode - let the multi-ship targeting handle the cleanup
                break
    else:
        enemy_misses.add((r, c))
    
    return mode

# -----------------------------
# Setup
# -----------------------------
# Initialize game using utility functions
game_state = reset_game_state()
statistics = create_statistics_globals()

# Update global references
player_ships = game_state['player_ships']
enemy_ships = game_state['enemy_ships']

def sync_game_state():
    """Sync global variables with game_state dictionary"""
    global player_ships, enemy_ships, player_hits, player_misses, enemy_hits, enemy_misses
    global occupied, current_hits, mode, player_turn, game_over, winner
    global games_played, ai_wins, total_ai_shots, ai_shot_counts
    
    # Update game_state from globals (in case they were modified)
    game_state['player_ships'] = player_ships
    game_state['enemy_ships'] = enemy_ships  
    game_state['player_hits'] = player_hits
    game_state['player_misses'] = player_misses
    game_state['enemy_hits'] = enemy_hits
    game_state['enemy_misses'] = enemy_misses
    game_state['occupied'] = occupied
    game_state['current_hits'] = current_hits
    game_state['mode'] = mode
    game_state['player_turn'] = player_turn
    game_state['game_over'] = game_over
    game_state['winner'] = winner
    
    # Update globals from game_state
    player_ships = game_state['player_ships']
    enemy_ships = game_state['enemy_ships']
    player_hits = game_state['player_hits']
    player_misses = game_state['player_misses']
    enemy_hits = game_state['enemy_hits']
    enemy_misses = game_state['enemy_misses']
    occupied = game_state['occupied']
    current_hits = game_state['current_hits']
    mode = game_state['mode']
    player_turn = game_state['player_turn']
    game_over = game_state['game_over']
    winner = game_state['winner']
    
    # Update statistics
    games_played = statistics['games_played']
    ai_wins = statistics['ai_wins']
    total_ai_shots = statistics['total_ai_shots']
    ai_shot_counts = statistics['ai_shot_counts']

def reset_game():
    """Reset game using utility function"""
    global game_state, statistics
    global player_ships, enemy_ships, player_hits, player_misses, enemy_hits, enemy_misses
    global occupied, current_hits, mode, player_turn, game_over, winner
    global games_played, ai_wins, total_ai_shots, ai_shot_counts
    
    # Reset the game state
    game_state = reset_game_state()
    
    # Update all global variables from the new game state
    player_ships = game_state['player_ships']
    enemy_ships = game_state['enemy_ships']
    player_hits = game_state['player_hits']
    player_misses = game_state['player_misses']
    enemy_hits = game_state['enemy_hits']
    enemy_misses = game_state['enemy_misses']
    occupied = game_state['occupied']
    current_hits = game_state['current_hits']
    mode = game_state['mode']
    player_turn = game_state['player_turn']
    game_over = game_state['game_over']
    winner = game_state['winner']
    
    # Update statistics variables
    games_played = statistics['games_played']
    ai_wins = statistics['ai_wins']
    total_ai_shots = statistics['total_ai_shots']
    ai_shot_counts = statistics['ai_shot_counts']

# Initialize the sync
sync_game_state()

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
            grid_pos = get_grid_pos(mouse_x, mouse_y, RIGHT_GRID_X, GRID_Y, CELL_SIZE, GRID_WIDTH, GRID_HEIGHT)
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
                        update_statistics(statistics, enemy_hits, enemy_misses, winner)
                        sync_game_state()
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
            update_statistics(statistics, enemy_hits, enemy_misses, winner)
            sync_game_state()
        else:
            print("DEBUG: all_ships_sunk returned False - game continues")
            player_turn=True

    screen.fill(WHITE)
    draw_grid(screen, LEFT_GRID_X, GRID_Y, "My Ships", CELL_SIZE, GRID_WIDTH, GRID_HEIGHT)
    draw_grid(screen, RIGHT_GRID_X, GRID_Y, "Enemy Waters (Monte Carlo AI)", CELL_SIZE, GRID_WIDTH, GRID_HEIGHT)
    ship_colors=[ORANGE,GREEN,BLUE,YELLOW,PURPLE]
    for i,ship in enumerate(player_ships):
        color = ship_colors[i%len(ship_colors)]
        for r,c in ship:
            pygame.draw.rect(screen, color, (LEFT_GRID_X + c*CELL_SIZE +2, GRID_Y + r*CELL_SIZE +2, CELL_SIZE-4, CELL_SIZE-4))
    draw_hits_misses(screen, LEFT_GRID_X, GRID_Y, enemy_hits, enemy_misses, CELL_SIZE)
    draw_hits_misses(screen, RIGHT_GRID_X, GRID_Y, player_hits, player_misses, CELL_SIZE)
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
