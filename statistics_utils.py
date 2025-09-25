"""
Statistics utilities for battleship - game tracking and reset functions
"""
from game_utils import generate_ships, GRID_SIZE

def create_statistics_globals():
    """Initialize global statistics variables"""
    return {
        'games_played': 0,
        'ai_wins': 0,
        'total_ai_shots': 0,
        'ai_shot_counts': []
    }

def reset_game_state():
    """Reset the game state for a new game - returns new game state dict"""
    return {
        'player_ships': generate_ships(),
        'enemy_ships': generate_ships(),
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

def update_statistics(stats, enemy_hits, enemy_misses, winner):
    """Update game statistics when a game ends"""
    stats['games_played'] += 1
    ai_shots_this_game = len(enemy_hits) + len(enemy_misses)
    stats['total_ai_shots'] += ai_shots_this_game
    
    if winner == "AI":
        stats['ai_wins'] += 1
        stats['ai_shot_counts'].append(ai_shots_this_game)
        
        print(f"\n=== GAME {stats['games_played']} COMPLETE ===")
        print(f"Winner: {winner}")
        print(f"AI shots this game: {ai_shots_this_game}")
        
        if len(stats['ai_shot_counts']) > 0:
            avg_shots = sum(stats['ai_shot_counts']) / len(stats['ai_shot_counts'])
            min_shots = min(stats['ai_shot_counts'])
            max_shots = max(stats['ai_shot_counts'])
            
            print(f"\n--- AI STATISTICS (when AI wins) ---")
            print(f"AI wins: {stats['ai_wins']}/{stats['games_played']} ({stats['ai_wins']/stats['games_played']*100:.1f}%)")
            print(f"Average shots to win: {avg_shots:.1f}")
            print(f"Best game (fewest shots): {min_shots}")
            print(f"Worst game (most shots): {max_shots}")
            print(f"Last 5 games: {stats['ai_shot_counts'][-5:]}")
            print("=====================================\n")
    else:
        print(f"\n=== GAME {stats['games_played']} COMPLETE ===")
        print(f"Winner: {winner} (Player won!)")
        print(f"AI shots taken: {ai_shots_this_game}")
        print("=====================================\n")