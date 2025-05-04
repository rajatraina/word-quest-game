import pygame
import random

pygame.init()

WIDTH, HEIGHT = 640, 240
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dino Run - Pixel Style")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GROUND_HEIGHT = 30
GRAVITY = 0.6
JUMP_VELOCITY = -10
FPS = 60

font = pygame.font.SysFont(None, 32)

def draw_text(text, x, y, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def draw_dino(surface, x, y, frame, crouching):
    color = (200, 200, 200)
    if crouching:
        pygame.draw.rect(surface, color, (x, y + 20, 40, 20))
        pygame.draw.rect(surface, BLACK, (x + 5, y + 25, 5, 5))
    else:
        pygame.draw.rect(surface, color, (x, y, 30, 40))
        pygame.draw.rect(surface, BLACK, (x + 5, y + 10, 5, 5))
        leg_x = x + (5 if frame == 0 else 20)
        pygame.draw.rect(surface, BLACK, (leg_x, y + 35, 5, 5))

def draw_cactus(surface, rect):
    pygame.draw.rect(surface, (0, 255, 0), rect)
    pygame.draw.rect(surface, (0, 200, 0), rect.inflate(-6, -6))

def draw_bird(surface, rect, frame):
    color = (255, 100, 100)
    pygame.draw.ellipse(surface, color, rect)
    wing_y = rect.y + (5 if frame == 0 else -5)
    pygame.draw.line(surface, color, (rect.centerx, rect.centery), (rect.centerx + 10, wing_y), 2)

def draw_rock(surface, rect):
    pygame.draw.rect(surface, (150, 150, 150), rect)
    pygame.draw.circle(surface, (100, 100, 100), rect.center, rect.width // 2)

def run_dino_game():
    clock = pygame.time.Clock()
    dino = pygame.Rect(50, HEIGHT - GROUND_HEIGHT - 40, 30, 40)
    crouch_offset = 15
    dino_vel_y = 0
    on_ground = True
    is_crouching = False

    obstacles = []
    obstacle_timer = 0
    score = 0
    dino_frame = 0
    bird_frame = 0

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BLACK)

        jump = False
        crouch = False
        dino_frame = (dino_frame + 1) % 20
        bird_frame = (bird_frame + 1) % 20

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] and on_ground:
            jump = True
        if keys[pygame.K_DOWN]:
            crouch = True

        if jump:
            dino_vel_y = JUMP_VELOCITY
            on_ground = False
        if crouch and on_ground and not is_crouching:
            dino.y += crouch_offset
            dino.height -= crouch_offset
            is_crouching = True
        elif not crouch and is_crouching:
            dino.y -= crouch_offset
            dino.height += crouch_offset
            is_crouching = False

        dino.y += dino_vel_y
        dino_vel_y += GRAVITY
        if dino.y >= HEIGHT - GROUND_HEIGHT - dino.height:
            dino.y = HEIGHT - GROUND_HEIGHT - dino.height
            on_ground = True

        obstacle_timer += 1
        if obstacle_timer > 60:
            obstacle_timer = 0
            roll = random.random()
            if roll < 0.6:
                height = random.choice([30, 40])
                obstacles.append({
                    "rect": pygame.Rect(WIDTH, HEIGHT - GROUND_HEIGHT - height, 20, height),
                    "type": "cactus"
                })
            elif roll < 0.9:
                y_pos = random.choice([
                    HEIGHT - GROUND_HEIGHT - 40,
                    HEIGHT - GROUND_HEIGHT - 60,
                    HEIGHT - GROUND_HEIGHT - 100
                ])
                obstacles.append({
                    "rect": pygame.Rect(WIDTH, y_pos, 30, 20),
                    "type": "bird"
                })
            else:
                size = 20
                obstacles.append({
                    "rect": pygame.Rect(WIDTH, HEIGHT - GROUND_HEIGHT - size, size, size),
                    "type": "rock"
                })

        for obs in obstacles:
            obs["rect"].x -= 6
        obstacles = [obs for obs in obstacles if obs["rect"].x > -40]

        for obs in obstacles:
            if dino.colliderect(obs["rect"]):
                running = False

        draw_dino(screen, dino.x, dino.y, dino_frame // 10, is_crouching)
        for obs in obstacles:
            if obs["type"] == "cactus":
                draw_cactus(screen, obs["rect"])
            elif obs["type"] == "bird":
                draw_bird(screen, obs["rect"], bird_frame // 10)
            elif obs["type"] == "rock":
                draw_rock(screen, obs["rect"])

        pygame.draw.rect(screen, WHITE, (0, HEIGHT - GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))
        score += 1
        draw_text(f"Score: {score}", 10, 10)
        pygame.display.flip()

    pygame.quit()
    print(f"BONUS RESULT: {score // 10}")
    return score // 10

if __name__ == "__main__":
    run_dino_game()