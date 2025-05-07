import pygame
import os
import sys
import random
from pygame import font

from script import load_image  # Предположим, что эта функция уже есть

pygame.init()
current_path = os.path.dirname(__file__)
os.chdir(current_path)

WIDTH, HEIGHT = 1200, 800
FPS = 60
sc = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FONT = pygame.font.Font(None, 50)

player_idle_images = load_image('image/golem/idle')
player_run_images = load_image('image/golem/run')
bat_run_images = load_image('image/bat/run')


def draw_menu():
    sc.fill('black')
    title = FONT.render("Главное меню", True, (255, 255, 255))
    start_btn = FONT.render("1. Начать игру", True, (200, 200, 200))
    quit_btn = FONT.render("2. Выйти", True, (200, 200, 200))
    sc.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
    sc.blit(start_btn, (WIDTH // 2 - start_btn.get_width() // 2, HEIGHT // 2))
    sc.blit(quit_btn, (WIDTH // 2 - quit_btn.get_width() // 2, HEIGHT // 2 + 60))
    pygame.display.flip()


def main_menu():
    while True:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return True
                elif event.key == pygame.K_2:
                    pygame.quit()
                    sys.exit()
        clock.tick(30)


class Player(pygame.sprite.Sprite):
    def __init__(self, idle_images, run_images, pos):
        super().__init__()
        self.original_idle = idle_images
        self.original_run = run_images
        self.facing_left = False
        self.image = idle_images[0]
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.speed = 5
        self.frame = 0
        self.anim_timer = 0
        self.anim_delay = 100
        self.moving = False

    def update(self):
        keys = pygame.key.get_pressed()
        self.moving = False
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
            self.facing_left = True
            self.moving = True
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            self.facing_left = False
            self.moving = True
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
            self.moving = True
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed
            self.moving = True

        # Ограничение в пределах экрана
        self.rect.clamp_ip(sc.get_rect())

        # Отражение по направлению
        if self.facing_left:
            self.idle_images = [pygame.transform.flip(img, True, False) for img in self.original_idle]
            self.run_images = [pygame.transform.flip(img, True, False) for img in self.original_run]
        else:
            self.idle_images = self.original_idle
            self.run_images = self.original_run

        now = pygame.time.get_ticks()
        if self.moving:
            if now - self.anim_timer > self.anim_delay:
                self.anim_timer = now
                self.frame = (self.frame + 1) % len(self.run_images)
            self.image = self.run_images[self.frame]
        else:
            self.image = self.idle_images[0]


class Timer:
    def __init__(self):
        self.count = 0
        self.time = 0

    def update(self):
        self.count += 1
        self.time = self.count // FPS
        text = font.SysFont('arial', 40).render(f'{self.time}', True, 'Black')
        sc.blit(text, (100, 20))


class Score:
    def __init__(self):
        self.points = 0

    def draw(self):
        score_text = FONT.render(f"Счёт: {self.points}", True, (255, 255, 255))
        sc.blit(score_text, (WIDTH - 200, 20))


class Enemy(pygame.sprite.Sprite):
    def __init__(self, images, player):
        super().__init__()
        self.original_images = images  # Сохраняем оригиналы
        self.images = images
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.frame = 0
        self.anim_timer = 0
        self.anim_delay = 100
        self.speed = 2
        self.facing_left = False
        self.player = player
        self.angle_offset = random.uniform(-0.1, 0.1)  # Случайное смещение для пути

    def update(self):
        # Вычисляем направление к игроку
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance != 0:
            dx, dy = dx / distance, dy / distance  # Нормализуем направление

        # Добавляем небольшое случайное отклонение в путь врага
        dx += self.angle_offset
        dy += self.angle_offset

        # Обновляем позицию врага
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed

        # Поворот врага в нужную сторону
        if dx < 0 and not self.facing_left:
            self.facing_left = True
            self.images = [pygame.transform.flip(img, True, False) for img in self.original_images]
        elif dx > 0 and self.facing_left:
            self.facing_left = False
            self.images = self.original_images

        # Обновляем анимацию
        now = pygame.time.get_ticks()
        if now - self.anim_timer > self.anim_delay:
            self.anim_timer = now
            self.frame = (self.frame + 1) % len(self.images)
            self.image = self.images[self.frame]


def spawn_enemy():
    if random.randint(1, 100) <= 2:
        enemy = Enemy(bat_run_images, player)

        # Появление из случайной стороны
        side = random.choice(['left', 'right', 'top', 'bottom'])
        if side == 'left':
            enemy.rect.x = -100
            enemy.rect.y = random.randint(0, HEIGHT)
        elif side == 'right':
            enemy.rect.x = WIDTH + 100
            enemy.rect.y = random.randint(0, HEIGHT)
        elif side == 'top':
            enemy.rect.x = random.randint(0, WIDTH)
            enemy.rect.y = -100
        elif side == 'bottom':
            enemy.rect.x = random.randint(0, WIDTH)
            enemy.rect.y = HEIGHT + 100

        enemy_group.add(enemy)


def restart():
    global player_group, enemy_group, player, timer, score_obj
    player_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    player = Player(player_idle_images, player_run_images, pos=(WIDTH // 2, HEIGHT // 2))
    player_group.add(player)
    timer = Timer()
    score_obj = Score()


def game_lvl():
    sc.fill('grey')
    timer.update()
    spawn_enemy()

    player_group.update()
    enemy_group.update()

    player_group.draw(sc)
    enemy_group.draw(sc)

    score_obj.draw()

    # Столкновение с врагами
    if pygame.sprite.spritecollideany(player, enemy_group):
        game_over()
        return

    pygame.display.flip()


def game_over():
    text = FONT.render("Вы проиграли! Перезапуск...", True, (255, 0, 0))
    sc.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.delay(2000)
    restart()


if main_menu():
    restart()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        game_lvl()
        clock.tick(FPS)
