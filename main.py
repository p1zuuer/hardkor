import pygame
import random
import math
import sys
from enum import Enum

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Настройки игры
WIDTH, HEIGHT = 1280, 720
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NO HUMANITY")
clock = pygame.time.Clock()

# Цвет
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)
MEDIUM_GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Шрифты
try:
    title_font = pygame.font.Font(None, 72)
    main_font = pygame.font.Font(None, 42)
    small_font = pygame.font.Font(None, 28)
except:
    title_font = pygame.font.SysFont('arial', 72, bold=True)
    main_font = pygame.font.SysFont('arial', 42)
    small_font = pygame.font.SysFont('arial', 28)


# Типы врагов
class EnemyType(Enum):
    NORMAL = "normal"
    FAST = "fast"
    TANK = "tank"
    BOSS = "boss"
    ULTRA = "ultra"


# Класс кнопки
class Button:
    def __init__(self, x, y, width, height, text, price=None, tooltip=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.price = price
        self.tooltip = tooltip
        self.active = True
        self.hovered = False

    def draw(self, surface, points=None):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)

        if not self.active:
            color = DARK_GRAY
            border_color = MEDIUM_GRAY
        elif self.price is not None and points is not None and points < self.price:
            color = DARK_GRAY
            border_color = MEDIUM_GRAY
        else:
            color = LIGHT_GRAY if self.hovered else WHITE
            border_color = WHITE

        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=5)

        text_color = BLACK if color in (WHITE, LIGHT_GRAY) else MEDIUM_GRAY
        text_surf = main_font.render(self.text, True, text_color)
        surface.blit(text_surf, (self.rect.centerx - text_surf.get_width() // 2,
                                 self.rect.centery - text_surf.get_height() // 2))

        if self.price is not None:
            price_color = WHITE if (points is not None and points >= self.price) else MEDIUM_GRAY
            price_surf = small_font.render(f"{self.price} PTS", True, price_color)
            surface.blit(price_surf, (self.rect.right - price_surf.get_width() - 15,
                                      self.rect.bottom - price_surf.get_height() - 10))

        if self.hovered and self.tooltip:
            tooltip_rect = pygame.Rect(mouse_pos[0] + 20, mouse_pos[1],
                                       max(250, len(self.tooltip) * 8), 34)
            pygame.draw.rect(surface, DARK_GRAY, tooltip_rect)
            pygame.draw.rect(surface, WHITE, tooltip_rect, 1)

            tooltip_surf = small_font.render(self.tooltip, True, WHITE)
            surface.blit(tooltip_surf, (tooltip_rect.x + 10, tooltip_rect.y + 7))

    def check_click(self, pos, points=None):
        if self.active and self.rect.collidepoint(pos):
            if self.price is None or (points is not None and points >= self.price):
                return True
        return False


# Класс игрока
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, upgrades=None):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (20, 20), 18)
        pygame.draw.circle(self.image, BLACK, (20, 20), 18, 2)

        self.rect = self.image.get_rect(center=(x, y))
        self.upgrades = upgrades or {}

        # Характеристики
        self.base_speed = 5
        self.speed = self.base_speed + self.upgrades.get("speed", 0)
        self.max_health = 100 + self.upgrades.get("health", 0) * 5
        self.health = self.max_health
        self.invincible = False
        self.invincible_timer = 0
        self.dash_cooldown = 0
        self.time_slow_cooldown = 0
        self.dash_active = False
        self.time_slow_active = False
        self.dash_direction = [0, 0]
        self.last_dx, self.last_dy = 0, 0

    def take_damage(self, damage=1):
        if self.invincible:
            return False

        self.health -= damage
        self.invincible = True
        self.invincible_timer = 30
        return self.health <= 0

    def update(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += self.speed

        # Сохраняем направление для предсказания
        if dx != 0 or dy != 0:
            self.last_dx, self.last_dy = dx, dy

        # Нормализация диагонального движения
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        # Рывок
        if keys[pygame.K_LSHIFT] and not self.dash_active and self.dash_cooldown <= 0:
            self.dash_active = True
            self.dash_cooldown = 180
            self.dash_direction = [dx, dy] if (dx != 0 or dy != 0) else [1, 0]

        if self.dash_active:
            dash_speed = 10 + self.upgrades.get("dash", 0) * 2
            self.rect.x += self.dash_direction[0] * dash_speed
            self.rect.y += self.dash_direction[1] * dash_speed
            self.dash_cooldown -= 1

            if self.dash_cooldown <= 150:
                self.dash_active = False
        else:
            self.rect.x += dx
            self.rect.y += dy

        # Замедление времени
        if keys[pygame.K_SPACE] and not self.time_slow_active and self.time_slow_cooldown <= 0:
            self.time_slow_active = True
            self.time_slow_cooldown = 300 - self.upgrades.get("cooldown", 0) * 20

        if self.time_slow_active:
            self.time_slow_cooldown -= 1
            if self.time_slow_cooldown <= 240:
                self.time_slow_active = False

        # Обновление кулдаунов
        if self.dash_cooldown > 0 and not self.dash_active:
            self.dash_cooldown -= 1

        if self.time_slow_cooldown > 0 and not self.time_slow_active:
            self.time_slow_cooldown -= 1

        # Неуязвимость после получения урона
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        # Границы экрана
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y))


# Класс врага
class Enemy(pygame.sprite.Sprite):
    ENEMY_STATS = {
        EnemyType.NORMAL: {"size": 25, "color": MEDIUM_GRAY, "speed": 2.5, "health": 1, "damage": 1, "points": 10},
        EnemyType.FAST: {"size": 20, "color": LIGHT_GRAY, "speed": 3.5, "health": 1, "damage": 1, "points": 15},
        EnemyType.TANK: {"size": 35, "color": DARK_GRAY, "speed": 1.8, "health": 3, "damage": 1, "points": 30},
        EnemyType.BOSS: {"size": 50, "color": WHITE, "speed": 2.2, "health": 15, "damage": 2, "points": 100},
        EnemyType.ULTRA: {"size": 70, "color": RED, "speed": 2.5, "health": 30, "damage": 3, "points": 250}
    }

    def __init__(self, x, y, target, enemy_type=EnemyType.NORMAL):
        super().__init__()
        self.type = enemy_type
        self.target = target
        stats = self.ENEMY_STATS[enemy_type]

        # Характеристики
        self.size = stats["size"]
        self.color = stats["color"]
        self.base_speed = stats["speed"]
        self.speed = self.base_speed
        self.max_health = stats["health"]
        self.health = self.max_health
        self.damage = stats["damage"]
        self.points = stats["points"]

        # Поведение
        self.state = "approach"  # "approach", "retreat", "wait"
        self.attack_counter = 0
        self.max_attacks = random.randint(1, 3)
        self.retreat_timer = 0
        self.wait_timer = 0

        # Физика
        self.velocity = [0, 0]
        self.acceleration = 0.1

        # Инициализация
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self._setup_appearance()
        self.rect = self.image.get_rect(center=(x, y))

    def _setup_appearance(self):
        if self.type == EnemyType.ULTRA:
            pygame.draw.polygon(self.image, self.color, [
                (self.size // 2, 0), (self.size, self.size // 3),
                (self.size, 2 * self.size // 3), (self.size // 2, self.size),
                (0, 2 * self.size // 3), (0, self.size // 3)
            ])
            pygame.draw.polygon(self.image, BLACK, [
                (self.size // 2, 0), (self.size, self.size // 3),
                (self.size, 2 * self.size // 3), (self.size // 2, self.size),
                (0, 2 * self.size // 3), (0, self.size // 3)
            ], 2)
        else:
            pygame.draw.rect(self.image, self.color, (0, 0, self.size, self.size), border_radius=self.size // 4)
            pygame.draw.rect(self.image, BLACK, (0, 0, self.size, self.size), 2, border_radius=self.size // 4)

    def update(self, time_slow_factor=1.0):
        if self.state == "approach":
            self._approach_player(time_slow_factor)
        elif self.state == "retreat":
            self._retreat(time_slow_factor)
        elif self.state == "wait":
            self._wait()

        # Применяем скорость
        self.rect.x += self.velocity[0] * time_slow_factor
        self.rect.y += self.velocity[1] * time_slow_factor

        # Трение
        self.velocity[0] *= 0.95
        self.velocity[1] *= 0.95

    def _approach_player(self, time_slow_factor):
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > 0:
            # Ускоряемся в направлении игрока
            self.velocity[0] += (dx / dist) * self.acceleration
            self.velocity[1] += (dy / dist) * self.acceleration

            # Ограничение максимальной скорости
            speed = math.hypot(*self.velocity)
            if speed > self.speed:
                self.velocity[0] = (self.velocity[0] / speed) * self.speed
                self.velocity[1] = (self.velocity[1] / speed) * self.speed

            # Проверка на достижение игрока
            if dist < 50:
                self.attack_counter += 1
                if self.attack_counter >= self.max_attacks:
                    self.state = "retreat"
                    self.retreat_timer = 60

                    # Отскок при отступлении
                    self.velocity[0] = -dx / dist * self.speed * 2
                    self.velocity[1] = -dy / dist * self.speed * 2

    def _retreat(self, time_slow_factor):
        self.retreat_timer -= 1

        # Если время отступления закончилось, ждем перед новой атакой
        if self.retreat_timer <= 0:
            self.state = "wait"
            self.wait_timer = random.randint(30, 90)
            self.attack_counter = 0

            # Замедляемся при ожидании
            self.velocity[0] *= 0.5
            self.velocity[1] *= 0.5

    def _wait(self):
        self.wait_timer -= 1

        # Если время ожидания закончилось, начинаем новую атаку
        if self.wait_timer <= 0:
            self.state = "approach"

            # Новая цель - случайная точка рядом с игроком
            angle = random.uniform(0, 2 * math.pi)
            distance = random.randint(50, 150)
            self.current_target = (
                self.target.rect.centerx + math.cos(angle) * distance,
                self.target.rect.centery + math.sin(angle) * distance
            )


# Главное меню
def main_menu():
    buttons = [
        Button(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 60, "START", None, "Начать новую игру"),
        Button(WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 60, "QUIT", None, "Выйти из игры")
    ]

    while True:
        screen.fill(BLACK)

        # Заголовок
        title = title_font.render("NO HUMANITY", True, WHITE)
        title_shadow = title_font.render("NO HUMANITY", True, DARK_GRAY)
        screen.blit(title_shadow, (WIDTH // 2 - title_shadow.get_width() // 2 + 3, 153))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        subtitle = small_font.render("SURVIVE AT ALL COSTS", True, MEDIUM_GRAY)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 230))

        # Кнопки
        for button in buttons:
            button.draw(screen)

        # Управление
        controls = [
            "WASD - Движение",
            "SHIFT - Рывок",
            "SPACE - Замедление времени",
            "ESC - Пауза"
        ]

        for i, control in enumerate(controls):
            control_text = small_font.render(control, True, MEDIUM_GRAY)
            screen.blit(control_text, (WIDTH // 2 - control_text.get_width() // 2, HEIGHT - 150 + i * 30))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.check_click(event.pos):
                        if button.text == "START":
                            return "start"
                        elif button.text == "QUIT":
                            pygame.quit()
                            sys.exit()

        clock.tick(FPS)


# Магазин улучшений
def shop_screen(points, upgrades):
    buttons = [
        Button(WIDTH // 4 - 150, 200, 300, 60, "SPEED",
               50 + upgrades.get("speed", 0) * 30,
               f"+1 к скорости (сейчас: {5 + upgrades.get('speed', 0)})"),
        Button(WIDTH // 4 - 150, 280, 300, 60, "HEALTH",
               75 + upgrades.get("health", 0) * 50,
               f"+5 к здоровью (сейчас: {20 + upgrades.get('health', 0) * 5})"),
        Button(WIDTH // 4 - 150, 360, 300, 60, "DASH",
               100 + upgrades.get("dash", 0) * 50,
               f"+2 к силе рывка (сейчас: {10 + upgrades.get('dash', 0) * 2})"),
        Button(3 * WIDTH // 4 - 150, 200, 300, 60, "SLOW",
               125 + upgrades.get("slow", 0) * 75,
               f"Увеличивает замедление (сейчас: {0.5 - upgrades.get('slow', 0) * 0.1:.1f}x)"),
        Button(3 * WIDTH // 4 - 150, 280, 300, 60, "COOLDOWN",
               150 + upgrades.get("cooldown", 0) * 100,
               f"-20 к кулдауну (сейчас: {300 - upgrades.get('cooldown', 0) * 20})"),
        Button(WIDTH // 2 - 150, HEIGHT - 120, 300, 60, "START", None, "Начать игру")
    ]

    while True:
        screen.fill(BLACK)

        title = title_font.render("UPGRADES", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        points_text = main_font.render(f"POINTS: {points}", True, WHITE)
        screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, 120))

        for button in buttons:
            button.draw(screen, points)

        stats = [
            f"Speed: {5 + upgrades.get('speed', 0)}",
            f"Health: {20 + upgrades.get('health', 0) * 5}",
            f"Dash: {10 + upgrades.get('dash', 0) * 2}",
            f"Slow: {0.5 - upgrades.get('slow', 0) * 0.1:.1f}x",
            f"Cooldown: {300 - upgrades.get('cooldown', 0) * 20}"
        ]

        for i, stat in enumerate(stats):
            stat_text = small_font.render(stat, True, WHITE)
            x_pos = WIDTH // 4 - 150 if i < 2 else 3 * WIDTH // 4 - 150
            y_pos = 270 + i * 80 if i < 2 else 270 + (i - 2) * 80
            screen.blit(stat_text, (x_pos, y_pos))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.check_click(event.pos, points):
                        if button.text == "SPEED":
                            if points >= button.price:
                                upgrades["speed"] += 1
                                points -= button.price
                        elif button.text == "HEALTH":
                            if points >= button.price:
                                upgrades["health"] += 1
                                points -= button.price
                        elif button.text == "DASH":
                            if points >= button.price:
                                upgrades["dash"] += 1
                                points -= button.price
                        elif button.text == "SLOW":
                            if points >= button.price:
                                upgrades["slow"] += 1
                                points -= button.price
                        elif button.text == "COOLDOWN":
                            if points >= button.price:
                                upgrades["cooldown"] += 1
                                points -= button.price
                        elif button.text == "START":
                            return points, upgrades

        clock.tick(FPS)


# Экран смерти
def death_screen(wave, time, points, total_points):
    buttons = [
        Button(WIDTH // 2 - 150, HEIGHT // 2 + 100, 300, 60, "CONTINUE", None, "В магазин улучшений"),
        Button(WIDTH // 2 - 150, HEIGHT // 2 + 180, 300, 60, "MAIN MENU", None, "В главное меню")
    ]

    while True:
        screen.fill(BLACK)

        title = title_font.render("YOU DIED", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        stats = [
            f"Wave: {wave}",
            f"Time: {time:.1f} sec",
            f"Points: {points}",
            f"Total Points: {total_points}"
        ]

        for i, stat in enumerate(stats):
            stat_text = main_font.render(stat, True, WHITE)
            screen.blit(stat_text, (WIDTH // 2 - stat_text.get_width() // 2, 250 + i * 50))

        for button in buttons:
            button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.check_click(event.pos):
                        if button.text == "CONTINUE":
                            return "continue"
                        elif button.text == "MAIN MENU":
                            return "menu"

        clock.tick(FPS)


# Меню паузы
def pause_menu():
    buttons = [
        Button(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 60, "RESUME", None, "Продолжить игру"),
        Button(WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 60, "QUIT", None, "Выйти в меню")
    ]

    while True:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title = title_font.render("PAUSED", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 200))

        for button in buttons:
            button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "resume"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.check_click(event.pos):
                        if button.text == "RESUME":
                            return "resume"
                        elif button.text == "QUIT":
                            return "quit"

        clock.tick(FPS)


# Основной игровой цикл
def game_loop(upgrades):
    player = Player(WIDTH // 2, HEIGHT // 2, upgrades)
    enemies = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group(player)

    # Параметры волн
    wave = 1
    game_time = 0
    points = 0
    spawn_timer = 0
    enemies_per_wave = 5
    enemies_spawned = 0
    wave_clear = False
    next_wave_timer = 3.0  # 3 секунды между волнами

    # Модификаторы сложности
    enemy_speed_modifier = 1.0
    enemy_health_modifier = 1.0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        game_time += dt
        spawn_timer += dt

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                action = pause_menu()
                if action == "quit":
                    running = False
                    return "menu", points

        # Логика волн
        if wave_clear:
            next_wave_timer -= dt
            if next_wave_timer <= 0:
                wave += 1
                enemies_per_wave = 5 + wave * 2
                enemies_spawned = 0
                wave_clear = False
                next_wave_timer = 3.0

                # Увеличение сложности
                enemy_speed_modifier = min(2.0, 1.0 + wave * 0.05)
                enemy_health_modifier = min(3.0, 1.0 + wave * 0.1)

                # Спавн боссов
                if wave % 5 == 0:
                    spawn_boss(wave // 5, enemies, all_sprites, player, enemy_speed_modifier, enemy_health_modifier)
                if wave % 10 == 0:
                    spawn_ultra_boss(enemies, all_sprites, player, enemy_speed_modifier, enemy_health_modifier)

                show_wave_message(wave)

        # Спавн врагов
        if not wave_clear and enemies_spawned < enemies_per_wave and spawn_timer >= 0.5:
            spawn_timer = 0
            enemies_spawned += 1
            spawn_enemy(wave, enemy_speed_modifier, enemy_health_modifier, enemies, all_sprites, player)

        # Проверка завершения волны
        if not wave_clear and enemies_spawned >= enemies_per_wave and len(enemies) == 0:
            wave_clear = True
            points += wave * 10  # Бонус за завершение волны

        # Замедление времени
        time_slow_factor = 0.5 - upgrades.get("slow", 0) * 0.1 if player.time_slow_active else 1.0

        # Обновление объектов
        player.update()
        for enemy in enemies:
            enemy.update(time_slow_factor)

            # Проверка столкновений
            if pygame.sprite.collide_rect(player, enemy) and not player.invincible:
                if player.take_damage(enemy.damage):
                    return "death", points
                else:
                    enemy.kill()
                    points += enemy.points

        # Отрисовка
        screen.fill(BLACK)
        all_sprites.draw(screen)

        # Интерфейс
        draw_ui(player, wave, game_time, points, next_wave_timer if wave_clear else 0)

        pygame.display.flip()

    return "menu", points


# Вспомогательные функции
def spawn_enemy(wave, speed_mod, health_mod, enemies, all_sprites, player):
    # Уменьшаем шанс появления танков на ранних волнах
    weights = [70 - min(wave, 50), 20 + wave // 2, 5 + wave // 3]
    enemy_type = random.choices(
        [EnemyType.NORMAL, EnemyType.FAST, EnemyType.TANK],
        weights=weights,
        k=1
    )[0]

    # Спавн дальше от игрока
    min_dist = 300
    while True:
        side = random.choice(["top", "bottom", "left", "right"])
        x, y = get_spawn_position(side)
        if math.hypot(x - player.rect.x, y - player.rect.y) > min_dist:
            break

    enemy = Enemy(x, y, player, enemy_type)
    enemy.speed *= speed_mod
    enemy.max_health = int(enemy.max_health * health_mod)
    enemy.health = enemy.max_health

    enemies.add(enemy)
    all_sprites.add(enemy)


def spawn_boss(tier, enemies, all_sprites, player, speed_mod, health_mod):
    side = random.choice(["top", "bottom", "left", "right"])
    x, y = get_spawn_position(side)

    boss = Enemy(x, y, player, EnemyType.BOSS)
    boss.max_health = int((15 + tier * 5) * health_mod)
    boss.health = boss.max_health
    boss.speed = (1.8 + tier * 0.1) * speed_mod
    boss.damage = 2 + tier // 2

    enemies.add(boss)
    all_sprites.add(boss)


def spawn_ultra_boss(enemies, all_sprites, player, speed_mod, health_mod):
    side = random.choice(["top", "bottom", "left", "right"])
    x, y = get_spawn_position(side)

    ultra = Enemy(x, y, player, EnemyType.ULTRA)
    ultra.max_health = int(30 * health_mod)
    ultra.health = ultra.max_health
    ultra.speed = 2.5 * speed_mod
    ultra.damage = 3

    enemies.add(ultra)
    all_sprites.add(ultra)


def get_spawn_position(side):
    if side == "top":
        return random.randint(0, WIDTH), -50
    elif side == "bottom":
        return random.randint(0, WIDTH), HEIGHT + 50
    elif side == "left":
        return -50, random.randint(0, HEIGHT)
    else:
        return WIDTH + 50, random.randint(0, HEIGHT)


def show_wave_message(wave_num):
    message = title_font.render(f"WAVE {wave_num}", True, WHITE)
    screen.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT // 3))
    pygame.display.flip()
    pygame.time.delay(1500)


def draw_ui(player, wave, game_time, points, next_wave_timer):
    # Здоровье
    health_width = 200 * (player.health / player.max_health)
    pygame.draw.rect(screen, DARK_GRAY, (20, 20, 200, 20))
    pygame.draw.rect(screen, GREEN, (20, 20, health_width, 20))
    pygame.draw.rect(screen, BLACK, (20, 20, 200, 20), 2)

    # Статистика
    stats = [
        f"Wave: {wave}",
        f"Points: {points}",
        f"Time: {game_time:.1f}s",
        f"Next Wave: {max(0, next_wave_timer):.1f}s" if next_wave_timer > 0 else ""
    ]

    for i, stat in enumerate(stats):
        if stat:  # Не отображаем пустые строки
            stat_text = small_font.render(stat, True, WHITE)
            screen.blit(stat_text, (WIDTH - stat_text.get_width() - 20, 20 + i * 30))

    # Способности
    if player.dash_cooldown > 0:
        dash_text = small_font.render(f"Dash: {player.dash_cooldown // 60 + 1}s", True, WHITE)
        screen.blit(dash_text, (20, 50))

    if player.time_slow_cooldown > 0:
        slow_text = small_font.render(f"Slow: {player.time_slow_cooldown // 60 + 1}s", True, WHITE)
        screen.blit(slow_text, (20, 80))

    if player.time_slow_active:
        active_text = main_font.render("SLOW MOTION", True, BLUE)
        screen.blit(active_text, (WIDTH // 2 - active_text.get_width() // 2, 20))


# Главная функция
def main():
    pygame.mouse.set_visible(True)

    upgrades = {
        "speed": 0,
        "health": 0,
        "dash": 0,
        "slow": 0,
        "cooldown": 0,
        "points": 0
    }

    action = main_menu()
    if action == "quit":
        pygame.quit()
        return

    while True:
        points, upgrades = shop_screen(upgrades["points"], upgrades)
        upgrades["points"] = points

        result, earned_points = game_loop(upgrades)
        upgrades["points"] += earned_points

        if result == "death":
            action = death_screen(0, 0, earned_points, upgrades["points"])
            if action == "menu":
                main_menu_action = main_menu()
                if main_menu_action == "quit":
                    break
        elif result == "menu":
            main_menu_action = main_menu()
            if main_menu_action == "quit":
                break

    pygame.quit()


if __name__ == "__main__":
    main()