import pygame
import random

# Import utility modules
from game_utils import generate_ships, is_valid_placement, get_grid_pos, is_hit, all_ships_sunk, create_board, can_place_ship, mark_ship_positions, target_shot, enhanced_target_shot_multi_ship
from graphics_utils import draw_grid, draw_hits_misses, draw_statistics

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
        # Target mode: try to finish off the ship using enhanced targeting for multiple ships
        shot, updated_current_hits = enhanced_target_shot_multi_ship(current_hits, occupied, enemy_hits, enemy_misses, player_ships)
        current_hits[:] = updated_current_hits  # Update the list in place
        
        if shot is None:
            # No valid target shots remaining (all neighbors tried), clear current hits and go back to hunt
            print(f"Heatmap multi-ship target mode complete: all neighbors of remaining unsunk ships have been tried, switching to hunt mode")
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
                    # Ship is sunk, but don't clear current_hits yet
                    # The enhanced_target_shot_multi_ship function will filter out hits from sunk ships
                    print(f"Ship sunk! But continuing target mode to check for adjacent unsunk ships. Current hits: {current_hits}")
                    # Stay in target mode - let the multi-ship targeting handle the cleanup
                break
    else:
        enemy_misses.add((r, c))
    
    return mode


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
                        update_statistics()
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
            update_statistics()
        else:
            print("DEBUG: all_ships_sunk returned False - game continues")
            player_turn=True

    screen.fill(WHITE)
    draw_grid(screen, LEFT_GRID_X, GRID_Y, "My Ships", CELL_SIZE, GRID_WIDTH, GRID_HEIGHT)
    draw_grid(screen, RIGHT_GRID_X, GRID_Y, "Enemy Waters", CELL_SIZE, GRID_WIDTH, GRID_HEIGHT)
    ship_colors=[ORANGE,GREEN,BLUE,YELLOW,PURPLE]
    for i,ship in enumerate(player_ships):
        color = ship_colors[i%len(ship_colors)]
        for r,c in ship:
            pygame.draw.rect(screen, color, (LEFT_GRID_X + c*CELL_SIZE +2, GRID_Y + r*CELL_SIZE +2, CELL_SIZE-4, CELL_SIZE-4))
    draw_hits_misses(screen, LEFT_GRID_X, GRID_Y, enemy_hits, enemy_misses, CELL_SIZE)
    draw_hits_misses(screen, RIGHT_GRID_X, GRID_Y, player_hits, player_misses, CELL_SIZE)
    font=pygame.font.Font(None,48)
    if game_over:
        text=font.render(f"{winner} Wins!", True, BLACK)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2,50))
    else:
        turn_text="Your Turn" if player_turn else "AI Turn"
        text=font.render(turn_text, True, BLACK)
        screen.blit(text, (screen.get_width()//2 - text.get_width()//2,50))
    
    # Show game statistics using utility function
    draw_statistics(screen, games_played, ai_wins, ai_shot_counts)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
