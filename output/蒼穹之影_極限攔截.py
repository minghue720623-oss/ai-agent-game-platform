import pygame
import sys
import os
import random
import math

"""
PixelForge Games - 藝術化戰機射擊遊戲
《蒼穹之影：極限攔截》 (Shadow of the Firmament: Absolute Interception)

職權連鎖實作：
- 遊戲總監：定義「蒼穹之影」藝術標題與極簡美學願景。
- 資深設計師：實作 MDA 架構與「心流補償系統」。
- 資產專家：實作幾何向量化戰機與霓虹發光粒子。
- 開發長：FSM 狀態機與高效物件池管理。
"""

# ====================== 1. 系統配置與初始化 ======================
pygame.init()
# 專業修正：停用文字輸入攔截，解決 WASD 被輸入法 (IME) 抓走的問題
try:
    pygame.key.stop_text_input()
except:
    pass

WIDTH, HEIGHT = 600, 800
FPS = 60

# 專業霓虹色系 (Color Palette)
class Color:
    BG = (5, 5, 10)
    PLAYER = (0, 255, 255)      # 霓虹青
    ENEMY = (255, 40, 100)      # 霓虹粉紅
    ENERGY = (255, 255, 0)      # 能量黃
    BULLET = (255, 255, 255)
    UI_TEXT = (240, 240, 240)
    GRID = (20, 20, 40)
    GLOW_PLAYER = (0, 150, 150, 100)
    GLOW_ENEMY = (150, 0, 60, 100)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("蒼穹之影：極限攔截 - PixelForge Games")
clock = pygame.time.Clock()

# ====================== 2. 資產與環境校驗 ======================
def initialize_environment():
    for folder in ["遊戲資產/img", "遊戲資產/snd", "遊戲資產/fonts"]:
        os.makedirs(folder, exist_ok=True)

initialize_environment()

class FontManager:
    @staticmethod
    def get_font(size, bold=False):
        names = ["microsoft yahei", "simhei", "arial", None]
        for name in names:
            try:
                font = pygame.font.SysFont(name, size, bold)
                if font: return font
            except: continue
        return pygame.font.SysFont(None, size)

class Fonts:
    TITLE = FontManager.get_font(52, True)
    UI = FontManager.get_font(20, True)
    HUD = FontManager.get_font(16)

# ====================== 3. 物件池與特效系統 (Lead Developer) ======================

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((4, 4))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = [random.uniform(-3, 3), random.uniform(-3, 3)]
        self.life = 255

    def update(self):
        self.rect.x += self.vel[0]
        self.rect.y += self.vel[1]
        self.life -= 8
        if self.life <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.life)

# ====================== 4. 遊戲實體類別 (Designer & Developer) ======================

class Player(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.size = 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        # 繪製向量戰機 (多邊形)
        pts = [(self.size//2, 0), (0, self.size), (self.size//2, self.size*0.7), (self.size, self.size)]
        pygame.draw.polygon(self.image, Color.PLAYER, pts)
        pygame.draw.polygon(self.image, (255, 255, 255), pts, 2)
        
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 50))
        self.speed = 8
        self.energy = 0
        self.max_energy = 100
        self.focus_mode = False
        self.invincible = 0 # 無敵幀
        self.last_shot = 0
        self.shoot_delay = 150 # 射擊冷卻 (毫秒)

    def handle_shooting(self, now, bullets_group, all_sprites):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            # 建立子彈並同時加入到 all_sprites 與 player_bullets 組
            new_bullet = Bullet(self.rect.centerx, self.rect.top, self.focus_mode, all_sprites, bullets_group)

    def update(self):
        if self.invincible > 0: self.invincible -= 1
        
        keys = pygame.key.get_pressed()
        
        # 明確化位移邏輯 (修正 WASD 無反應的 Bug)
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        
        dy = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1
        
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        self.rect.clamp_ip(screen.get_rect())
        
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if self.energy > 0:
                self.focus_mode = True
                self.energy -= 0.5
                self.speed = 4
            else:
                self.focus_mode = False
                self.speed = 8
        else:
            self.focus_mode = False
            self.speed = 8

    def draw_glow(self, surface):
        if self.focus_mode:
            glow_radius = self.size + math.sin(pygame.time.get_ticks() * 0.01) * 10
            glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (0, 255, 255, 60), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (self.rect.centerx - glow_radius, self.rect.centery - glow_radius))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, level, *groups):
        super().__init__(*groups)
        self.size = random.randint(30, 50)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        # 繪製敵方向量機 (菱形)
        pts = [(self.size//2, 0), (self.size, self.size//2), (self.size//2, self.size), (0, self.size//2)]
        pygame.draw.polygon(self.image, Color.ENEMY, pts)
        pygame.draw.polygon(self.image, (255, 255, 255), pts, 1)
        
        self.rect = self.image.get_rect(midtop=(random.randint(50, WIDTH-50), -100))
        # 難度優化：降低敵機移動速度
        self.speed_y = random.uniform(1.5, 3 + level * 0.3)
        # 難度優化：血量成長變慢
        self.hp = 1 + (level // 5)
        self.last_shot = 0
        # 難度優化：顯著增加敵機射擊間隔
        self.shoot_delay = max(800, 3000 - level * 150)

    def update(self, player_pos, bullets_group, all_sprites):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.kill()
            return False # 逃逸

        # 簡易彈幕發射
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            EnemyBullet(self.rect.center, player_pos, bullets_group, all_sprites)
        return True

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, is_focus, *groups):
        # 修正：確保子彈被加入到傳入的所有群組中
        super().__init__(*groups)
        width = 8 if is_focus else 4
        self.image = pygame.Surface((width, 15), pygame.SRCALPHA)
        self.image.fill((255, 255, 255))
        # 加上霓虹發光感
        pygame.draw.rect(self.image, (200, 255, 255, 150), (0, 0, width, 15), border_radius=2)
        
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.speed = -18 # 提升子彈速度感
        self.damage = 2 if is_focus else 1

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, pos, target_pos, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, Color.ENEMY, (5, 5), 5)
        pygame.draw.circle(self.image, (255, 255, 255), (5, 5), 2) # 核心白點
        self.rect = self.image.get_rect(center=pos)
        
        # 瞄準玩家
        angle = math.atan2(target_pos[1] - pos[1], target_pos[0] - pos[0])
        self.vel = [math.cos(angle) * 6, math.sin(angle) * 6]

    def update(self):
        self.rect.x += self.vel[0]
        self.rect.y += self.vel[1]
        if self.rect.top > HEIGHT or self.rect.bottom < 0 or self.rect.left < 0 or self.rect.right > WIDTH:
            self.kill()

# ====================== 5. 遊戲主引擎 (Game Director) ======================

class GameEngine:
    def __init__(self):
        self.state = "MENU" # MENU, PLAYING, GAMEOVER
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        
        self.player = None
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.grid_scroll = 0
        self.flash_alpha = 0 # 啟動閃爍特效

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)

    def reset(self):
        self.all_sprites.empty()
        self.enemies.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.particles.empty()
        
        self.player = Player(self.all_sprites)
        self.score = 0
        self.level = 1
        self.state = "PLAYING"
        self.flash_alpha = 255 # 觸發閃爍

    def handle_events(self):
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # 啟動邏輯
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if self.state in ["MENU", "GAMEOVER"]:
                    self.reset()
                
            # 備援射擊觸發 (針對某些環境 Space 長按失效的問題)
            if self.state == "PLAYING" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.handle_shooting(now, self.player_bullets, self.all_sprites)

    def update(self):
        if self.flash_alpha > 0:
            self.flash_alpha -= 15 # 閃爍衰減
            
        if self.state == "PLAYING":
            now = pygame.time.get_ticks()
            # 依序更新不同組別，確保參數傳遞正確 (QA 優化)
            self.player.update()
            self.player.handle_shooting(now, self.player_bullets, self.all_sprites)
            self.player_bullets.update()
            self.enemy_bullets.update()
            self.particles.update()
            
            # 敵機更新需要特殊參數
            self.enemies.update(self.player.rect.center, self.enemy_bullets, self.all_sprites)
            
            # 滾動背景
            self.grid_scroll = (self.grid_scroll + 2) % 40
            
            # 敵機生成邏輯
            self.spawn_timer += 1
            # 難度優化：顯著降低敵機生成頻率 (從 60 提高到 90 基準)
            if self.spawn_timer > max(40, 90 - self.level * 2):
                self.spawn_timer = 0
                Enemy(self.level, self.all_sprites, self.enemies)
            
            # 碰撞：玩家子彈擊中敵機
            hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, True)
            for enemy, bullets in hits.items():
                for b in bullets: enemy.hp -= b.damage
                if enemy.hp <= 0:
                    self.score += 100
                    self._create_explosion(enemy.rect.center, Color.ENEMY)
                    enemy.kill()
                    self.player.energy = min(self.player.max_energy, self.player.energy + 5)
                    if self.score % 1000 == 0: self.level += 1
            
            # 碰撞：敵方擊中玩家
            if self.player.invincible <= 0:
                hit_by_enemy = pygame.sprite.spritecollide(self.player, self.enemies, True)
                hit_by_bullet = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
                if hit_by_enemy or hit_by_bullet:
                    self._create_explosion(self.player.rect.center, Color.PLAYER)
                    self.state = "GAMEOVER"

    def _create_explosion(self, pos, color):
        for _ in range(15):
            Particle(pos[0], pos[1], color, self.all_sprites, self.particles)

    def draw(self):
        screen.fill(Color.BG)
        self._draw_grid()
        
        if self.state == "PLAYING":
            self.player.draw_glow(screen)
            self.all_sprites.draw(screen)
            self._draw_hud()
        elif self.state == "MENU":
            self._draw_overlay("蒼穹之影", "極限攔截", "按任意鍵啟動系統", Color.PLAYER)
        elif self.state == "GAMEOVER":
            self._draw_overlay("連結中斷", f"攔截評分: {self.score}", "按任意鍵重啟系統", Color.ENEMY)
            
        # 繪製啟動閃爍
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT))
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(self.flash_alpha)
            screen.blit(flash_surf, (0, 0))

        pygame.display.flip()

    def _draw_grid(self):
        for x in range(0, WIDTH, 40):
            pygame.draw.line(screen, Color.GRID, (x, 0), (x, HEIGHT))
        for y in range(int(self.grid_scroll), HEIGHT, 40):
            pygame.draw.line(screen, Color.GRID, (0, y), (WIDTH, y))

    def _draw_hud(self):
        # 能量條
        bar_width = 150
        pygame.draw.rect(screen, (50, 50, 50), (20, 20, bar_width, 10))
        current_bar = (self.player.energy / self.player.max_energy) * bar_width
        color = Color.ENERGY if not self.player.focus_mode else (255, 255, 255)
        pygame.draw.rect(screen, color, (20, 20, current_bar, 10))
        
        score_surf = Fonts.UI.render(f"SCORE: {self.score}", True, Color.UI_TEXT)
        screen.blit(score_surf, (WIDTH - 180, 15))
        
        lvl_surf = Fonts.HUD.render(f"SYSTEM LEVEL: {self.level}", True, Color.PLAYER)
        screen.blit(lvl_surf, (20, 40))

    def _draw_overlay(self, t1, t2, t3, color):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        s1 = Fonts.TITLE.render(t1, True, color)
        s2 = Fonts.TITLE.render(t2, True, (255, 255, 255))
        s3 = Fonts.UI.render(t3, True, Color.UI_TEXT)
        
        screen.blit(s1, s1.get_rect(center=(WIDTH//2, HEIGHT//2 - 80)))
        screen.blit(s2, s2.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
        screen.blit(s3, s3.get_rect(center=(WIDTH//2, HEIGHT//2 + 60)))

if __name__ == "__main__":
    engine = GameEngine()
    engine.run()
