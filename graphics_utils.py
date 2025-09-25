"""
Graphics utilities for battleship - drawing functions
"""
import pygame

# Grid settings (these should match main files)
GRID_SIZE = 10

# Colors (these should match main files)
BLACK = (0, 0, 0)
BLUE = (0, 100, 200)
RED = (200, 0, 0)
GRAY = (128, 128, 128)

def draw_grid(surface, x, y, title, cell_size, grid_width, grid_height):
    """Draw the game grid with labels"""
    font = pygame.font.Font(None, 36)
    text = font.render(title, True, BLACK)
    surface.blit(text, (x, y - 60))
    for i in range(GRID_SIZE + 1):
        pygame.draw.line(surface, BLACK, (x + i * cell_size, y), (x + i * cell_size, y + grid_height), 2)
        pygame.draw.line(surface, BLACK, (x, y + i * cell_size), (x + grid_width, y + i * cell_size), 2)
    small_font = pygame.font.Font(None, 24)
    for i in range(GRID_SIZE):
        label = small_font.render(str(i + 1), True, BLACK)
        surface.blit(label, (x - 25, y + i * cell_size + 12))
        label = small_font.render(chr(ord('A') + i), True, BLACK)
        surface.blit(label, (x + i * cell_size + 15, y - 25))

def draw_hits_misses(surface, x, y, hits, misses, cell_size):
    """Draw hits and misses on the grid"""
    for row, col in misses:
        cx = x + col * cell_size + cell_size // 2
        cy = y + row * cell_size + cell_size // 2
        pygame.draw.circle(surface, BLUE, (cx, cy), 8)
    for row, col in hits:
        cell_x = x + col * cell_size + 5
        cell_y = y + row * cell_size + 5
        pygame.draw.line(surface, RED, (cell_x, cell_y), (cell_x + cell_size - 10, cell_y + cell_size - 10), 4)
        pygame.draw.line(surface, RED, (cell_x + cell_size - 10, cell_y), (cell_x, cell_y + cell_size - 10), 4)

def draw_statistics(surface, games_played, ai_wins, ai_shot_counts):
    """Draw game statistics on screen"""
    small_font = pygame.font.Font(None, 32)
    if games_played > 0:
        stats_y = 600
        stats_text = f"Games: {games_played} | AI Wins: {ai_wins} ({ai_wins/games_played*100:.1f}%)"
        if len(ai_shot_counts) > 0:
            avg_shots = sum(ai_shot_counts) / len(ai_shot_counts)
            stats_text += f" | Avg Shots: {avg_shots:.1f}"
        stats_surface = small_font.render(stats_text, True, BLACK)
        surface.blit(stats_surface, (10, stats_y))
        
        # Instructions
        instructions = small_font.render("Press R to reset game", True, GRAY)
        surface.blit(instructions, (10, stats_y + 30))