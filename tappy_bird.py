import pygame
import random
import sys
import os
import math

# Khởi tạo Pygame
pygame.init()

# Kích thước màn hình
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tappy Bird")
clock = pygame.time.Clock()

# Màu sắc
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
GREEN      = (34,  139, 34 )
GREEN_DARK = (0,   100, 0  )
SKY_TOP    = (100, 180, 255)
SKY_BOT    = (180, 225, 255)
YELLOW     = (255, 220, 0  )
YELLOW_D   = (200, 160, 0  )
RED        = (220, 50,  50 )
ORANGE     = (255, 140, 0  )
BROWN      = (101, 67,  33 )
BROWN_D    = (70,  40,  10 )
GRAY       = (180, 180, 180)
CLOUD      = (240, 248, 255)

# Ground height
GROUND_H = 50
PLAY_H   = SCREEN_HEIGHT - GROUND_H   # khu vực chơi

# Font (dùng font hệ thống hỗ trợ tiếng Việt nếu có)
def load_font(size):
    for name in ["Arial", "DejaVuSans", "FreeSans", None]:
        try:
            return pygame.font.SysFont(name, size) if name else pygame.font.Font(None, size)
        except:
            continue
    return pygame.font.Font(None, size)

font_small  = load_font(28)
font_medium = load_font(42)
font_large  = load_font(64)

HIGH_SCORE_FILE = "highscore.txt"


# ──────────────────────────────────────────
# Vẽ gradient nền
# ──────────────────────────────────────────
def draw_gradient(surface, color_top, color_bot, rect):
    x, y, w, h = rect
    for i in range(h):
        t = i / max(h - 1, 1)
        r = int(color_top[0] + t * (color_bot[0] - color_top[0]))
        g = int(color_top[1] + t * (color_bot[1] - color_top[1]))
        b = int(color_top[2] + t * (color_bot[2] - color_top[2]))
        pygame.draw.line(surface, (r, g, b), (x, y + i), (x + w, y + i))


# ──────────────────────────────────────────
class Bird:
    """Chú chim với animation vỗ cánh"""

    def __init__(self):
        self.x        = 100
        self.y        = PLAY_H // 2
        self.velocity = 0
        self.gravity  = 0.45
        self.jump_str = -9
        self.radius   = 16
        self.alive    = True
        self.angle    = 0           # góc nghiêng thân
        self.wing_t   = 0           # timer cánh
        self.dead_t   = 0           # timer chết (để hiệu ứng rơi)

    def jump(self):
        if self.alive:
            self.velocity = self.jump_str
            self.wing_t = 0         # reset cánh vỗ ngay khi nhảy

    def update(self):
        if not self.alive:
            # Rơi sau khi chết
            self.velocity += self.gravity * 1.5
            self.y += self.velocity
            self.angle = min(self.angle + 5, 90)
            self.dead_t += 1
            return

        self.velocity += self.gravity
        self.velocity  = min(self.velocity, 12)   # giới hạn tốc độ rơi
        self.y        += self.velocity
        self.wing_t   += 1

        # Góc nghiêng: bay lên → ngẩng đầu, rơi → cúi đầu
        target_angle = max(-25, min(45, self.velocity * 4))
        self.angle  += (target_angle - self.angle) * 0.2

        # Chạm trần → nảy nhẹ, không chết
        if self.y - self.radius < 0:
            self.y        = self.radius
            self.velocity = 2

        # Chạm đất → chết
        if self.y + self.radius >= PLAY_H:
            self.y      = PLAY_H - self.radius
            self.velocity = 0
            self.alive  = False

    def draw(self):
        cx, cy = int(self.x), int(self.y)
        r      = self.radius
        angle_rad = math.radians(self.angle)

        # Cánh (vỗ lên/xuống khi sống, xệ xuống khi chết)
        if self.alive:
            wing_phase = math.sin(self.wing_t * 0.4) * 8
        else:
            wing_phase = 8   # cánh xệ

        wing_pts = [
            (cx - 6, cy),
            (cx - 18, cy - 14 + wing_phase),
            (cx - 26, cy - 6 + wing_phase),
            (cx - 10, cy + 4),
        ]
        pygame.draw.polygon(screen, YELLOW_D, wing_pts)

        # Thân chim (hình tròn, nghiêng theo angle)
        pygame.draw.circle(screen, YELLOW,   (cx, cy), r)
        pygame.draw.circle(screen, YELLOW_D, (cx, cy), r, 2)

        # Bụng sáng hơn
        pygame.draw.ellipse(screen, (255, 240, 100),
                            (cx - 6, cy + 2, 14, 10))

        # Mắt
        ex = int(cx + 7 * math.cos(angle_rad - 0.3))
        ey = int(cy - 7 * math.sin(angle_rad - 0.3) - 4)
        pygame.draw.circle(screen, WHITE, (ex, ey), 5)
        pygame.draw.circle(screen, BLACK, (ex + 1, ey + 1), 3)
        pygame.draw.circle(screen, WHITE, (ex + 2, ey - 1), 1)  # ánh mắt

        # Mỏ
        bx = int(cx + (r + 5) * math.cos(angle_rad))
        by = int(cy - (r + 5) * math.sin(angle_rad))
        beak = [
            (bx,       by - 3),
            (bx + 10,  by),
            (bx,       by + 3),
        ]
        pygame.draw.polygon(screen, ORANGE, beak)
        pygame.draw.polygon(screen, RED,    beak, 1)

    def get_rect(self):
        # Hitbox nhỏ hơn sprite để chơi fair hơn
        margin = 4
        return pygame.Rect(
            self.x - self.radius + margin,
            self.y - self.radius + margin,
            (self.radius - margin) * 2,
            (self.radius - margin) * 2,
        )


# ──────────────────────────────────────────
class Pipe:
    """Cặp ống trên – dưới"""

    BASE_SPEED = 3.5

    def __init__(self, x, speed_bonus=0):
        self.x       = x
        self.width   = 65
        self.gap     = 155
        self.speed   = self.BASE_SPEED + speed_bonus
        self.passed  = False

        min_h = 70
        max_h = PLAY_H - self.gap - 70
        self.top_h   = random.randint(min_h, max_h)
        self.bot_y   = self.top_h + self.gap

        # Màu ống ngẫu nhiên nhẹ để tránh nhàm
        g = random.randint(120, 180)
        self.color      = (30, g, 30)
        self.color_dark = (0,  g - 60, 0)

    def update(self):
        self.x -= self.speed

    def draw(self):
        w = self.width

        # ── Ống trên ──
        # thân
        pygame.draw.rect(screen, self.color,
                         (self.x, 0, w, self.top_h))
        # viền trái/phải
        pygame.draw.rect(screen, self.color_dark,
                         (self.x, 0, w, self.top_h), 2)
        # mũ ống (rộng hơn thân 6px mỗi bên)
        cap_h = 18
        pygame.draw.rect(screen, self.color,
                         (self.x - 5, self.top_h - cap_h, w + 10, cap_h))
        pygame.draw.rect(screen, self.color_dark,
                         (self.x - 5, self.top_h - cap_h, w + 10, cap_h), 2)
        # sáng bóng
        pygame.draw.rect(screen, (100, 220, 100),
                         (self.x + 6, 0, 8, self.top_h - cap_h))

        # ── Ống dưới ──
        bot_h = PLAY_H - self.bot_y
        pygame.draw.rect(screen, self.color,
                         (self.x, self.bot_y, w, bot_h))
        pygame.draw.rect(screen, self.color_dark,
                         (self.x, self.bot_y, w, bot_h), 2)
        cap_y = self.bot_y
        pygame.draw.rect(screen, self.color,
                         (self.x - 5, cap_y, w + 10, cap_h))
        pygame.draw.rect(screen, self.color_dark,
                         (self.x - 5, cap_y, w + 10, cap_h), 2)
        pygame.draw.rect(screen, (100, 220, 100),
                         (self.x + 6, cap_y + cap_h, 8, bot_h - cap_h))

    def get_rects(self):
        return (
            pygame.Rect(self.x, 0, self.width, self.top_h),
            pygame.Rect(self.x, self.bot_y, self.width, PLAY_H - self.bot_y),
        )

    def is_offscreen(self):
        return self.x + self.width + 10 < 0


# ──────────────────────────────────────────
class Cloud:
    """Mây nền trang trí"""

    def __init__(self, x=None, speed=None):
        self.x     = x if x is not None else SCREEN_WIDTH + random.randint(0, 200)
        self.y     = random.randint(20, int(PLAY_H * 0.4))
        self.scale = random.uniform(0.6, 1.2)
        self.speed = speed if speed is not None else random.uniform(0.4, 0.9)
        self.alpha = random.randint(160, 230)

    def update(self):
        self.x -= self.speed
        if self.x + 120 * self.scale < 0:
            self.x     = SCREEN_WIDTH + random.randint(20, 100)
            self.y     = random.randint(20, int(PLAY_H * 0.4))
            self.scale = random.uniform(0.6, 1.2)

    def draw(self, surf):
        s = self.scale
        cx, cy = int(self.x), int(self.y)
        cloud_surf = pygame.Surface((int(120 * s) + 4, int(60 * s) + 4),
                                    pygame.SRCALPHA)
        parts = [
            (int(40 * s), int(30 * s), int(28 * s)),
            (int(65 * s), int(20 * s), int(24 * s)),
            (int(90 * s), int(28 * s), int(22 * s)),
            (int(55 * s), int(38 * s), int(20 * s)),
        ]
        for px, py, pr in parts:
            pygame.draw.circle(cloud_surf, (*CLOUD, self.alpha), (px, py), pr)
        surf.blit(cloud_surf, (cx, cy))


# ──────────────────────────────────────────
class Particle:
    """Hạt hiệu ứng khi chết"""

    def __init__(self, x, y):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vx    = math.cos(angle) * speed
        self.vy    = math.sin(angle) * speed - 3
        self.x     = x
        self.y     = y
        self.life  = random.randint(30, 60)
        self.color = random.choice([YELLOW, ORANGE, RED, WHITE])
        self.r     = random.randint(3, 7)

    def update(self):
        self.vy  += 0.3
        self.x   += self.vx
        self.y   += self.vy
        self.life -= 1
        self.r    = max(0, self.r - 0.08)

    def draw(self):
        if self.life > 0 and self.r > 0:
            alpha = min(255, int(255 * self.life / 60))
            s = pygame.Surface((int(self.r * 2) + 2, int(self.r * 2) + 2),
                               pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha),
                               (int(self.r) + 1, int(self.r) + 1), int(self.r))
            screen.blit(s, (int(self.x - self.r), int(self.y - self.r)))


# ──────────────────────────────────────────
class Game:
    """Quản lý toàn bộ trò chơi"""

    PIPE_INTERVAL_START = 88   # frame
    PIPE_INTERVAL_MIN   = 60

    def __init__(self):
        self.high_score = self.load_high_score()
        self.clouds = [Cloud(x=random.randint(0, SCREEN_WIDTH))
                       for _ in range(5)]
        self.reset_game()

    # ── Persistence ────────────────────────
    def load_high_score(self):
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE) as f:
                    return max(0, int(f.read().strip()))
            except:
                pass
        return 0

    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, "w") as f:
                f.write(str(self.high_score))
        except:
            pass

    # ── Reset ──────────────────────────────
    def reset_game(self):
        self.bird         = Bird()
        self.pipes        = []
        self.particles    = []
        self.score        = 0
        self.game_over    = False
        self.game_started = False
        self.pipe_timer   = 0
        self.death_done   = False   # chờ chim rơi xuống đất rồi mới show overlay

    # ── Speed helpers ───────────────────────
    def speed_bonus(self):
        """Tốc độ tăng dần theo điểm"""
        return min(self.score // 5 * 0.3, 2.5)

    def pipe_interval(self):
        return max(self.PIPE_INTERVAL_MIN,
                   self.PIPE_INTERVAL_START - self.score // 3)

    # ── Events ─────────────────────────────
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            pressed = (event.type == pygame.KEYDOWN and
                       event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w)) or \
                      event.type == pygame.MOUSEBUTTONDOWN

            if pressed:
                if not self.game_started:
                    self.game_started = True
                elif not self.game_over:
                    self.bird.jump()
                elif self.death_done:
                    self.reset_game()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

        return True

    # ── Update ─────────────────────────────
    def update(self):
        # Luôn cập nhật mây
        for c in self.clouds:
            c.update()

        if not self.game_started:
            return

        # Cập nhật particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        # Nếu game over: chờ chim rơi xuống đất
        if self.game_over:
            self.bird.update()
            if self.bird.y + self.bird.radius >= PLAY_H or self.bird.dead_t > 90:
                self.death_done = True
            return

        # ── Logic chính ──
        self.bird.update()

        if not self.bird.alive:
            self._trigger_death()
            return

        # Spawn ống
        self.pipe_timer += 1
        if self.pipe_timer >= self.pipe_interval():
            self.pipes.append(Pipe(SCREEN_WIDTH + 10, self.speed_bonus()))
            self.pipe_timer = 0

        # Cập nhật ống
        for pipe in self.pipes[:]:
            pipe.update()

            bird_rect = self.bird.get_rect()
            tr, br     = pipe.get_rects()
            if bird_rect.colliderect(tr) or bird_rect.colliderect(br):
                self._trigger_death()
                return

            if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                pipe.passed  = True
                self.score  += 1

            if pipe.is_offscreen():
                self.pipes.remove(pipe)

    def _trigger_death(self):
        self.bird.alive   = False
        self.game_over    = True
        self.death_done   = False
        # Sinh particles tại vị trí chim
        for _ in range(25):
            self.particles.append(Particle(self.bird.x, self.bird.y))
        # Cập nhật điểm cao
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

    # ── Draw helpers ───────────────────────
    def draw_background(self):
        draw_gradient(screen, SKY_TOP, SKY_BOT, (0, 0, SCREEN_WIDTH, PLAY_H))

        # Mây
        for c in self.clouds:
            c.draw(screen)

        # Mặt đất
        pygame.draw.rect(screen, BROWN,
                         (0, PLAY_H, SCREEN_WIDTH, GROUND_H))
        # Cỏ
        pygame.draw.rect(screen, GREEN,
                         (0, PLAY_H, SCREEN_WIDTH, 8))
        pygame.draw.rect(screen, BROWN_D,
                         (0, PLAY_H + 8, SCREEN_WIDTH, 2))

    def draw_score(self):
        # Bóng chữ
        def shadow_text(font, text, color, x, y):
            s = font.render(text, True, (0, 0, 0, 160))
            screen.blit(s, (x + 2, y + 2))
            s = font.render(text, True, color)
            screen.blit(s, (x, y))

        shadow_text(font_small, f"Score: {self.score}", WHITE, 12, 12)
        shadow_text(font_small, f"Best:  {self.high_score}", YELLOW, 12, 46)

        if self.score > 0 and self.score % 5 == 0:
            pass   # có thể thêm milestone text

    def draw_start_screen(self):
        # Panel mờ
        panel = pygame.Surface((320, 240), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 100))
        screen.blit(panel, (40, 120))

        # Tiêu đề (nẩy nhẹ)
        bob = int(math.sin(pygame.time.get_ticks() / 400) * 5)
        title = font_large.render("TAPPY BIRD", True, YELLOW)
        tr    = title.get_rect(center=(SCREEN_WIDTH // 2, 170 + bob))
        # bóng
        ts = font_large.render("TAPPY BIRD", True, ORANGE)
        screen.blit(ts, (tr.x + 3, tr.y + 3))
        screen.blit(title, tr)

        # Gợi ý
        t1 = font_small.render("Nhan SPACE / Click de bat dau", True, WHITE)
        screen.blit(t1, t1.get_rect(center=(SCREEN_WIDTH // 2, 240)))
        t2 = font_small.render("ESC de thoat", True, GRAY)
        screen.blit(t2, t2.get_rect(center=(SCREEN_WIDTH // 2, 278)))

        # Điểm cao
        if self.high_score > 0:
            ht = font_small.render(f"Ky luc: {self.high_score}", True, YELLOW)
            screen.blit(ht, ht.get_rect(center=(SCREEN_WIDTH // 2, 316)))

    def draw_game_over(self):
        if not self.death_done:
            return   # chờ animation rơi

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Panel
        panel_w, panel_h = 320, 240
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 30, 220))
        px, py = (SCREEN_WIDTH - panel_w) // 2, 150
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, YELLOW, (px, py, panel_w, panel_h), 2)

        cx = SCREEN_WIDTH // 2

        go = font_large.render("GAME OVER", True, RED)
        screen.blit(go, go.get_rect(center=(cx, 195)))

        sc = font_medium.render(f"Score: {self.score}", True, WHITE)
        screen.blit(sc, sc.get_rect(center=(cx, 255)))

        new_rec = self.score > 0 and self.score == self.high_score
        if new_rec:
            nr = font_small.render("★ Ky luc moi! ★", True, YELLOW)
            screen.blit(nr, nr.get_rect(center=(cx, 295)))
        else:
            hs = font_small.render(f"Best: {self.high_score}", True, YELLOW)
            screen.blit(hs, hs.get_rect(center=(cx, 295)))

        # Nhấp nháy hướng dẫn
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            rt = font_small.render("Nhan SPACE / Click de choi lai", True, WHITE)
            screen.blit(rt, rt.get_rect(center=(cx, 335)))

        et = font_small.render("ESC de thoat", True, GRAY)
        screen.blit(et, et.get_rect(center=(cx, 365)))

    def draw_speed_indicator(self):
        """Hiển thị tốc độ / cấp độ hiện tại"""
        level = int(self.speed_bonus() / 0.3) + 1
        if level > 1:
            lv = font_small.render(f"Lv.{level}", True, ORANGE)
            screen.blit(lv, lv.get_rect(topright=(SCREEN_WIDTH - 10, 12)))

    # ── Main draw ──────────────────────────
    def draw(self):
        self.draw_background()

        for pipe in self.pipes:
            pipe.draw()

        self.bird.draw()

        for p in self.particles:
            p.draw()

        self.draw_score()
        self.draw_speed_indicator()

        if not self.game_started:
            self.draw_start_screen()

        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    # ── Main loop ──────────────────────────
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            clock.tick(60)

        pygame.quit()
        sys.exit()


# ── Entry point ────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
