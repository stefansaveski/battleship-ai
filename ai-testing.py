#heat map 10x10
#array of ships with their coordinates, pop coordinates as we shoot
#if all cords in ship are removed remove the ship, adjust heat map based on ships left
#hunt and target method to implement when a ship is hit
#only shoot one seperated spots
import random

def create_board(n=10):
    return [[0 for _ in range(n)] for _ in range(n)]

# Each ship is a list of coordinates (row, col)


def random_shot():
    # pick random row (0–9) and column (0–9)
    # but force them to follow checkerboard rule: (row + col) % 2 == 0
    while True:
        row = random.randint(0, 9)
        col = random.randint(0, 9)
        if (row + col) % 2 == 0:  # checkerboard condition
            return (row, col)

def can_place_ship(occupied, x, y, ship_len, horizontal):
    n = len(occupied)

    if horizontal:
        if y + ship_len > n:
            return False
        for k in range(ship_len):
            if occupied[x][y + k] == 1:
                return False
    else:
        if x + ship_len > n:
            return False
        for k in range(ship_len):
            if occupied[x + k][y] == 1:
                return False
    return True

def mark_ship_positions(board, occupied, ship_len):
    n = len(board)

    # Horizontal placements
    for i in range(n):
        for j in range(n - ship_len + 1):
            if can_place_ship(occupied, i, j, ship_len, True):
                for k in range(ship_len):
                    board[i][j + k] += 1

    # Vertical placements
    for i in range(n - ship_len + 1):
        for j in range(n):
            if can_place_ship(occupied, i, j, ship_len, False):
                for k in range(ship_len):
                    board[i + k][j] += 1

def ai_turn(ships, occupied):
    heatmap = create_board();
    for ship in ships:
        mark_ship_positions(heatmap, occupied, len(ship))
    max_val = -1;
    max_pos = (-1, -1);
    for i in range(len(heatmap)):
        for j in range(len(heatmap[0])):
            if(heatmap[i][j] > max_val and (i + j) % 2 == 0):
                max_val = heatmap[i][j]
                max_pos = (i, j);
    occupied[max_pos[0]][max_pos[1]] = 1;
    for ship in ships:
        if max_pos in ship:
            ship.remove(max_pos)
    ships = [ship for ship in ships if ship]
    print_board(heatmap);
    print_board(occupied);
    for i, ship in enumerate(ships, start=1):
        print(f"Ship {i}: {ship}")


def print_board(board):
    for row in board:
        print(" ".join(f"{val:2}" for val in row))

def main():
    ships = [
    # Carrier (5 cells)
    [(0,0), (0,1), (0,2), (0,3), (0,4)],

    # Battleship (4 cells)
    [(2,2), (3,2), (4,2), (5,2)],

    # Cruiser (3 cells)
    [(7,5), (7,6), (7,7)],

    # Submarine (3 cells)
    [(9,0), (9,1), (9,2)],

    # Destroyer (2 cells)
    [(4,7), (5,7)]
    ]
    occupied = create_board();
    ai_turn(ships, occupied);
    ai_turn(ships, occupied);


if __name__ == "__main__":
    main()
