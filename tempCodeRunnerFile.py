    candidates = [(r,c,heatmap[r][c]) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if occupied[r][c]==0]
