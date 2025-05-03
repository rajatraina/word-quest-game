
import pygame
import random
import time
import math

pygame.init()

WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brick Break Bonus")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PADDLE_COLOR = (200, 200, 200)
BALL_COLOR = (255, 255, 0)
BRICK_COLOR_1 = (0, 150, 255)
BRICK_COLOR_2 = (255, 100, 100)
POWERUP_COLOR = (160, 32, 240)

FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 80, 10
BALL_RADIUS = 8
BRICK_ROWS, BRICK_COLS = 5, 8
BRICK_WIDTH = WIDTH // BRICK_COLS
BRICK_HEIGHT = 20
LIVES = 3
PADDLE_SPEED = 6

font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 48)

def draw_text(text, x, y, font=font, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def generate_bricks():
    bricks = []
    for r in range(BRICK_ROWS):
        for c in range(BRICK_COLS):
            if random.random() > 0.3:
                x = c * BRICK_WIDTH
                y = r * BRICK_HEIGHT + 40
                roll = random.random()
                if roll < 0.2:
                    value = 2
                    color = BRICK_COLOR_2
                elif roll < 0.25:
                    value = 0
                    color = POWERUP_COLOR
                else:
                    value = 1
                    color = BRICK_COLOR_1
                bricks.append({
                    'rect': pygame.Rect(x, y, BRICK_WIDTH - 2, BRICK_HEIGHT - 2),
                    'value': value,
                    'color': color
                })
    return bricks

def bounce_angle(paddle, ball):
    relative_x = ball.centerx - paddle.centerx
    norm = max(-1, min(1, relative_x / (paddle.width / 2)))
    max_angle = math.radians(60)
    angle = norm * max_angle
    speed = 6
    dx = speed * math.sin(angle)
    dy = -abs(speed * math.cos(angle))
    return dx, dy

def run_bricks_game():
    paddle = pygame.Rect(WIDTH//2 - PADDLE_WIDTH//2, HEIGHT - 30, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball = pygame.Rect(WIDTH//2, HEIGHT//2, BALL_RADIUS, BALL_RADIUS)
    ball_dx, ball_dy = 4 * random.choice([-1, 1]), -4

    bricks = generate_bricks()
    clock = pygame.time.Clock()
    bonus_points = 0
    lives = LIVES
    move_left = False
    move_right = False
    power_up_active = False
    power_up_end_time = 0
    win = False

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    move_left = True
                elif event.key == pygame.K_RIGHT:
                    move_right = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    move_left = False
                elif event.key == pygame.K_RIGHT:
                    move_right = False

        if move_left and paddle.left > 0:
            paddle.move_ip(-PADDLE_SPEED, 0)
        if move_right and paddle.right < WIDTH:
            paddle.move_ip(PADDLE_SPEED, 0)

        if power_up_active and time.time() > power_up_end_time:
            power_up_active = False
            paddle.width = PADDLE_WIDTH

        ball.move_ip(ball_dx, ball_dy)

        if ball.left <= 0 or ball.right >= WIDTH:
            ball_dx *= -1
        if ball.top <= 0:
            ball_dy *= -1
        if ball.colliderect(paddle):
            ball_dx, ball_dy = bounce_angle(paddle, ball)

        for brick in bricks[:]:
            if ball.colliderect(brick['rect']):
                bricks.remove(brick)
                ball_dy *= -1
                if brick['value'] == 0:
                    power_up_active = True
                    power_up_end_time = time.time() + 5
                    paddle.width = int(PADDLE_WIDTH * 1.8)
                else:
                    bonus_points += brick['value']
                break

        if ball.bottom >= HEIGHT:
            lives -= 1
            ball = pygame.Rect(WIDTH//2, HEIGHT//2, BALL_RADIUS, BALL_RADIUS)
            ball_dx, ball_dy = 4 * random.choice([-1, 1]), -4
            time.sleep(0.5)

        if lives <= 0 or len(bricks) == 0:
            running = False
            win = len(bricks) == 0

        pygame.draw.rect(screen, PADDLE_COLOR, paddle)
        pygame.draw.ellipse(screen, BALL_COLOR, ball)
        for brick in bricks:
            pygame.draw.rect(screen, brick['color'], brick['rect'])

        draw_text(f"Score: {bonus_points}  Lives: {lives}", 10, 10)
        if power_up_active:
            draw_text("🔮 Power-up: Wide Paddle!", WIDTH - 220, 10, POWERUP_COLOR)

        pygame.display.flip()

    screen.fill(BLACK)
    if win:
        draw_text("🎉 YOU WIN! 🎉", WIDTH//2 - 120, HEIGHT//2 - 20, big_font, WHITE)
    else:
        draw_text("💥 GAME OVER 💥", WIDTH//2 - 120, HEIGHT//2 - 20, big_font, WHITE)
    pygame.display.flip()
    time.sleep(2)
    pygame.quit()
    print(f"BONUS RESULT: {bonus_points}")
    return bonus_points

if __name__ == "__main__":
    run_bricks_game()
