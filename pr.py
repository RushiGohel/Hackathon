#!/usr/bin/env python3
"""
Recycling Sorter (fixed)
- Fixed constructor & main-guard typos from the original snippet
- Made audio initialization resilient (works even without an audio device)
- Small robustness fixes for drawing rotated items

Save as `recycling_sorter_fixed.py` and run with Python 3 (needs pygame).
Install pygame with: pip install pygame
"""

import pygame
import random
import json
import math
import os
from dataclasses import dataclass, field
from typing import Tuple, List, Optional

# --------------------------- Config ---------------------------------
SCREEN_W, SCREEN_H = 1000, 650
FPS = 60

C_WHITE = (245, 245, 245)
C_BLACK = (20, 20, 20)
C_GRAY = (60, 60, 60)
C_DIM = (30, 30, 30)
C_SHADOW = (0, 0, 0, 60)
C_PAPER = (59, 130, 246)     # blue
C_PLASTIC = (239, 68, 68)    # red
C_METAL = (161, 161, 170)    # zinc-ish
C_ORGANIC = (34, 197, 94)    # green
C_EWASTE = (147, 51, 234)    # purple
C_GOLD = (250, 204, 21)

BINS = [
    ("Paper", C_PAPER),
    ("Plastic", C_PLASTIC),
    ("Metal", C_METAL),
    ("Organic", C_ORGANIC),
    ("E-Waste", C_EWASTE),
]

# Example items: name -> (category, short tip)
ITEMS = {
    "Newspaper": ("Paper", "Paper goes in blue bin. Keep it dry."),
    "Cardboard": ("Paper", "Flatten boxes to save space."),
    "Notebook": ("Paper", "Remove plastic spirals when possible."),
    "Magazine": ("Paper", "Glossy paper can be recycled in many cities."),
    "Paper Cup": ("Paper", "If wax-lined, check local rules."),
    "Bottle": ("Plastic", "Empty and crush to save space."),
    "Food Box": ("Plastic", "Rinse to avoid contamination."),
    "Straw": ("Plastic", "Hard to recycle; avoid single-use."),
    "Milk Jug": ("Plastic", "Caps on or off depends on locale."),
    "Toothbrush": ("Plastic", "Consider bamboo alternatives."),
    "Can": ("Metal", "Aluminum recycles endlessly!"),
    "Tin Can": ("Metal", "Rinse before recycling."),
    "Soda Can": ("Metal", "Crush cans to save space."),
    "Foil": ("Metal", "Clean foil can be recycled if balled up."),
    "Steel Lid": ("Metal", "Attach to can if safe."),
    "Banana Peel": ("Organic", "Great for compost."),
    "Apple Core": ("Organic", "Compost to enrich soil."),
    "Tea Bag": ("Organic", "Check if bag has plastic."),
    "Leaves": ("Organic", "Compost yard waste."),
    "Egg Shells": ("Organic", "Add to compost for calcium."),
    "Phone": ("E-Waste", "Take to e-waste drop-off."),
    "Battery": ("E-Waste", "Never bin batteries!"),
    "Charger": ("E-Waste", "E-waste centers recover metals."),
    "Earphones": ("E-Waste", "Recycle wires/e-waste properly."),
    "Keyboard": ("E-Waste", "Contains valuable components."),
}

# Spawn parameters per level
LEVELS = [
    # (fall_speed, spawn_interval_frames, level_duration_seconds, target_score_increment)
    (2.4, 75, 50, 200),
    (3.0, 65, 55, 450),
    (3.6, 58, 60, 800),
    (4.2, 52, 60, 1200),
    (4.8, 46, 65, 1700),
]

LIVES_START = 3
HISCORE_FILE = "recycling_sorter_highscore.json"

# --------------------------- Helpers --------------------------------

def load_hiscore():
    try:
        if os.path.exists(HISCORE_FILE):
            with open(HISCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return int(data.get("hiscore", 0))
    except Exception:
        pass
    return 0


def save_hiscore(score: int):
    try:
        with open(HISCORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"hiscore": score}, f)
    except Exception:
        pass


def lerp(a, b, t):
    return a + (b - a) * t

# --------------------------- Game Objects ---------------------------

@dataclass
class Item:
    name: str
    category: str
    tip: str
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    w: int = 120
    h: int = 40
    dragging: bool = False
    grabbed_dx: float = 0.0
    grabbed_dy: float = 0.0
    rot: float = 0.0
    rot_speed: float = field(default_factory=lambda: random.uniform(-0.25, 0.25))

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, gravity: float):
        if not self.dragging:
            # gravity is a level-scaled parameter; scale it down so movement is playable
            self.vy += gravity * 0.02
            self.x += self.vx
            self.y += self.vy
            self.rot += self.rot_speed

    def draw(self, surf: pygame.Surface, font: pygame.font.Font):
        # Draw a rounded rectangle "tag" with shadow and rotated content
        rect = self.rect()
        shadow = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 60), shadow.get_rect(), border_radius=12)
        surf.blit(shadow, (rect.x + 3, rect.y + 4))

        item_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(item_surf, self.color, item_surf.get_rect(), border_radius=12)
        text_surf = font.render(self.name, True, C_WHITE)
        item_surf.blit(text_surf, text_surf.get_rect(center=(self.w // 2, self.h // 2)))

        # When rotating, compute a blit rect that keeps the tag centered where it should be
        angle = self.rot if not self.dragging else 0
        rotated = pygame.transform.rotate(item_surf, angle)
        blit_rect = rotated.get_rect(center=(self.x + self.w / 2, self.y + self.h / 2))
        surf.blit(rotated, blit_rect)


@dataclass
class Bin:
    label: str
    color: Tuple[int, int, int]
    rect: pygame.Rect

    def draw(self, surf: pygame.Surface, font: pygame.font.Font):
        # Bin body
        pygame.draw.rect(surf, self.color, self.rect, border_radius=16)
        # Lip/top
        lip = pygame.Rect(self.rect.x - 6, self.rect.y - 14, self.rect.w + 12, 20)
        lip_color = tuple(min(255, int(c * 0.85)) for c in self.color)
        pygame.draw.rect(surf, lip_color, lip, border_radius=12)
        # Label
        lbl = font.render(self.label, True, C_WHITE)
        surf.blit(lbl, lbl.get_rect(center=(self.rect.centerx, self.rect.centery)))


# --------------------------- Game -----------------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Recycling Sorter - Gamified Environmental Education")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()

        # Fonts (fallback to default if the named font isn't available)
        self.font = pygame.font.SysFont("bahnschrift", 22)
        self.font_small = pygame.font.SysFont("bahnschrift", 18)
        self.font_big = pygame.font.SysFont("bahnschrift", 36)
        self.font_huge = pygame.font.SysFont("bahnschrift", 56, bold=True)

        # Audio initialization - be resilient if no audio device is present
        self.mixer_available = True
        try:
            pygame.mixer.init()
        except Exception:
            self.mixer_available = False

        # Prepare simple sfx; _gen_beep will return None if generation fails
        self.snd_correct = self._gen_beep(freq=800) if self.mixer_available else None
        self.snd_wrong = self._gen_beep(freq=200) if self.mixer_available else None
        self.snd_levelup = self._gen_beep(freq=1100) if self.mixer_available else None
        self.muted = False

        self.reset(full=True)

    def _gen_beep(self, freq=440, ms=120):
        # Try to synthesize a short sine beep. If anything goes wrong, return None.
        if not self.mixer_available:
            return None
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * (ms / 1000.0))
            buf = bytearray()
            volume = 0.5
            for i in range(n_samples):
                t = i / sample_rate
                sample = int(math.sin(2 * math.pi * freq * t) * 32767 * volume)
                # little-endian 16-bit signed
                buf += sample.to_bytes(2, byteorder="little", signed=True)
            # Wrap in try/except because some pygame builds may not accept raw bytes here
            try:
                return pygame.mixer.Sound(buffer=bytes(buf))
            except Exception:
                return None
        except Exception:
            return None

    def reset(self, full=False):
        self.items: List[Item] = []
        self.score = 0
        self.hiscore = load_hiscore()
        self.lives = LIVES_START
        self.level = 0
        self.level_time_left = LEVELS[self.level][2]
        self.level_target = LEVELS[self.level][3]
        self.frames_since_spawn = 0
        self.streak = 0
        self.tip_message = ""
        self.tip_timer = 0.0
        self.state = "MENU" if full else "PLAYING"

        # Build bins evenly across bottom
        margin = 20
        bin_w = (SCREEN_W - margin * (len(BINS) + 1)) // len(BINS)
        bin_h = 110
        y = SCREEN_H - bin_h - 20
        self.bins: List[Bin] = []
        for i, (label, color) in enumerate(BINS):
            x = margin + i * (bin_w + margin)
            self.bins.append(Bin(label, color, pygame.Rect(x, y, bin_w, bin_h)))

        # Background gradient cache
        self.bg = pygame.Surface((SCREEN_W, SCREEN_H))
        for yy in range(SCREEN_H):
            t = yy / SCREEN_H
            r = int(lerp(18, 6, t))
            g = int(lerp(28, 12, t))
            b = int(lerp(38, 22, t))
            pygame.draw.line(self.bg, (r, g, b), (0, yy), (SCREEN_W, yy))

    def spawn_item(self):
        name = random.choice(list(ITEMS.keys()))
        category, tip = ITEMS[name]
        color = {
            "Paper": C_PAPER,
            "Plastic": C_PLASTIC,
            "Metal": C_METAL,
            "Organic": C_ORGANIC,
            "E-Waste": C_EWASTE,
        }[category]
        x = random.randint(60, SCREEN_W - 160)
        y = -50
        vx = random.uniform(-0.3, 0.3)
        vy = random.uniform(0.5, 1.5)
        self.items.append(Item(name, category, tip, x, y, vx, vy, color))

    def play_sfx(self, snd: Optional[pygame.mixer.Sound]):
        if self.muted or snd is None:
            return
        try:
            snd.play()
        except Exception:
            pass

    def update(self, dt: float):
        if self.state != "PLAYING":
            return

        fall_speed, spawn_interval, level_secs, _ = LEVELS[self.level]
        self.frames_since_spawn += 1
        if self.frames_since_spawn >= spawn_interval:
            self.frames_since_spawn = 0
            self.spawn_item()

        # Update items
        for it in self.items[:]:
            it.update(fall_speed)
            # Missed item (fell past bottom)
            if it.y > SCREEN_H + 60:
                try:
                    self.items.remove(it)
                except ValueError:
                    pass
                self.register_miss("Item fell off screen")

        # Tip timer
        if self.tip_timer > 0:
            self.tip_timer -= dt
            if self.tip_timer <= 0:
                self.tip_message = ""

        # Level timer & check progress
        self.level_time_left -= dt
        if self.level_time_left <= 0:
            # Advance if score meets target
            if self.score >= self.level_target and self.level < len(LEVELS) - 1:
                self.level += 1
                self.level_time_left = LEVELS[self.level][2]
                self.level_target = LEVELS[self.level][3]
                self.tip_message = f"Level up! Level {self.level + 1} 🎉"
                self.tip_timer = 3.0
                self.play_sfx(self.snd_levelup)
            else:
                # End game
                self.game_over()

    def register_hit(self, correct: bool, tip: str):
        if correct:
            self.streak += 1
            base = 50
            bonus = min(5 * self.streak, 150)  # streak multiplier
            self.score += base + bonus
            self.tip_message = tip
            self.tip_timer = 3.5
            self.play_sfx(self.snd_correct)
        else:
            self.register_miss("Wrong bin! -1 life.")
            self.tip_message = tip
            self.tip_timer = 3.5
            self.play_sfx(self.snd_wrong)

    def register_miss(self, reason="Miss"):
        self.streak = 0
        self.lives -= 1
        if self.lives <= 0:
            self.game_over()

    def game_over(self):
        self.state = "GAMEOVER"
        if self.score > self.hiscore:
            save_hiscore(self.score)
            self.hiscore = self.score

    def handle_mouse_down(self, pos):
        if self.state != "PLAYING":
            return
        for it in reversed(self.items):
            if it.rect().collidepoint(pos):
                it.dragging = True
                mx, my = pos
                it.grabbed_dx = it.x - mx
                it.grabbed_dy = it.y - my
                return

    def handle_mouse_up(self, pos):
        if self.state != "PLAYING":
            return
        for it in self.items:
            if it.dragging:
                it.dragging = False
                # Check overlap with a bin
                placed = False
                for b in self.bins:
                    if b.rect.colliderect(it.rect()):
                        placed = True
                        try:
                            self.items.remove(it)
                        except ValueError:
                            pass
                        correct = (it.category == b.label)
                        tip = (f"✅ {it.name}: {it.tip}" if correct
                               else f"❌ {it.name} goes in {it.category} bin.")
                        self.register_hit(correct, tip)
                        break
                return

    def handle_mouse_motion(self, pos):
        if self.state != "PLAYING":
            return
        mx, my = pos
        for it in self.items:
            if it.dragging:
                it.x = mx + it.grabbed_dx
                it.y = my + it.grabbed_dy
                it.vx = 0
                it.vy = 0

    def draw_hud(self):
        # Top bar
        hud_h = 72
        pygame.draw.rect(self.screen, C_DIM, (0, 0, SCREEN_W, hud_h))
        # Score
        score_s = self.font_big.render(f"Score: {self.score}", True, C_WHITE)
        self.screen.blit(score_s, (20, 18))
        # Hiscore
        hs_s = self.font.render(f"High: {self.hiscore}", True, C_WHITE)
        self.screen.blit(hs_s, (20, 50))
        # Lives
        lives_surf = self.font.render(f"Lives: {'❤' * self.lives}", True, (255, 90, 90))
        self.screen.blit(lives_surf, (220, 24))
        # Streak
        if self.streak >= 2:
            streak_s = self.font.render(f"Streak x{self.streak}", True, C_GOLD)
            self.screen.blit(streak_s, (220, 50))
        # Level & time
        lvl_s = self.font_big.render(f"Level {self.level + 1}", True, C_WHITE)
        self.screen.blit(lvl_s, (SCREEN_W - 300, 12))
        time_s = self.font.render(f"Time Left: {max(0, int(self.level_time_left))}s", True, C_WHITE)
        self.screen.blit(time_s, (SCREEN_W - 300, 50))
        # Target
        target_s = self.font.render(f"Target: {self.level_target}", True, C_WHITE)
        self.screen.blit(target_s, (SCREEN_W - 120, 50))

    def draw_tip(self):
        if not self.tip_message:
            return
        pad = 12
        text = self.font_small.render(self.tip_message, True, C_WHITE)
        w, h = text.get_size()
        box = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(box, (0, 0, 0, 140), (0, 0, w + pad * 2, h + pad * 2), border_radius=12)
        box.blit(text, (pad, pad))
        self.screen.blit(box, box.get_rect(center=(SCREEN_W // 2, 120)))

    def draw_bins(self):
        for b in self.bins:
            b.draw(self.screen, self.font)

    def draw_items(self):
        for it in self.items:
            it.draw(self.screen, self.font)

    def draw_menu(self):
        title = self.font_huge.render("Recycling Sorter", True, C_WHITE)
        sub = self.font_big.render("Drag items into the correct bin!", True, (220, 220, 220))
        note = self.font.render("Press SPACE to start • P to pause • M to mute", True, (210, 210, 210))

        self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 160)))
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 220)))
        self.screen.blit(note, note.get_rect(center=(SCREEN_W // 2, 270)))

        # Educational blurb
        blurb_lines = [
            "Tips:",
            "• Keep recyclables clean & dry. Contamination sends whole batches to landfill.",
            "• Organic waste can be composted to cut methane emissions.",
            "• E-waste contains valuable metals—recycle at certified centers.",
        ]
        y = 340
        for line in blurb_lines:
            s = self.font.render(line, True, C_WHITE)
            self.screen.blit(s, s.get_rect(center=(SCREEN_W // 2, y)))
            y += 30

        # Draw bins preview
        self.draw_bins()

    def draw_pause(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        s = self.font_huge.render("Paused", True, C_WHITE)
        self.screen.blit(s, s.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 20)))
        tip = self.font.render("Press P to resume • M to mute/unmute", True, C_WHITE)
        self.screen.blit(tip, tip.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 30)))

    def draw_gameover(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        s = self.font_huge.render("Game Over", True, C_WHITE)
        self.screen.blit(s, s.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 60)))
        sc = self.font_big.render(f"Score: {self.score}   High: {self.hiscore}", True, C_WHITE)
        self.screen.blit(sc, sc.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
        tip = self.font.render("Press R to restart • ESC to quit", True, C_WHITE)
        self.screen.blit(tip, tip.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 60)))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1_000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and self.state == "MENU":
                        self.state = "PLAYING"
                    elif event.key == pygame.K_p and self.state == "PLAYING":
                        self.state = "PAUSE"
                    elif event.key == pygame.K_p and self.state == "PAUSE":
                        self.state = "PLAYING"
                    elif event.key == pygame.K_m:
                        self.muted = not self.muted
                    elif event.key == pygame.K_r and self.state == "GAMEOVER":
                        self.reset(full=False)
                        self.state = "PLAYING"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse_down(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.handle_mouse_up(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)

            if self.state == "PLAYING":
                self.update(dt)

            # Draw
            self.screen.blit(self.bg, (0, 0))
            self.draw_bins()
            self.draw_items()
            self.draw_hud()
            self.draw_tip()

            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "PAUSE":
                self.draw_pause()
            elif self.state == "GAMEOVER":
                self.draw_gameover()

            pygame.display.flip()

        pygame.quit()


# --------------------------- Main -----------------------------------
if __name__ == "__main__":
    Game().run()
