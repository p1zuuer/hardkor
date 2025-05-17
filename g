class Enemy(pygame.sprite.Sprite):
    ENEMY_STATS = {
        EnemyType.NORMAL: {"size": 25, "color": MEDIUM_GRAY, "speed": 1.5, "health": 1, "damage": 1, "points": 10},
        EnemyType.FAST: {"size": 20, "color": LIGHT_GRAY, "speed": 2.0, "health": 1, "damage": 1, "points": 15},
        EnemyType.TANK: {"size": 35, "color": DARK_GRAY, "speed": 1.0, "health": 3, "damage": 1, "points": 30},
        EnemyType.BOSS: {"size": 50, "color": WHITE, "speed": 1.8, "health": 15, "damage": 2, "points": 100},
        EnemyType.ULTRA: {"size": 70, "color": RED, "speed": 2.0, "health": 30, "damage": 3, "points": 250}
    }
