import pygame
import sys
import random
import time

pygame.init()
pygame.mixer.init()

# Screen dimensions
WIDTH = 400
HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Game variables
gravity = 0.15
bird_movement = 0
game_active = False
score = 0
high_score = 0
difficulty = None
paused = False

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load and resize images
try:
    background_img = pygame.image.load(r"assets/background.png").convert()
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))

    bird_img = pygame.image.load(r"assets/bird.png").convert_alpha()
    bird_img = pygame.transform.scale(bird_img, (50, 40))  # Increased size

    pipe_img = pygame.image.load(r"assets/pipe.png").convert_alpha()
    pipe_img = pygame.transform.scale(pipe_img, (70, 400))

    powerup_img = pygame.image.load(r"assets/powerup.png").convert_alpha()
    powerup_img = pygame.transform.scale(powerup_img, (30, 30))
except pygame.error as e:
    print(f"Couldn't load image: {e}")
    sys.exit()

# Load sounds
try:
    jump_sound = pygame.mixer.Sound(r"assets/jump1.mp3")
    score_sound = pygame.mixer.Sound(r"assets/score.mp3")
    hit_sound = pygame.mixer.Sound(r"assets/hit1.mp3")
    powerup_sound = pygame.mixer.Sound(r"assets/powerup.mp3")
    pause_sound = pygame.mixer.Sound(r"assets/pause.mp3")
    unpause_sound = pygame.mixer.Sound(r"assets/unpause.mp3")
except pygame.error as e:
    print(f"Couldn't load sound: {e}")
    sys.exit()

# Bird rectangle  
bird_rect = bird_img.get_rect(center=(100, HEIGHT // 2))

# Pipe setup
pipe_list = []
SPAWNPIPE = pygame.USEREVENT

# Power-up setup
powerup = None
SPAWNPOWERUP = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWNPOWERUP, 10000)  # Spawn power-up every 10 seconds

# Particle system
particles = []

# Difficulty settings
difficulty_settings = {
    'easy': {'gravity': 0.15, 'jump': -4, 'pipe_speed': 2, 'pipe_frequency': 2500, 'gap': 250},
    'medium': {'gravity': 0.2, 'jump': -5, 'pipe_speed': 3, 'pipe_frequency': 2000, 'gap': 225},
    'hard': {'gravity': 0.25, 'jump': -6, 'pipe_speed': 4, 'pipe_frequency': 1500, 'gap': 200}
}

font = pygame.font.Font(None, 36)

def create_pipe():
    random_pipe_pos = random.choice([300, 350, 400])
    bottom_pipe = pipe_img.get_rect(midtop=(500, random_pipe_pos))
    top_pipe = pipe_img.get_rect(midbottom=(500, random_pipe_pos - difficulty_settings[difficulty]['gap']))
    return bottom_pipe, top_pipe

def move_pipes(pipes):
    for pipe in pipes:
        pipe.centerx -= difficulty_settings[difficulty]['pipe_speed']
    return [pipe for pipe in pipes if pipe.right > -50]

def draw_pipes(pipes):
    for pipe in pipes:
        if pipe.bottom >= HEIGHT:
            screen.blit(pipe_img, pipe)
        else:
            flip_pipe = pygame.transform.flip(pipe_img, False, True)
            screen.blit(flip_pipe, pipe)

def check_collision(pipes):
    for pipe in pipes:
        if bird_rect.colliderect(pipe):
            hit_sound.play()
            return False
    if bird_rect.top <= -100 or bird_rect.bottom >= HEIGHT:
        hit_sound.play()
        return False
    return True

def rotate_bird(bird):
    new_bird = pygame.transform.rotozoom(bird, -bird_movement * 3, 1)
    return new_bird

def draw_score():
    score_surface = font.render(f'Score: {score}', True, BLACK)
    score_rect = score_surface.get_rect(center=(WIDTH // 2, 50))
    screen.blit(score_surface, score_rect)

def create_powerup():
    return powerup_img.get_rect(center=(WIDTH + 50, random.randint(100, HEIGHT - 100)))

def move_powerup(powerup):
    powerup.centerx -= 3
    return powerup if powerup.right > 0 else None

def draw_powerup(powerup):
    if powerup:
        screen.blit(powerup_img, powerup)

def create_particles(pos):
    return {'pos': list(pos), 'vel': [random.uniform(-1, 1), random.uniform(-2, 0)], 'timer': 30}

def update_particles():
    global particles
    for particle in particles:
        particle['pos'][0] += particle['vel'][0]
        particle['pos'][1] += particle['vel'][1]
        particle['timer'] -= 1
    particles = [particle for particle in particles if particle['timer'] > 0]

def draw_particles():
    for particle in particles:
        pygame.draw.circle(screen, YELLOW, [int(particle['pos'][0]), int(particle['pos'][1])], 3)

def draw_start_screen():
    screen.blit(background_img, (0, 0))
    start_text = font.render("Choose Difficulty", True, BLACK)
    screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 4))
    
    easy_text = font.render("1 - Easy", True, GREEN)
    screen.blit(easy_text, (WIDTH // 2 - easy_text.get_width() // 2, HEIGHT // 2 - 50))
    
    medium_text = font.render("2 - Medium", True, BLUE)
    screen.blit(medium_text, (WIDTH // 2 - medium_text.get_width() // 2, HEIGHT // 2))
    
    hard_text = font.render("3 - Hard", True, RED)
    screen.blit(hard_text, (WIDTH // 2 - hard_text.get_width() // 2, HEIGHT // 2 + 50))
    
    score_text = font.render(f"High Score: {high_score}", True, BLACK)
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT * 3 // 4))

def draw_pause_screen():
    pause_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pause_surface.fill((0, 0, 0, 128))
    screen.blit(pause_surface, (0, 0))
    pause_text = font.render("PAUSED", True, WHITE)
    screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))
    resume_text = font.render("Press P to Resume", True, WHITE)
    screen.blit(resume_text, (WIDTH // 2 - resume_text.get_width() // 2, HEIGHT // 2 + 50))

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if not game_active and not difficulty:
                if event.key == pygame.K_1:
                    difficulty = 'easy'
                elif event.key == pygame.K_2:
                    difficulty = 'medium'
                elif event.key == pygame.K_3:
                    difficulty = 'hard'
                
                if difficulty:
                    pygame.time.set_timer(SPAWNPIPE, difficulty_settings[difficulty]['pipe_frequency'])
                    game_active = True
                    pipe_list.clear()
                    bird_rect.center = (100, HEIGHT // 2)
                    bird_movement = 0
                    score = 0
            elif game_active and not paused:
                if event.key == pygame.K_SPACE:
                    bird_movement = 0
                    bird_movement += difficulty_settings[difficulty]['jump']
                    jump_sound.play()
                    particles.extend([create_particles(bird_rect.center) for _ in range(5)])
                elif event.key == pygame.K_p:
                    paused = True
                    pause_sound.play()
            elif paused:
                if event.key == pygame.K_p:
                    paused = False
                    unpause_sound.play()
        if event.type == SPAWNPIPE and game_active and not paused:
            pipe_list.extend(create_pipe())
            score += 1
            score_sound.play()
        if event.type == SPAWNPOWERUP and game_active and not paused:
            powerup = create_powerup()

    screen.blit(background_img, (0, 0))

    if game_active and not paused:
        # Bird movement
        bird_movement += difficulty_settings[difficulty]['gravity']
        rotated_bird = rotate_bird(bird_img)
        bird_rect.centery += bird_movement
        screen.blit(rotated_bird, bird_rect)

        # Pipes
        pipe_list = move_pipes(pipe_list)
        draw_pipes(pipe_list)

        # Power-up
        if powerup:
            powerup = move_powerup(powerup)
            draw_powerup(powerup)
            if powerup and bird_rect.colliderect(powerup):
                powerup = None
                score += 5
                powerup_sound.play()
                particles.extend([create_particles(bird_rect.center) for _ in range(20)])

        # Particles
        update_particles()
        draw_particles()

        # Collision
        game_active = check_collision(pipe_list)

        # Score
        draw_score()
    elif paused:
        # Draw the game state
        screen.blit(rotate_bird(bird_img), bird_rect)
        draw_pipes(pipe_list)
        draw_powerup(powerup)
        draw_particles()
        draw_score()
        # Draw pause screen
        draw_pause_screen()
    else:
        if score > high_score:
            high_score = score
        difficulty = None
        powerup = None
        particles.clear()
        draw_start_screen()
        # Add a small delay before allowing restart
        pygame.display.flip()
        time.sleep(1)  # 1 second delay

    pygame.display.update()
    clock.tick(60)
