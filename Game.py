import pygame
import sys
import random
import os

# --- Helper Functions ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def draw_text_centered(surface, text, font, color, y):
    """Draw text centered horizontally at given y position"""
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=(WIDTH // 2, y))
    surface.blit(rendered, rect)

def draw_hud_box(surface, text, font, text_color, bg_color, x, y, padding=10):
    """Draws a text HUD box with background and padding"""
    rendered = font.render(text, True, text_color)
    rect = rendered.get_rect(topleft=(x, y))
    box_rect = pygame.Rect(rect.x - padding, rect.y - padding,
                           rect.width + 2*padding, rect.height + 2*padding)
    # Semi-transparent background
    s = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
    s.fill(bg_color)
    surface.blit(s, (box_rect.x, box_rect.y))
    pygame.draw.rect(surface, WHITE, box_rect, 2, border_radius=8)
    surface.blit(rendered, rect)

# --- Initialize Pygame ---
pygame.init()
pygame.mixer.init()

# --- Screen ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Catcher")

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)
HUD_BG = (0,0,0,180)  # Semi-transparent

# --- Load Images ---
basket_img = pygame.image.load(resource_path("images/basket.png"))
basket_img = pygame.transform.scale(basket_img, (100, 60))
fruit_img = pygame.image.load(resource_path("images/fruit.png"))
fruit_img = pygame.transform.scale(fruit_img, (40, 40))
powerup_img = pygame.image.load(resource_path("images/powerup.png"))
powerup_img = pygame.transform.scale(powerup_img, (30, 30))
background_img = pygame.image.load(resource_path("images/background.png"))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
crown_img = pygame.image.load(resource_path("images/crown.png"))
crown_img = pygame.transform.scale(crown_img, (32, 32))
pygame.display.set_icon(pygame.image.load(resource_path("images/logo.png")))

# --- Sounds ---
catch_sound = pygame.mixer.Sound(resource_path("sound/catch.mp3"))
miss_sound = pygame.mixer.Sound(resource_path("sound/miss.mp3"))
gameover_sound = pygame.mixer.Sound(resource_path("sound/gameover.mp3"))
pygame.mixer.music.load(resource_path("sound/background.mp3"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# --- Fonts ---
font = pygame.font.SysFont(None, 40)

# --- Player ---
player = basket_img.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20))

# --- Game Variables ---
score = 0
lives = 3
game_over = False
gameover_played = False
frame_count = 0
level = None
paused = False
start_screen = True
current_stage = 0
show_level_up = False
level_up_timer = 0

# --- Additional Stats ---
total_fruits_caught = 0
current_combo = 0
max_combo = 0

# --- Sound/Music toggles ---
sound_on = True
music_on = True

# --- High Score ---
high_score = 0
if os.path.exists("highscore.txt"):
    with open("highscore.txt", "r") as f:
        try:
            high_score = int(f.read().strip())
        except:
            high_score = 0

# --- Falling Objects ---
falling_objects = []
powerups = []

# --- Level Settings ---
level_stages = {
    "easy": [(0, {"spawn_time":50,"speed_range":(3,5)}),
             (10, {"spawn_time":40,"speed_range":(4,6)}),
             (20, {"spawn_time":30,"speed_range":(5,7)})],
    "medium": [(0, {"spawn_time":30,"speed_range":(4,8)}),
               (20, {"spawn_time":25,"speed_range":(5,9)}),
               (40, {"spawn_time":20,"speed_range":(6,10)}),
               (60, {"spawn_time":15,"speed_range":(7,11)})],
    "hard": [(0, {"spawn_time":15,"speed_range":(6,12)}),
             (20, {"spawn_time":12,"speed_range":(7,13)}),
             (40, {"spawn_time":10,"speed_range":(8,14)}),
             (60, {"spawn_time":8,"speed_range":(9,15)}),
             (80, {"spawn_time":6,"speed_range":(10,16)})]
}
spawn_time, speed_range = 30, (4,8)
powerup_chance = 0.01

# --- Reset Game ---
def reset_game():
    global score, lives, falling_objects, powerups, game_over, gameover_played, frame_count
    global paused, current_stage, show_level_up, level_up_timer
    global total_fruits_caught, current_combo, max_combo
    score = 0
    lives = 3
    falling_objects = []
    powerups = []
    game_over = False
    gameover_played = False
    frame_count = 0
    paused = False
    current_stage = 0
    show_level_up = False
    level_up_timer = 0
    total_fruits_caught = 0
    current_combo = 0
    max_combo = 0

# --- Clock ---
clock = pygame.time.Clock()

# --- Start Menu Animation ---
clouds = [{"x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT//2)} for _ in range(5)]

# --- Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Start Screen Input
        if start_screen and event.type == pygame.KEYDOWN:
            start_screen = False

        # Level Select
        if not start_screen and level is None and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: level = "easy"
            elif event.key == pygame.K_2: level = "medium"
            elif event.key == pygame.K_3: level = "hard"
            if level:
                spawn_time = level_stages[level][0][1]["spawn_time"]
                speed_range = level_stages[level][0][1]["speed_range"]
                reset_game()

        # Pause / Resume
        if level and not game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            paused = not paused

        # Pause Menu Options
        if paused and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                sound_on = not sound_on
            if event.key == pygame.K_m:
                music_on = not music_on
                if music_on:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.pause()
            if event.key == pygame.K_b:
                level = None
                reset_game()

        # Game Over Controls
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                reset_game()
            elif event.key == pygame.K_b:
                level = None
                reset_game()

    # --- Game Logic ---
    if level and not game_over and not paused:
        # Update Stage
        for i, (threshold, settings) in enumerate(level_stages[level]):
            if score >= threshold and i > current_stage:
                current_stage = i
                spawn_time = settings["spawn_time"]
                speed_range = settings["speed_range"]
                show_level_up = True
                level_up_timer = 90  # 1.5 sec at 60fps

        # Player Movement
        mouse_x, _ = pygame.mouse.get_pos()
        player.centerx = mouse_x
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: player.x -= 7
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: player.x += 7
        if player.left < 0: player.left = 0
        if player.right > WIDTH: player.right = WIDTH

        # Spawn Fruits
        frame_count += 1
        if frame_count % spawn_time == 0:
            x_pos = random.randint(0, WIDTH - fruit_img.get_width())
            falling_objects.append({"rect": fruit_img.get_rect(topleft=(x_pos, 0)),
                                    "speed": random.randint(*speed_range)})

        # Spawn Powerups
        if random.random() < powerup_chance:
            x_pos = random.randint(0, WIDTH - powerup_img.get_width())
            powerups.append({"rect": powerup_img.get_rect(topleft=(x_pos, 0)),
                             "speed": random.randint(3,6)})

        # Fruits Collision
        for obj in falling_objects[:]:
            obj["rect"].y += obj["speed"]
            if obj["rect"].colliderect(player):
                falling_objects.remove(obj)
                score += 1
                total_fruits_caught += 1
                current_combo += 1
                if current_combo > max_combo:
                    max_combo = current_combo
                if sound_on: catch_sound.play()
            elif obj["rect"].top > HEIGHT:
                falling_objects.remove(obj)
                lives -= 1
                current_combo = 0
                if sound_on: miss_sound.play()
                if lives <= 0:
                    game_over = True
                    if score > high_score:
                        high_score = score
                        with open("highscore.txt", "w") as f:
                            f.write(str(high_score))

        # Powerups Collision
        for p in powerups[:]:
            p["rect"].y += p["speed"]
            if p["rect"].colliderect(player):
                powerups.remove(p)
                score += 5
                total_fruits_caught += 1
                current_combo += 1
                if current_combo > max_combo:
                    max_combo = current_combo
                if sound_on: catch_sound.play()
            elif p["rect"].top > HEIGHT:
                powerups.remove(p)

    # --- Drawing ---
    screen.blit(background_img, (0,0))

    # Start Screen
    if start_screen:
        title_font = pygame.font.SysFont(None, 80)
        subtitle_font = pygame.font.SysFont(None, 40)
        draw_text_centered(screen, "FRUIT CATCHER", title_font, WHITE, HEIGHT//2 - 100)

        # Blinking text
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            draw_text_centered(screen, "Press Any Key to Start", subtitle_font, WHITE, HEIGHT//2 - 30)

        # High Score
        hs_text = subtitle_font.render(f"High Score: {high_score}", True, GOLD)
        hs_rect = hs_text.get_rect(center=(WIDTH//2 + 20, HEIGHT//2 + 30))
        screen.blit(hs_text, hs_rect)
        crown_rect = crown_img.get_rect(midright=(hs_rect.left - 10, hs_rect.centery))
        screen.blit(crown_img, crown_rect)

        draw_text_centered(screen, "Made with Pygame", subtitle_font, WHITE, HEIGHT//2 + 80)

        # Clouds Animation
        for cloud in clouds:
            pygame.draw.ellipse(screen, WHITE, (cloud["x"], cloud["y"], 80, 40))
            cloud["x"] -= 1
            if cloud["x"] < -80:
                cloud["x"] = WIDTH
                cloud["y"] = random.randint(0, HEIGHT//2)

    # Level Select
    elif level is None:
        draw_text_centered(screen, "Select Level:", font, WHITE, HEIGHT//2 - 120)
        draw_text_centered(screen, "Press 1 for Easy", font, WHITE, HEIGHT//2 - 70)
        draw_text_centered(screen, "Press 2 for Medium", font, WHITE, HEIGHT//2 - 30)
        draw_text_centered(screen, "Press 3 for Hard", font, WHITE, HEIGHT//2 + 10)
        instructions = [
            "Instructions:",
            "- Move basket with Mouse or Arrow Keys",
            "- Catch fruits to gain points",
            "- Catch power-ups for bonus points (+5)",
            "- Missing fruits loses a life",
            "- Game ends when lives reach 0",
            "- Press P to Pause during game",
            "- Press B to go Back to Level Select"
        ]
        for i, line in enumerate(instructions):
            draw_text_centered(screen, line, font, WHITE, HEIGHT//2 + 60 + i*30)

    # Pause Menu
    elif paused:
        draw_text_centered(screen, "PAUSED", font, WHITE, HEIGHT//2 - 120)
        draw_text_centered(screen, "Press P to Continue", font, WHITE, HEIGHT//2 - 80)
        draw_text_centered(screen, "Press B to go Back to Level Select", font, WHITE, HEIGHT//2 - 40)
        draw_text_centered(screen, f"Sound: {'ON' if sound_on else 'OFF'} (Press S)", font, WHITE, HEIGHT//2)
        draw_text_centered(screen, f"Music: {'ON' if music_on else 'OFF'} (Press M)", font, WHITE, HEIGHT//2 + 40)

    # In-Game
    elif not game_over:
        screen.blit(basket_img, player)
        for obj in falling_objects: screen.blit(fruit_img, obj["rect"])
        for p in powerups: screen.blit(powerup_img, p["rect"])
        draw_hud_box(screen, f"Score: {score}", font, WHITE, HUD_BG, 10, 10)
        draw_hud_box(screen, f"Lives: {lives}", font, WHITE, HUD_BG, WIDTH - 160, 10)
        if show_level_up:
            draw_text_centered(screen, f"Level Up!", font, GOLD, HEIGHT//2 - 200)
            level_up_timer -= 1
            if level_up_timer <= 0:
                show_level_up = False

    # Game Over
    else:
        if not gameover_played:
            if sound_on: gameover_sound.play()
            gameover_played = True
        draw_text_centered(screen, "GAME OVER", font, WHITE, HEIGHT//2 - 140)
        draw_text_centered(screen, f"Final Score: {score}", font, WHITE, HEIGHT//2 - 100)
        draw_text_centered(screen, f"High Score: {high_score}", font, GOLD, HEIGHT//2 - 60)
        draw_text_centered(screen, f"Fruits Caught: {total_fruits_caught}", font, WHITE, HEIGHT//2 - 20)
        draw_text_centered(screen, f"Max Combo: {max_combo}", font, WHITE, HEIGHT//2 + 20)
        draw_text_centered(screen, "Press ENTER to Restart", font, WHITE, HEIGHT//2 + 60)
        draw_text_centered(screen, "Press B to go Back to Level Select", font, WHITE, HEIGHT//2 + 100)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()