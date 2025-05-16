import pygame
import random
import math
import sys
from pygame import gfxdraw
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

# Цветовая палитра (монохромная)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)
MEDIUM_GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)

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

        # Стиль кнопки в духе No Humanity
        if not self.active:
            color = DARK_GRAY
            border_color = MEDIUM_GRAY
        elif self.price is not None and points is not None and points < self.price:
            color = DARK_GRAY
            border_color = MEDIUM_GRAY
        else:
            color = LIGHT_GRAY if self.hovered else WHITE
            border_color = BLACK

        # Основная кнопка
        pygame.draw.rect(surface, color, self.rect, border_radius=0)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=0)

        # Текст кнопки
        text_color = BLACK if color in (WHITE, LIGHT_GRAY) else MEDIUM_GRAY
        text_surf = main_font.render(self.text, True, text_color)
        surface.blit(text_surf, (self.rect.centerx - text_surf.get_width() // 2,
                                 self.rect.centery - text_surf.get_height() // 2))

        # Цена (если есть)
        if self.price is not None:
            price_color = WHITE if (points is not None and points >= self.price) else MEDIUM_GRAY
            price_surf = small_font.render(f"{self.price} PTS", True, price_color)
            surface.blit(price_surf, (self.rect.right - price_surf.get_width() - 15,
                                      self.rect.bottom - price_surf.get_height() - 10))

        # Подсказка
        if self.hovered and self.tooltip:
            tooltip_rect = pygame.Rect(mouse_pos[0] + 20, mouse_pos[1],
                                       max(250, len(self.tooltip) * 8), 34)
            pygame.draw.rect(surface, DARK_GRAY, tooltip_rect)
            pygame.draw.rect(surface, WHITE, tooltip_rect, 1)

            tooltip_surf = small_font.render(self.tooltip, True, WHITE)
            surface.blit(tooltip_surf, (tooltip_rect.x + 10, tooltip_rect.y + 7))

    def check_click(self, pos, points=None):
        """Проверяет, была ли нажата кнопка"""
        if self.active and self.rect.collidepoint(pos):
            if self.price is None or (points is not None and points >= self.price):
                return self.price if self.price is not None else 0
        return None


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, upgrades=None):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (20, 20), 18)
        pygame.draw.circle(self.image, BLACK, (20, 20), 18, 2)

        self.rect = self.image.get_rect(center=(x, y))
        upgrades = upgrades or {}
        self.speed = 5 + upgrades.get("speed", 0)
        self.max_health = 3 + upgrades.get("health", 0)
        self.health = self.max_health
        self.invincible = False
        self.invincible_timer = 0
        self.dash_cooldown = 0
        self.time_slow_cooldown = 0
        self.dash_active = False
        self.time_slow_active = False
        self.dash_direction = [0, 0]

    def take_damage(self, damage=1):
        """Обработка получения урона"""
        if self.invincible:
            return False  # Игрок неуязвим, урон не получен

        self.health -= damage
        self.invincible = True
        self.invincible_timer = 60  # 1 секунда неуязвимости

        # Возвращает True, если игрок умер
        return self.health <= 0

    def update(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        # Движение
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += self.speed

        # Нормализация
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        # Рывок
        if keys[pygame.K_LSHIFT] and not self.dash_active and self.dash_cooldown <= 0:
            self.dash_active = True
            self.dash_cooldown = 180
            self.dash_direction = [dx, dy] if (dx != 0 or dy != 0) else [1, 0]

        if self.dash_active:
            dash_speed = 10
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
            self.time_slow_cooldown = 300

        if self.time_slow_active:
            self.time_slow_cooldown -= 1
            if self.time_slow_cooldown <= 240:
                self.time_slow_active = False

        # Кулдауны
        if self.dash_cooldown > 0 and not self.dash_active:
            self.dash_cooldown -= 1

        if self.time_slow_cooldown > 0 and not self.time_slow_active:
            self.time_slow_cooldown -= 1

        # Неуязвимость
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        # Границы экрана
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y))


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, target, enemy_type=EnemyType.NORMAL):
        super().__init__()
        self.type = enemy_type
        self.target = target
        self.abilities = []
        self.ability_cooldown = 0

        # Настройки для разных типов врагов
        if enemy_type == EnemyType.NORMAL:
            self._setup_normal()
        elif enemy_type == EnemyType.FAST:
            self._setup_fast()
        elif enemy_type == EnemyType.TANK:
            self._setup_tank()
        elif enemy_type == EnemyType.BOSS:
            self._setup_boss()
        elif enemy_type == EnemyType.ULTRA:
            self._setup_ultra()

        # Случайные способности для обычных врагов
        if enemy_type in [EnemyType.NORMAL, EnemyType.FAST, EnemyType.TANK]:
            self._assign_random_ability()

        # Настройка изображения
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self._setup_appearance()

        self.rect = self.image.get_rect(center=(x, y))
        self.health = self.max_health
        self.cooldown_timer = 0

    def _setup_normal(self):
        self.size = 25
        self.color = MEDIUM_GRAY
        self.speed = 2.0
        self.max_health = 1
        self.damage = 1
        self.points = 10
        self.abilities_chance = 0.3  # 30% шанс иметь способность

    def _setup_fast(self):
        self.size = 20
        self.color = LIGHT_GRAY
        self.speed = 3.5
        self.max_health = 1
        self.damage = 1
        self.points = 15
        self.abilities_chance = 0.4  # 40% шанс иметь способность

    def _setup_tank(self):
        self.size = 35
        self.color = DARK_GRAY
        self.speed = 1.5
        self.max_health = 5
        self.damage = 2
        self.points = 30
        self.abilities_chance = 0.5  # 50% шанс иметь способность

    def _setup_boss(self):
        self.size = 50
        self.color = WHITE
        self.speed = 2.0
        self.max_health = 15
        self.damage = 3
        self.points = 100
        self.abilities = ["summon", "charge"]  # Боссы всегда имеют способности

    def _setup_ultra(self):
        self.size = 70
        self.color = RED
        self.speed = 2.5
        self.max_health = 30
        self.damage = 5
        self.points = 250
        self.abilities = ["summon", "charge", "laser"]  # Ультра-боссы имеют все способности

    def _setup_appearance(self):
        """Настройка внешнего вида врага"""
        if self.type == EnemyType.ULTRA:
            # Особый вид для ультра-босса
            pygame.draw.polygon(self.image, self.color, [
                (self.size // 2, 0),
                (self.size, self.size // 3),
                (self.size, 2 * self.size // 3),
                (self.size // 2, self.size),
                (0, 2 * self.size // 3),
                (0, self.size // 3)
            ])
            pygame.draw.polygon(self.image, BLACK, [
                (self.size // 2, 0),
                (self.size, self.size // 3),
                (self.size, 2 * self.size // 3),
                (self.size // 2, self.size),
                (0, 2 * self.size // 3),
                (0, self.size // 3)
            ], 2)
        else:
            # Стандартный вид для остальных врагов
            pygame.draw.rect(self.image, self.color, (0, 0, self.size, self.size), border_radius=self.size // 4)
            pygame.draw.rect(self.image, BLACK, (0, 0, self.size, self.size), 2, border_radius=self.size // 4)

    def _assign_random_ability(self):
        """Назначение случайной способности врагу"""
        if random.random() < self.abilities_chance:
            abilities = ["speed_boost", "heal", "explode"]
            self.abilities.append(random.choice(abilities))

    def update(self, time_slow_factor=1.0):
        # Обновление кулдауна способностей
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        # Использование способностей
        if self.abilities and self.cooldown_timer <= 0:
            self._use_ability()
            self.cooldown_timer = 120  # 2 секунды кулдауна

        # Движение к игроку
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > 0:
            dx = dx / dist * self.speed * time_slow_factor
            dy = dy / dist * self.speed * time_slow_factor

        self.rect.x += dx
        self.rect.y += dy

    def _use_ability(self):
        """Использование способностей врага"""
        for ability in self.abilities:
            if ability == "speed_boost":
                self.speed *= 1.5  # Увеличиваем скорость на 50%
            elif ability == "heal" and self.health < self.max_health:
                self.health = min(self.max_health, self.health + 1)  # Восстанавливаем 1 HP
            elif ability == "explode":
                # Взрыв при смерти
                pass  # Обрабатывается при смерти врага
            elif ability == "summon":
                # Босс призывает маленьких врагов (обрабатывается в игровом цикле)
                pass
            elif ability == "charge":
                # Босс делает рывок к игроку
                dx = self.target.rect.centerx - self.rect.centerx
                dy = self.target.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self.rect.x += dx / dist * 20  # Большой рывок
                    self.rect.y += dy / dist * 20
            elif ability == "laser":
                # Ультра-босс стреляет лазером (обрабатывается в игровом цикле)
                pass

    def explode(self):
        """Эффект взрыва врага"""
        if "explode" in self.abilities:
            explosion_radius = 100
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)

            if dist < explosion_radius:
                damage = 2  # Урон от взрыва
                return damage
        return 0


def main_menu():
    """Главное меню игры"""
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

        # Подзаголовок
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
                    if button.check_click(event.pos) is not None:
                        if button.text == "START":
                            return "start"
                        elif button.text == "QUIT":
                            pygame.quit()
                            sys.exit()

        clock.tick(FPS)


def shop_screen(points, upgrades):
    """Экран улучшений"""
    buttons = [
        Button(WIDTH // 4 - 150, 200, 300, 60, "SPEED", 100 + upgrades.get("speed", 0) * 50, "+1 к скорости"),
        Button(WIDTH // 4 - 150, 280, 300, 60, "HEALTH", 150 + upgrades.get("health", 0) * 75, "+1 к здоровью"),
        Button(WIDTH // 4 - 150, 360, 300, 60, "DASH", 200 + upgrades.get("dash", 0) * 100, "+0.5 к силе рывка"),
        Button(3 * WIDTH // 4 - 150, 200, 300, 60, "SLOW", 250 + upgrades.get("slow", 0) * 125, "-0.1 к замедлению"),
        Button(3 * WIDTH // 4 - 150, 280, 300, 60, "COOLDOWN", 300 + upgrades.get("cooldown", 0) * 150,
               "-10% к кулдаунам"),
        Button(WIDTH // 2 - 150, HEIGHT - 120, 300, 60, "START", None, "Начать игру")
    ]

    while True:
        screen.fill(BLACK)

        # Заголовок
        title = title_font.render("UPGRADES", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

        # Очки
        points_text = main_font.render(f"POINTS: {points}", True, WHITE)
        screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, 120))

        # Кнопки
        for button in buttons:
            button.draw(screen, points)

        # Статистика
        stats = [
            f"Speed: {5 + upgrades.get('speed', 0)}",
            f"Health: {3 + upgrades.get('health', 0)}",
            f"Dash: {5 + upgrades.get('dash', 0) * 0.5:.1f}x",
            f"Slow: {0.5 - upgrades.get('slow', 0) * 0.1:.1f}x",
            f"Cooldown: {100 - upgrades.get('cooldown', 0) * 10}%"
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
                    spent = button.check_click(event.pos, points)
                    if spent is not None:
                        if button.text == "SPEED":
                            upgrades["speed"] += 1
                            points -= spent
                        elif button.text == "HEALTH":
                            upgrades["health"] += 1
                            points -= spent
                        elif button.text == "DASH":
                            upgrades["dash"] += 1
                            points -= spent
                        elif button.text == "SLOW":
                            upgrades["slow"] += 1
                            points -= spent
                        elif button.text == "COOLDOWN":
                            upgrades["cooldown"] += 1
                            points -= spent
                        elif button.text == "START":
                            return points, upgrades

        clock.tick(FPS)


def death_screen(wave, time, points, total_points):
    """Экран смерти"""
    buttons = [
        Button(WIDTH // 2 - 150, HEIGHT // 2 + 100, 300, 60, "CONTINUE", None, "В магазин улучшений"),
        Button(WIDTH // 2 - 150, HEIGHT // 2 + 180, 300, 60, "MAIN MENU", None, "В главное меню")
    ]

    while True:
        screen.fill(BLACK)

        # Заголовок
        title = title_font.render("YOU DIED", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        # Статистика
        stats = [
            f"Wave: {wave}",
            f"Time: {time:.1f} sec",
            f"Points: {points}",
            f"Total Points: {total_points}"
        ]

        for i, stat in enumerate(stats):
            stat_text = main_font.render(stat, True, WHITE)
            screen.blit(stat_text, (WIDTH // 2 - stat_text.get_width() // 2, 250 + i * 50))

        # Кнопки
        for button in buttons:
            button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.check_click(event.pos) is not None:
                        if button.text == "CONTINUE":
                            return "continue"
                        elif button.text == "MAIN MENU":
                            return "menu"

        clock.tick(FPS)


def pause_menu():
    """Меню паузы"""
    buttons = [
        Button(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 60, "RESUME", None, "Продолжить игру"),
        Button(WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 60, "QUIT", None, "Выйти в меню")
    ]

    while True:
        # Полупрозрачный фон
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Заголовок
        title = title_font.render("PAUSED", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 200))

        # Кнопки
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
                    if button.check_click(event.pos) is not None:
                        if button.text == "RESUME":
                            return "resume"
                        elif button.text == "QUIT":
                            return "quit"

        clock.tick(FPS)


def game_loop(upgrades):
    """Основной игровой цикл"""
    player = Player(WIDTH // 2, HEIGHT // 2, upgrades)
    enemies = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group(player)
    lasers = []  # Для лазеров ультра-боссов

    wave = 1
    game_time = 0
    points = 0
    spawn_timer = 0
    spawn_interval = 90
    wave_timer = 0
    next_wave_time = 30  # Следующая волна через 30 секунд

    # Для эффектов
    explosion_effects = []
    laser_effects = []

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        game_time += dt
        spawn_timer += 1
        wave_timer += dt

        # Обновление эффектов
        for effect in explosion_effects[:]:
            effect["timer"] -= 1
            if effect["timer"] <= 0:
                explosion_effects.remove(effect)

        for laser in laser_effects[:]:
            laser["timer"] -= 1
            if laser["timer"] <= 0:
                laser_effects.remove(laser)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                action = pause_menu()
                if action == "quit":
                    running = False
                    return "menu", points

        # Спавн врагов
        if spawn_timer >= spawn_interval or (len(enemies) == 0 and wave_timer >= next_wave_time):
            if len(enemies) == 0:
                wave += 1
                wave_timer = 0
                next_wave_time = max(10, 30 - wave)  # Уменьшаем время между волнами

            spawn_timer = 0
            enemy_types = [EnemyType.NORMAL] * 70 + [EnemyType.FAST] * 20 + [EnemyType.TANK] * 10

            # Добавляем боссов и ультра-боссов
            if wave % 5 == 0:
                enemy_types += [EnemyType.BOSS] * 20
            if wave % 10 == 0:
                enemy_types += [EnemyType.ULTRA] * 5

            enemy_type = random.choice(enemy_types)
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                x, y = random.randint(0, WIDTH), -50
            elif side == "bottom":
                x, y = random.randint(0, WIDTH), HEIGHT + 50
            elif side == "left":
                x, y = -50, random.randint(0, HEIGHT)
            else:
                x, y = WIDTH + 50, random.randint(0, HEIGHT)

            enemy = Enemy(x, y, player, enemy_type)
            enemies.add(enemy)
            all_sprites.add(enemy)

            # Уменьшаем интервал спавна с каждой волной
            spawn_interval = max(30, 90 - wave * 5)

        # Обновление объектов
        time_slow_factor = 0.5 - upgrades.get("slow", 0) * 0.1 if player.time_slow_active else 1.0

        player.update()
        for enemy in enemies:
            enemy.update(time_slow_factor)

            # Проверка способности "summon" у боссов
            if enemy.type in [EnemyType.BOSS, EnemyType.ULTRA] and random.random() < 0.01:
                for _ in range(3):  # Босс призывает 3 маленьких врага
                    minion_type = random.choice([EnemyType.NORMAL, EnemyType.FAST])
                    minion = Enemy(enemy.rect.centerx, enemy.rect.centery, player, minion_type)
                    enemies.add(minion)
                    all_sprites.add(minion)

            # Проверка способности "laser" у ультра-боссов
            if enemy.type == EnemyType.ULTRA and random.random() < 0.005:
                # Создаем лазер от ультра-босса к игроку
                laser = {
                    "start": (enemy.rect.centerx, enemy.rect.centery),
                    "end": (player.rect.centerx, player.rect.centery),
                    "timer": 30,  # Длительность эффекта лазера
                    "damage": 3  # Урон от лазера
                }
                laser_effects.append(laser)

                # Проверяем попадание лазера в игрока
                if not player.invincible:
                    player.take_damage(laser["damage"])

            # Столкновения
            if pygame.sprite.collide_rect(player, enemy) and not player.invincible:
                if player.take_damage(enemy.damage):
                    return "death", points
                else:
                    player.invincible = True
                    player.invincible_timer = 60

                    # Проверка способности "explode"
                    explosion_damage = enemy.explode()
                    if explosion_damage > 0:
                        explosion_effects.append({
                            "pos": (enemy.rect.centerx, enemy.rect.centery),
                            "radius": 100,
                            "timer": 30
                        })
                        if player.take_damage(explosion_damage):
                            return "death", points

                    enemy.kill()
                    points += enemy.points

        # Отрисовка
        screen.fill(BLACK)

        # Отрисовка эффектов
        for effect in explosion_effects:
            pygame.draw.circle(screen, RED, effect["pos"], effect["radius"], 2)

        for laser in laser_effects:
            pygame.draw.line(screen, RED, laser["start"], laser["end"], 3)

        all_sprites.draw(screen)

        # Интерфейс
        # Полоска здоровья
        health_width = 200 * (player.health / player.max_health)
        pygame.draw.rect(screen, DARK_GRAY, (20, 20, 200, 20))
        pygame.draw.rect(screen, WHITE, (20, 20, health_width, 20))
        pygame.draw.rect(screen, BLACK, (20, 20, 200, 20), 2)

        # Статистика
        stats = [
            f"Wave: {wave}",
            f"Points: {points}",
            f"Time: {game_time:.1f}s",
            f"Next Wave: {max(0, next_wave_time - wave_timer):.1f}s"
        ]

        for i, stat in enumerate(stats):
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
            active_text = main_font.render("SLOW MOTION", True, WHITE)
            screen.blit(active_text, (WIDTH // 2 - active_text.get_width() // 2, 20))

        pygame.display.flip()

    return "menu", points


def main():
    """Главная функция"""
    pygame.mouse.set_visible(True)

    # Начальные улучшения
    upgrades = {
        "speed": 0,
        "health": 0,
        "dash": 0,
        "slow": 0,
        "cooldown": 0,
        "points": 0
    }

    # Главное меню
    action = main_menu()
    if action == "quit":
        pygame.quit()
        return

    while True:
        # Магазин улучшений
        points, upgrades = shop_screen(upgrades["points"], upgrades)
        upgrades["points"] = points

        # Игровой цикл
        result, earned_points = game_loop(upgrades)
        upgrades["points"] += earned_points

        # Обработка результата
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