import pygame
import os
import sys
import random
import math
from pygame import gfxdraw
from collections import defaultdict

# Инициализация
pygame.init()

# Настройки
WIDTH, HEIGHT = 1200, 800
FPS = 60
sc = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NO HUMANITY: ULTIMATE EDITION")
clock = pygame.time.Clock()
FONT = pygame.font.Font(None, 50)
BIG_FONT = pygame.font.Font(None, 100)
SMALL_FONT = pygame.font.Font(None, 36)

# Цвета
RED = (255, 50, 50)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (50, 255, 50)
GOLD = (255, 215, 0)
BLUE = (100, 100, 255)
BROWN = (150, 75, 0)


# Класс кнопки для магазина
class Button:
    def __init__(self, x, y, width, height, text, price):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.price = price
        self.active = True

    def draw(self, surface, points):
        color = GREEN if self.active and points >= self.price else (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect, 0, 10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, 10)

        text = FONT.render(self.text, True, WHITE)
        price_text = SMALL_FONT.render(f"Цена: {self.price}", True, GOLD if points >= self.price else RED)

        surface.blit(text, (self.rect.x + 10, self.rect.y + 10))
        surface.blit(price_text, (self.rect.x + 10, self.rect.y + 50))

    def check_click(self, pos, points):
        if self.rect.collidepoint(pos) and self.active and points >= self.price:
            return self.price
        return 0


# Класс игрока с способностями
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, upgrades=None):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 255, 0), (15, 15), 15)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 7 + (upgrades["speed"] if upgrades else 0)
        self.health = 1 + (upgrades["health"] if upgrades else 0)
        self.invincible = False
        self.abilities = {
            "dash": {"cooldown": 0, "max_cooldown": 180, "duration": 15, "active": False},
            "time_slow": {"cooldown": 0, "max_cooldown": 300, "duration": 60, "active": False}
        }
        self.dash_direction = [0, 0]

    def update(self):
        keys = pygame.key.get_pressed()

        # Обработка способностей
        if keys[pygame.K_LSHIFT] and self.abilities["dash"]["cooldown"] <= 0:
            self.abilities["dash"]["active"] = True
            self.abilities["dash"]["cooldown"] = self.abilities["dash"]["max_cooldown"]
            self.dash_direction = [0, 0]
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.dash_direction[0] = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.dash_direction[0] = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.dash_direction[1] = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.dash_direction[1] = 1

        if keys[pygame.K_SPACE] and self.abilities["time_slow"]["cooldown"] <= 0:
            self.abilities["time_slow"]["active"] = True
            self.abilities["time_slow"]["cooldown"] = self.abilities["time_slow"]["max_cooldown"]

        # Движение
        dx, dy = 0, 0
        if not self.abilities["dash"]["active"]:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= self.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += self.speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= self.speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += self.speed
        else:
            dx, dy = self.dash_direction[0] * self.speed * 3, self.dash_direction[1] * self.speed * 3
            self.abilities["dash"]["duration"] -= 1
            if self.abilities["dash"]["duration"] <= 0:
                self.abilities["dash"]["active"] = False
                self.abilities["dash"]["duration"] = 15

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(sc.get_rect())

        # Обновление перезарядки способностей
        for ability in self.abilities.values():
            if ability["cooldown"] > 0:
                ability["cooldown"] -= 1


# Классы врагов
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, target):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0), (10, 10), 10)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = random.uniform(1.5, 3.0)
        self.target = target
        self.angle = random.uniform(0, 6.28)
        self.health = 1

    def update(self, time_slow=False):
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist > 0:
            dx, dy = dx / dist, dy / dist

        self.angle += random.uniform(-0.1, 0.1)
        dx += 0.3 * math.cos(self.angle)
        dy += 0.3 * math.sin(self.angle)

        speed = self.speed * 0.5 if time_slow else self.speed
        self.rect.x += dx * speed
        self.rect.y += dy * speed


class FastEnemy(Enemy):
    def __init__(self, x, y, target):
        super().__init__(x, y, target)
        self.speed *= 1.8
        self.image.fill((255, 100, 100))


class TankEnemy(Enemy):
    def __init__(self, x, y, target):
        super().__init__(x, y, target)
        self.speed *= 0.6
        self.health = 3
        self.image.fill((100, 100, 255))


class BossEnemy(Enemy):
    def __init__(self, x, y, target):
        super().__init__(x, y, target)
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 255), (20, 20), 20)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2.0
        self.health = 10
        self.attack_cooldown = 0

    def update(self, time_slow=False):
        super().update(time_slow)
        if self.attack_cooldown <= 0:
            self.attack_cooldown = 60
            return True  # Создать мини-врагов
        self.attack_cooldown -= 1
        return False


# Разрушаемые объекты
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(BROWN)
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 3

    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True
        return False


# Эффекты
def shake_screen(intensity=10, duration=200):
    for _ in range(duration // 10):
        offset = (random.randint(-intensity, intensity), random.randint(-intensity, intensity))
        sc.blit(sc, offset)
        pygame.display.flip()
        pygame.time.delay(10)


def draw_blood(pos):
    for _ in range(20):
        radius = random.randint(2, 5)
        x, y = pos[0] + random.randint(-20, 20), pos[1] + random.randint(-20, 20)
        color = (150 + random.randint(0, 50), 0, 0)
        pygame.gfxdraw.filled_circle(sc, x, y, radius, color)


def create_particles(position, color, count=20):
    particles = []
    for _ in range(count):
        particle = {
            "pos": [position[0], position[1]],
            "vel": [random.uniform(-2, 2), random.uniform(-2, 2)],
            "color": color,
            "life": random.randint(30, 60)
        }
        particles.append(particle)
    return particles


def draw_particles(particles):
    for p in particles[:]:
        pygame.draw.circle(sc, p["color"], (int(p["pos"][0]), int(p["pos"][1])), 3)
        p["pos"][0] += p["vel"][0]
        p["pos"][1] += p["vel"][1]
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)


# Магазин улучшений
def show_shop(points, upgrades):
    buttons = [
        Button(WIDTH // 2 - 200, 200, 400, 100, "Скорость +1", 100 + upgrades["speed"] * 50),
        Button(WIDTH // 2 - 200, 350, 400, 100, "Здоровье +1", 150 + upgrades["health"] * 75),
        Button(WIDTH // 2 - 200, 500, 400, 100, "Запустить игру", 0)
    ]

    running = True
    while running:
        sc.fill(BLACK)

        title = BIG_FONT.render("МАГАЗИН УЛУЧШЕНИЙ", True, GOLD)
        points_text = FONT.render(f"Очков: {points}", True, WHITE)
        stats_text = FONT.render(
            f"Текущие: Скорость {upgrades['speed']} | Здоровье {upgrades['health']}",
            True, WHITE
        )

        sc.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        sc.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, 150))
        sc.blit(stats_text, (WIDTH // 2 - stats_text.get_width() // 2, HEIGHT - 100))

        for button in buttons:
            button.draw(sc, points)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i, button in enumerate(buttons):
                        spent = button.check_click(event.pos, points)
                        if spent > 0 and i < 2:  # Первые две кнопки - улучшения
                            points -= spent
                            if i == 0:  # Скорость
                                upgrades["speed"] += 1
                                buttons[0].price = 100 + upgrades["speed"] * 50
                            elif i == 1:  # Здоровье
                                upgrades["health"] += 1
                                buttons[1].price = 150 + upgrades["health"] * 75
                        elif i == 2:  # Кнопка запуска
                            return points, upgrades

        clock.tick(FPS)


# Меню паузы
def pause_menu():
    paused = True
    while paused:
        sc.fill(BLACK)
        title = BIG_FONT.render("ПАУЗА", True, WHITE)
        hint1 = FONT.render("Нажми ESC чтобы продолжить", True, WHITE)
        hint2 = FONT.render("Нажми Q чтобы выйти в меню", True, WHITE)

        sc.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))
        sc.blit(hint1, (WIDTH // 2 - hint1.get_width() // 2, HEIGHT // 2))
        sc.blit(hint2, (WIDTH // 2 - hint2.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = False
                elif event.key == pygame.K_q:
                    return False  # Выход в главное меню

        clock.tick(5)
    return True


# Основной игровой цикл
def main():
    upgrades = {"speed": 0, "health": 0}
    total_points = 0
    achievements = {
        "survive_30s": {"unlocked": False, "name": "30 секунд выживания"},
        "survive_60s": {"unlocked": False, "name": "1 минута выживания"},
        "wave_5": {"unlocked": False, "name": "5 волна"}
    }

    while True:
        player = Player(WIDTH // 2, HEIGHT // 2, upgrades)
        all_sprites = pygame.sprite.Group(player)
        enemies = pygame.sprite.Group()
        obstacles = pygame.sprite.Group()
        particles = []

        # Создаем несколько препятствий
        for _ in range(5):
            x = random.randint(100, WIDTH - 100)
            y = random.randint(100, HEIGHT - 100)
            obstacles.add(Obstacle(x, y))

        game_time = 0
        wave_number = 1
        running = True
        game_over = False
        time_slow_active = False
        achievement_shown = False

        while running:
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not pause_menu():
                            running = False
                            game_over = False
                            break

            if not game_over:
                # Обновление игрового времени
                game_time += 1 / FPS

                # Проверка достижений
                if not achievement_shown:
                    if game_time >= 30 and not achievements["survive_30s"]["unlocked"]:
                        achievements["survive_30s"]["unlocked"] = True
                        achievement_shown = True
                    elif game_time >= 60 and not achievements["survive_60s"]["unlocked"]:
                        achievements["survive_60s"]["unlocked"] = True
                        achievement_shown = True
                    elif wave_number >= 5 and not achievements["wave_5"]["unlocked"]:
                        achievements["wave_5"]["unlocked"] = True
                        achievement_shown = True

                # Спавн волн врагов
                if len(enemies) == 0:
                    wave_number += 1
                    achievement_shown = False
                    spawn_wave(wave_number, player, enemies)

                # Обновление времени замедления
                time_slow_active = player.abilities["time_slow"]["active"] and player.abilities["time_slow"][
                    "duration"] > 0
                if player.abilities["time_slow"]["active"]:
                    player.abilities["time_slow"]["duration"] -= 1
                    if player.abilities["time_slow"]["duration"] <= 0:
                        player.abilities["time_slow"]["active"] = False

                # Обновление объектов
                all_sprites.update()
                for enemy in enemies:
                    if isinstance(enemy, BossEnemy) and enemy.update(time_slow_active):
                        # Босс создает мини-врагов
                        for _ in range(3):
                            enemies.add(Enemy(enemy.rect.centerx, enemy.rect.centery, player))
                    else:
                        enemy.update(time_slow_active)

                # Проверка столкновений
                for enemy in enemies:
                    if pygame.sprite.collide_rect(player, enemy) and not player.invincible:
                        player.health -= 1
                        if player.health <= 0:
                            draw_blood(player.rect.center)
                            shake_screen()
                            game_over = True
                            total_points += int(game_time * 10)  # 10 очков за секунду
                        else:
                            player.invincible = True
                            pygame.time.set_timer(pygame.USEREVENT, 1000)  # 1 сек неуязвимости

                # Отрисовка
                sc.fill(BLACK)

                # Рисуем препятствия
                obstacles.draw(sc)

                # Рисуем врагов
                for enemy in enemies:
                    if random.random() < 0.1 and not time_slow_active:
                        offset = (random.randint(-1, 1), random.randint(-1, 1))
                        sc.blit(enemy.image, (enemy.rect.x + offset[0], enemy.rect.y + offset[1]))
                    else:
                        sc.blit(enemy.image, enemy.rect)

                # Рисуем игрока
                if player.invincible and pygame.time.get_ticks() % 200 < 100:
                    pass  # Мигание при неуязвимости
                else:
                    sc.blit(player.image, player.rect)

                # Рисуем частицы
                draw_particles(particles)

                # Интерфейс
                time_text = FONT.render(f"Время: {int(game_time)} сек", True, WHITE)
                wave_text = FONT.render(f"Волна: {wave_number}", True, WHITE)
                health_text = FONT.render(f"Жизни: {player.health}", True, RED if player.health == 1 else GREEN)

                # Отображение перезарядки способностей
                dash_cooldown = max(0, player.abilities["dash"]["cooldown"])
                dash_text = SMALL_FONT.render(f"Рывок: {dash_cooldown // FPS + 1}c", True, WHITE)

                time_slow_cooldown = max(0, player.abilities["time_slow"]["cooldown"])
                time_slow_text = SMALL_FONT.render(f"Замедление: {time_slow_cooldown // FPS + 1}c", True, WHITE)

                sc.blit(time_text, (10, 10))
                sc.blit(wave_text, (10, 50))
                sc.blit(health_text, (10, 90))
                sc.blit(dash_text, (WIDTH - 200, 10))
                sc.blit(time_slow_text, (WIDTH - 200, 50))

                # Отображение активного замедления времени
                if time_slow_active:
                    slow_text = FONT.render("ЗАМЕДЛЕНИЕ!", True, BLUE)
                    sc.blit(slow_text, (WIDTH // 2 - slow_text.get_width() // 2, 10))

                # Отображение достижений
                if achievement_shown:
                    for i, (key, ach) in enumerate(achievements.items()):
                        if ach["unlocked"] and ach.get("new", False):
                            ach_text = FONT.render(f"Достижение: {ach['name']}!", True, GOLD)
                            sc.blit(ach_text, (WIDTH // 2 - ach_text.get_width() // 2, HEIGHT // 2 - 100 + i * 50))
                            ach["new"] = False
            else:
                # Экран смерти
                sc.fill(BLACK)
                death_text = BIG_FONT.render("ВЫ ПРОИГРАЛИ!", True, RED)
                points_text = FONT.render(f"Заработано очков: {int(game_time * 10)}", True, WHITE)
                total_text = FONT.render(f"Всего очков: {total_points}", True, GOLD)
                hint_text = SMALL_FONT.render("Нажмите ПРОБЕЛ для магазина", True, WHITE)

                sc.blit(death_text, (WIDTH // 2 - death_text.get_width() // 2, HEIGHT // 2 - 100))
                sc.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, HEIGHT // 2))
                sc.blit(total_text, (WIDTH // 2 - total_text.get_width() // 2, HEIGHT // 2 + 50))
                sc.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT // 2 + 150))

                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    total_points, upgrades = show_shop(total_points, upgrades)
                    running = False

            pygame.display.flip()
            clock.tick(FPS)


def spawn_wave(wave_number, player, enemies):
    enemies_to_spawn = 5 + wave_number * 2

    for _ in range(enemies_to_spawn):
        side = random.choice(["left", "right", "top", "bottom"])
        if side == "left":
            x, y = -20, random.randint(0, HEIGHT)
        elif side == "right":
            x, y = WIDTH + 20, random.randint(0, HEIGHT)
        elif side == "top":
            x, y = random.randint(0, WIDTH), -20
        else:
            x, y = random.randint(0, WIDTH), HEIGHT + 20

        # Выбираем тип врага в зависимости от волны
        if wave_number > 3 and random.random() < 0.3:
            if random.random() < 0.5:
                enemies.add(FastEnemy(x, y, player))
            else:
                enemies.add(TankEnemy(x, y, player))
        else:
            enemies.add(Enemy(x, y, player))

    # Каждые 5 волн добавляем босса
    if wave_number % 5 == 0:
        enemies.add(BossEnemy(WIDTH // 2, -100, player))


if __name__ == "__main__":
    main()