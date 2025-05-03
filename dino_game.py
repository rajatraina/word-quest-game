
import pygame
import random

pygame.init()

# Game settings
WIDTH, HEIGHT = 640, 240
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dino Run Bonus")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GROUND_HEIGHT = 30
GRAVITY = 0.5
JUMP_VELOCITY = -10
FPS = 60

font = pygame.font.SysFont(None, 32)

def draw_text(text, x, y, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def run_dino_game():
    clock = pygame.time.Clock()
    dino = pygame.Rect(50, HEIGHT - GROUND_HEIGHT - 40, 30, 40)
    dino_vel_y = 0
    on_ground = True

    obstacles = []
    obstacle_timer = 0
    score = 0

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BLACK)

        jump_requested = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                jump_requested = True

        if jump_requested and on_ground:
            dino_vel_y = JUMP_VELOCITY
            on_ground = False

        dino.y += dino_vel_y
        dino_vel_y += GRAVITY
        if dino.y >= HEIGHT - GROUND_HEIGHT - dino.height:
            dino.y = HEIGHT - GROUND_HEIGHT - dino.height
            on_ground = True

        obstacle_timer += 1
        if obstacle_timer > 60:
            obstacle_timer = 0
            height = random.randint(20, 50)
            obstacles.append(pygame.Rect(WIDTH, HEIGHT - GROUND_HEIGHT - height, 20, height))

        for obs in obstacles:
            obs.x -= 5
        obstacles = [obs for obs in obstacles if obs.x > -20]

        for obs in obstacles:
            if dino.colliderect(obs):
                running = False

        pygame.draw.rect(screen, WHITE, dino)
        for obs in obstacles:
            pygame.draw.rect(screen, WHITE, obs)
        pygame.draw.rect(screen, WHITE, (0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))

        score += 1
        draw_text(f"Score: {score}", 10, 10)

        pygame.display.flip()

    pygame.quit()
    print(f"BONUS RESULT: {score // 10}")
    return score // 10

if __name__ == "__main__":
    run_dino_game()
