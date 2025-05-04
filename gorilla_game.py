import pygame
import math
import random

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gorilla Banana Defense")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (100, 100, 255)
ORANGE = (255, 100, 0)
FPS = 60

font = pygame.font.SysFont(None, 28)

def draw_text(text, x, y, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def create_skyline(num_buildings):
    buildings = []
    width = WIDTH // num_buildings
    for i in range(num_buildings):
        height = random.randint(100, 300)
        buildings.append(pygame.Rect(i * width, HEIGHT - height, width - 5, height))
    return buildings

def place_rockets(buildings, num_rockets):
    choices = random.sample(buildings[2:], min(num_rockets, len(buildings) - 2))
    rockets = []
    for b in choices:
        rocket = pygame.Rect(b.centerx - 10, b.top - 30, 20, 30)
        rockets.append(rocket)
    return rockets

def run_gorilla_game():
    clock = pygame.time.Clock()
    buildings = create_skyline(10)
    gorilla_building = buildings[0]
    gorilla = pygame.Rect(gorilla_building.centerx - 10, gorilla_building.top - 30, 20, 30)

    rockets = place_rockets(buildings, 4)
    banana = None
    banana_vel = [0, 0]
    gravity = 0.5
    wind = random.uniform(-1.5, 1.5)
    banana_fired = False
    trajectory_tip = [gorilla.centerx + 100, gorilla.top - 100]

    craters = []
    flames = []
    flame_frames = []
    rocket_advance = False
    win = False
    lose = False
    running = True

    while running:
        clock.tick(FPS)
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        if not banana_fired:
            if keys[pygame.K_UP]: trajectory_tip[1] -= 3
            if keys[pygame.K_DOWN]: trajectory_tip[1] += 3
            if keys[pygame.K_LEFT]: trajectory_tip[0] -= 3
            if keys[pygame.K_RIGHT]: trajectory_tip[0] += 3

            tip_dx = trajectory_tip[0] - gorilla.centerx
            tip_dy = trajectory_tip[1] - gorilla.top
            speed = max(5, min(25, (tip_dx ** 2 + tip_dy ** 2) ** 0.5 / 10))
            angle = math.atan2(-tip_dy, tip_dx)
            banana_speed = speed
            banana_angle = math.degrees(angle)

            if keys[pygame.K_SPACE]:
                banana = pygame.Rect(gorilla.centerx, gorilla.top, 10, 10)
                banana_vel = [banana_speed * math.cos(angle), -banana_speed * math.sin(angle)]
                banana_fired = True

        if banana_fired and banana:
            banana.x += int(banana_vel[0])
            banana.y += int(banana_vel[1])
            banana_vel[1] += gravity
            banana_vel[0] += wind / 60.0

            for rocket in rockets[:]:
                if banana and banana.colliderect(rocket.inflate(40, 40)):
                    flames.append(pygame.Rect(rocket.centerx - 15, rocket.top - 15, 40, 40))
                    flame_frames.append(0)
                    rockets.remove(rocket)
                    banana = None
                    banana_fired = False
                    rocket_advance = True
                    break

            for b in buildings:
                if banana and b.collidepoint(banana.center):
                    craters.append(pygame.Rect(banana.centerx - 10, b.top - 10, 20, 10))
                    flames.append(pygame.Rect(banana.centerx - 20, b.top - 20, 40, 40))
                    flame_frames.append(0)
                    for rocket in rockets[:]:
                        if b.collidepoint(rocket.center) or abs(rocket.centerx - banana.centerx) < 30:
                            rockets.remove(rocket)
                    banana = None
                    banana_fired = False
                    rocket_advance = True
                    break

            if banana and (banana.y > HEIGHT or banana.x > WIDTH):
                banana = None
                banana_fired = False
                rocket_advance = True

        if rocket_advance and rockets:
            for rocket in rockets:
                rocket.move_ip(-1, 0)
                if rocket.colliderect(gorilla):
                    lose = True
                    running = False
            rocket_advance = False

        if not rockets:
            win = True
            running = False

        for b in buildings:
            pygame.draw.rect(screen, GRAY, b)
        for crater in craters:
            pygame.draw.ellipse(screen, BLACK, crater)
        for i, flame in enumerate(flames):
            radius = (flame.width // 2) + (flame_frames[i] % 4) - 2
            pygame.draw.circle(screen, ORANGE, flame.center, radius)
        flame_frames = [f + 1 for f in flame_frames]
        expired = [i for i, f in enumerate(flame_frames) if f > 30]
        for i in reversed(expired):
            del flames[i]
            del flame_frames[i]

        pygame.draw.rect(screen, BLUE, gorilla)
        for rocket in rockets:
            pygame.draw.rect(screen, RED, rocket)
        if banana:
            pygame.draw.circle(screen, YELLOW, banana.center, 5)
        if not banana_fired:
            pygame.draw.line(screen, YELLOW, (gorilla.centerx, gorilla.top), trajectory_tip, 2)

        draw_text(f"Angle: {int(banana_angle)}", 10, 10)
        draw_text(f"Speed: {int(banana_speed)}", 10, 40)
        draw_text(f"Wind: {wind:+.1f}", WIDTH - 160, 10)
        pygame.display.flip()

    screen.fill(BLACK)
    if win:
        draw_text("🎉 YOU WIN! 🎉", WIDTH//2 - 80, HEIGHT//2)
    else:
        draw_text("💥 YOU LOSE! 💥", WIDTH//2 - 80, HEIGHT//2)
    pygame.display.flip()
    pygame.time.wait(2000)
    pygame.quit()
    print("BONUS RESULT: 10")
    return 10

if __name__ == "__main__":
    run_gorilla_game()