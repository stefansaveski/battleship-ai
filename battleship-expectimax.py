import pygame
import random
from game_utils import generate_ships, is_valid_placement, get_grid_pos, is_hit, all_ships_sunk, target_shot, enhanced_target_shot_multi_ship, create_board, can_place_ship, mark_ship_positions
from graphics_utils import draw_grid, draw_hits_misses, draw_statistics
from statistics_utils import reset_game_state, update_statistics

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

# Game state - will be synchronized with utility modules
game_state = {
    'player_ships': [],
    'enemy_ships': [],
    'player_hits': set(),
    'player_misses': set(),
    'enemy_hits': set(),
    'enemy_misses': set(),
    'occupied': [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)],
    'current_hits': [],
    'mode': "hunt",
    'player_turn': True,
    'game_over': False,
    'winner': None
}

# Statistics tracking
statistics = {
    'games_played': 0,
    'ai_wins': 0,
    'total_ai_shots': 0,
    'ai_shot_counts': []
}

# Create references for backward compatibility
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

# Statistics tracking references
games_played = statistics['games_played']
ai_wins = statistics['ai_wins']
total_ai_shots = statistics['total_ai_shots']
ai_shot_counts = statistics['ai_shot_counts']

# AI parameters
MAX_DEPTH = 3     # max search depth
TOP_K = 8         # expand only top-k candidate moves
GAMMA = 0.9       # discount factor

# -----------------------------
# Functions
# -----------------------------
def get_grid_pos(mouse_x, mouse_y, grid_x, grid_y):
    if grid_x <= mouse_x <= grid_x + GRID_WIDTH and grid_y <= mouse_y <= grid_y + GRID_HEIGHT:
        col = (mouse_x - grid_x) // CELL_SIZE
        row = (mouse_y - grid_y) // CELL_SIZE
        return row, col
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
        shot, updated_current_hits = enhanced_target_shot_multi_ship(current_hits, occupied, enemy_hits, enemy_misses, player_ships)
        current_hits[:] = updated_current_hits  # Update the list in place
        
        if shot is None:
            # No valid target shots remaining (all neighbors tried), clear current hits and go back to hunt
            print(f"Expectimax multi-ship target mode complete: all neighbors of remaining unsunk ships have been tried, switching to hunt mode")
            current_hits.clear()
            mode = "hunt"
        else:
            r,c = shot
            if (r,c) in {pos for ship in player_ships for pos in ship}:
                enemy_hits.add((r,c)); current_hits.append((r,c))
                for ship in player_ships:
                    if (r,c) in ship and all(coord in enemy_hits for coord in ship):
                        # Ship is sunk, but don't clear current_hits yet
                        # The enhanced_target_shot_multi_ship function will filter out hits from sunk ships
                        print(f"Expectimax: Ship sunk! But continuing target mode to check for adjacent unsunk ships. Current hits: {current_hits}")
                        # Stay in target mode - let the multi-ship targeting handle the cleanup
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
                # Ship is sunk, but don't clear current_hits yet in hunt mode either
                # The enhanced_target_shot_multi_ship function will filter out hits from sunk ships
                print(f"Expectimax hunt mode: Ship sunk! Switching to target mode to check for adjacent unsunk ships. Current hits: {current_hits}")
                mode = "target"  # Switch to target mode to handle potential adjacent ships
    else:
        enemy_misses.add((r,c))
    return mode

def reset_game():
    """Reset the game state for a new game"""
    global game_state, player_ships, enemy_ships, player_hits, player_misses
    global enemy_hits, enemy_misses, occupied, current_hits, mode
    global player_turn, game_over, winner, games_played, ai_wins, total_ai_shots, ai_shot_counts
    
    game_state = reset_game_state()
    
    # Update global references
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
    games_played = statistics['games_played']
    ai_wins = statistics['ai_wins']
    total_ai_shots = statistics['total_ai_shots']
    ai_shot_counts = statistics['ai_shot_counts']

def update_game_statistics():
    """Update game statistics when a game ends"""
    update_statistics(statistics, enemy_hits, enemy_misses, winner)

# -----------------------------
# Setup
# -----------------------------
game_state['player_ships'] = generate_ships()
game_state['enemy_ships'] = generate_ships()
statistics = {
    'games_played': 0,
    'ai_wins': 0,
    'total_ai_shots': 0,
    'ai_shot_counts': []
}
player_ships = game_state['player_ships']
enemy_ships = game_state['enemy_ships']

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
                        update_game_statistics()
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
            update_game_statistics()
        else:
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
    
    # Show game statistics
    draw_statistics(screen, statistics['games_played'], statistics['ai_wins'], statistics['ai_shot_counts'])
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
