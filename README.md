# Battleship AI

A Python implementation of the classic Battleship game featuring advanced AI opponents. Includes three AI models (Heatmap, Monte Carlo, Expectimax) with multi-ship targeting logic for smarter gameplay.

## Features
- Play Battleship against the computer with a graphical interface (Pygame)
- Three AI strategies:
  - **Heatmap AI**: Uses probability heatmaps to hunt ships
  - **Monte Carlo AI**: Simulates possible ship placements for optimal shots
  - **Expectimax AI**: Game tree search for strategic decision-making
- **Multi-Ship Targeting**: AI continues targeting until all adjacent ships are sunk
- Game statistics tracking (shots, wins, averages)
- Easy-to-read code and modular utilities

## Getting Started

### Prerequisites
- Python 3.8+
- [Pygame](https://www.pygame.org/)

Install dependencies:
```powershell
pip install pygame
```

### Running the Game

Run any AI model from the command line:
```powershell
python battleship-heatmap.py
python battleship-montecarlo.py
python battleship-expectimax.py
```

- The Expectimax model launches a graphical window.
- The Heatmap and Monte Carlo models run in the console.

## How It Works
- Ships are randomly placed on a 10x10 grid.
- The AI uses advanced algorithms to hunt and sink all ships.
- Multi-ship targeting ensures the AI doesn't abandon adjacent ships when one is sunk.
- Game statistics are displayed after each game.

## File Structure
- `battleship-heatmap.py` — Heatmap AI model
- `battleship-montecarlo.py` — Monte Carlo AI model
- `battleship-expectimax.py` — Expectimax AI model (GUI)
- `game_utils.py` — Core game logic and targeting functions
- `graphics_utils.py` — Drawing and display utilities
- `statistics_utils.py` — Game statistics tracking


## Credits
- Developed by Stefan Saveski
- Powered by Python and Pygame

## License
MIT License
