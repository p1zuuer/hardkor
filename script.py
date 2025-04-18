import os
import pygame

def load_image(folder_path):
    images = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            full_path = os.path.join(folder_path, filename)
            image = pygame.image.load(full_path).convert_alpha()
            images.append(image)
    return images
