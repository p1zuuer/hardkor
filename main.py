import pygame
import os
import sys
import random

from pygame import font
from pygame.examples.vgrade import timer


from script import load_image
import time

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
bat_attack_image = load_image('image/bat/attack')




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
        self.idle_images = idle_images
        self.run_images = run_images

        self.image = self.idle_images[0]
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

        self.pos = self.rect.center


class Timer():
    def __init__(self):
        self.count = 0
        self.time = 0
    def update(self):
        self.count += 1
        self.time = self.count // FPS
        text = font.SysFont('aria', 40).render(f'{ self.time }', True, 'Black')

        sc.blit(text, (100,20))





class score(pygame.sprite.Sprite):
    score_text = FONT.render("score:", True, (255, 255, 255))


class Food(pygame.sprite.Sprite):
    def __init__(self, image):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(image, (20, 20))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH - 20)
        self.rect.y = random.randint(0, HEIGHT - 20)


def restart():
    global player_group, enemy_group, player,timer
    player_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()

    player = Player(player_idle_images, player_run_images, pos=(WIDTH // 2, HEIGHT // 2))
    player_group.add(player)
    timer = Timer()


def game_lvl():
    sc.fill('grey')
    timer.update()
    player_group.update()
    player_group.draw(sc)

    pygame.display.flip()


if main_menu():
    restart()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        game_lvl()
        clock.tick(FPS)
