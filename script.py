import os
import  pygame
def load_image(directory):
    image_list = []
    files = os.listdir(directory)
    for i in files:
        image = pygame.image.load(f'{directory}/{i}').convert_alpha()
        image_list.append(image)
    return  image_list