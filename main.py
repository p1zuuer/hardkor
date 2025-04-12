import pygame
import os
import sys

pygame.init()
current_path = os.path.dirname(__file__)
os.chdir(current_path)

WIDTH, HEIGHT = 1200, 800
FPS = 60
sc = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FONT = pygame.font.Font(None, 50)

from load import *


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
    def __init__(self, images, pos):
        super().__init__()
        self.images = [pygame.transform.scale(img, (30, 30)) for img in images]
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.speed = 5
        self.pos = self.rect.center

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed
        self.pos = self.rect.center
        sc.blit(player_image, (0, 0))


def restart():
    global player_group, hand_group
    player_group = pygame.sprite.Group()
    hand_group = pygame.sprite.Group()


def game_lvl():
    sc.fill('grey')
    player_group.update()
    player_group.draw(sc)
    hand_group.update()
    hand_group.draw(sc)
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
