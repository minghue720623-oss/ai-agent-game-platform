import pygame
import sys
import os
import random
import math
import json
import urllib.request
import array

# ====================== 0. 音效合成引擎 ======================
class SoundManager:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.bgm_channel = pygame.mixer.Channel(0)
        self.sfx_channel = pygame.mixer.Channel(1)
        self.sfx_channel_alt = pygame.mixer.Channel(2)
        self.generate_procedural_bgm()

    def make_tone(self, freq, duration, volume=0.1, type='square'):
        n_samples = int(22050 * duration)
        buf = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            t = i / 22050
            if type == 'square':
                sample = 32767 * volume * (1 if math.sin(2 * math.pi * freq * t) > 0 else -1)
            elif type == 'saw':
                sample = 32767 * volume * (2 * (t * freq - math.floor(t * freq + 0.5)))
            else: # sine
                sample = 32767 * volume * math.sin(2 * math.pi * freq * t)
            buf[i] = int(sample)
        return pygame.mixer.Sound(buffer=buf)

    def generate_procedural_bgm(self):
        seq = [110, 0, 110, 130, 0, 110, 164, 0, 110, 110, 196, 0, 130, 164, 0, 110]
        combined_samples = array.array('h')
        for freq in seq:
            n_samples = int(22050 * 0.5) 
            for i in range(n_samples):
                t = i / 22050
                if freq == 0:
                    combined_samples.append(0)
                else:
                    val = math.sin(2 * math.pi * freq * t) + 0.2 * math.sin(2 * math.pi * freq * 2 * t)
                    sample = 32767 * 0.02 * val
                    combined_samples.append(int(sample))
        self.bgm = pygame.mixer.Sound(buffer=combined_samples)

    def play_bgm(self):
        self.bgm_channel.play(self.bgm, loops=-1)

    def play_patch_sfx(self):
        s = self.make_tone(660, 0.04, 0.015, 'sine')
        self.sfx_channel.play(s)

    def play_overclock_sfx(self):
        s = self.make_tone(1000, 0.02, 0.01, 'sine')
        self.sfx_channel_alt.play(s)

    def play_scanner_sfx(self):
        n_samples = int(22050 * 0.15)
        buf = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            t = i / 22050
            f = 1200 - (t * 2000) 
            sample = 32767 * 0.02 * math.sin(2 * math.pi * f * t)
            buf[i] = int(sample)
        self.sfx_channel.play(pygame.mixer.Sound(buffer=buf))

    def play_firewall_sfx(self):
        s = self.make_tone(150, 0.05, 0.01, 'sine')
        self.sfx_channel_alt.play(s)

    def play_explode(self):
        s = self.make_tone(80, 0.15, 0.06, 'square')
        self.sfx_channel.play(s)

    def play_level_up(self):
        combined = array.array('h')
        for f in [440, 660, 880]:
            n = int(22050 * 0.1)
            for i in range(n):
                combined.append(int(32767 * 0.05 * math.sin(2 * math.pi * f * (i/22050))))
        self.sfx_channel.play(pygame.mixer.Sound(buffer=combined))

    def play_pickup_hp(self):
        s = self.make_tone(1320, 0.1, 0.04, 'sine')
        self.sfx_channel_alt.play(s)

    def play_pickup_magnet(self):
        s = self.make_tone(440, 0.2, 0.04, 'saw')
        self.sfx_channel_alt.play(s)

    def play_dash_sfx(self):
        n_samples = int(22050 * 0.1)
        buf = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            t = i / 22050
            f = 400 + (t * 2000)
            sample = 32767 * 0.02 * math.sin(2 * math.pi * f * t) * (1.0 - t/0.1)
            buf[i] = int(sample)
        self.sfx_channel_alt.play(pygame.mixer.Sound(buffer=buf))

"""
PixelForge Games - 專業技術實體化作品
《代碼保衛戰》(Code Defender)
"""

# ====================== 1. 系統配置與初始化 ======================
pygame.init()
try:
    pygame.key.stop_text_input()
except:
    pass

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
WORLD_WIDTH = 4000
WORLD_HEIGHT = 3200 
FPS = 60

class Color:
    BG = (5, 5, 15)
    PLAYER = (0, 255, 100)
    BUG = (255, 50, 50)
    FAST_BUG = (255, 200, 0)
    TANK_BUG = (150, 50, 255)
    PATCH = (0, 200, 255)
    SCANNER = (0, 255, 255)
    EXP = (255, 255, 0)
    UI_TEXT = (200, 220, 255)
    GRID = (20, 30, 50)
    BORDER = (0, 120, 255)
    CRATE = (180, 130, 70)
    MAGNET = (255, 100, 255)
    BOSS_HP = (255, 0, 100)
    GLOW = (0, 100, 255, 60)
    WHITE = (255, 255, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("代碼保衛戰 (Code Defender) - PixelForge Games")
clock = pygame.time.Clock()

DEFAULT_UPGRADES = [
    {"id": "firewall", "name": "雲端防火牆", "desc": "發射環繞伺服器的防禦屏障", "type": "WEAPON"},
    {"id": "patch", "name": "自動補丁", "desc": "自動攻擊最近的系統漏洞", "type": "WEAPON"},
    {"id": "overclock", "name": "核心超頻", "desc": "極速發射高頻率數據包", "type": "WEAPON"},
    {"id": "scanner", "name": "漏洞掃描器", "desc": "發射強力穿透束，清除路徑上所有威脅", "type": "WEAPON"},
    {"id": "ram", "name": "記憶體優化", "desc": "提升 15% 移動速度", "type": "BUFF"},
    {"id": "cache", "name": "快取加速", "desc": "縮短 10% 技能冷卻", "type": "BUFF"},
    {"id": "regen", "name": "自動修復", "desc": "系統背景執行修復，每 10 秒恢復 1% 生命", "type": "BUFF"}
]

class GitHubDataSource:
    def __init__(self, repo_path="pygame/pygame"):
        self.repo_path = repo_path
        self.data = DEFAULT_UPGRADES
        self.stats = {"issues": 0, "stars": 0, "name": "Local Cache"}
        self.connected = False
        
    def fetch_data(self):
        try:
            url = f"https://api.github.com/repos/{self.repo_path}"
            headers = {"User-Agent": "CodeDefender-Game-Client"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as response:
                res_data = json.loads(response.read().decode())
                self.stats["issues"] = res_data.get("open_issues_count", 0)
                self.stats["stars"] = res_data.get("stargazers_count", 0)
                self.stats["name"] = res_data.get("full_name", self.repo_path)
                self.connected = True
        except:
            self.connected = False

# ====================== 3. 武器系統 ======================

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, target_pos, speed, color, damage, owner="player", *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (7, 7), 7)
        pygame.draw.circle(self.image, Color.WHITE, (7, 7), 3)
        self.rect = self.image.get_rect(center=pos)
        self.damage = damage
        self.owner = owner
        dx = target_pos[0] - pos[0]
        dy = target_pos[1] - pos[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vel = [(dx/dist)*speed, (dy/dist)*speed]
        else:
            self.vel = [0, -speed]

    def update(self):
        self.rect.x += self.vel[0]
        self.rect.y += self.vel[1]
        if self.rect.x < -1000 or self.rect.x > WORLD_WIDTH+1000 or self.rect.y < -1000 or self.rect.y > WORLD_HEIGHT+1000:
            self.kill()

class BaseWeapon:
    def __init__(self, player, weapon_id):
        self.player = player
        self.weapon_id = weapon_id
        self.level = 1
        self.max_level = 5
        self.cooldown = 0
        self.max_cooldown = 60

    def level_up(self):
        if self.level < self.max_level:
            self.level += 1
            self.on_level_up()

    def on_level_up(self):
        pass

    def update(self, bugs, all_sprites, bullets):
        if self.cooldown > 0:
            self.cooldown -= 1
        else:
            if self.fire(bugs, all_sprites, bullets):
                reduction = 1.0 - (self.player.buffs.get("cache", 0) * 0.1)
                self.cooldown = self.max_cooldown * reduction

    def fire(self, bugs, all_sprites, bullets):
        return False

class AutoPatchWeapon(BaseWeapon):
    def __init__(self, player):
        super().__init__(player, "patch")
        self.max_cooldown = 45
        self.damage = 2

    def on_level_up(self):
        self.damage += 1
        self.max_cooldown = max(15, self.max_cooldown - 5)

    def fire(self, bugs, all_sprites, bullets):
        closest = None
        min_d = 600
        for bug in bugs:
            d = math.hypot(bug.rect.centerx - self.player.rect.centerx, bug.rect.centery - self.player.rect.centery)
            if d < min_d:
                min_d = d
                closest = bug
        if closest:
            Projectile(self.player.rect.center, closest.rect.center, 12, Color.PATCH, self.damage, "player", self.player.game_ref.all_sprites, bullets)
            if self.player.game_ref and self.player.game_ref.sound:
                self.player.game_ref.sound.play_patch_sfx()
            return True
        return False

class OverclockWeapon(BaseWeapon):
    def __init__(self, player):
        super().__init__(player, "overclock")
        self.max_cooldown = 20
        self.damage = 1
        self.projectiles = 1

    def on_level_up(self):
        self.damage += 0.5
        if self.level % 2 == 0:
            self.projectiles += 1

    def fire(self, bugs, all_sprites, bullets):
        if not bugs: return False
        targets = random.choices(list(bugs), k=min(self.projectiles, len(bugs)))
        for t in targets:
            Projectile(self.player.rect.center, t.rect.center, 18, (255, 100, 0), self.damage, "player", self.player.game_ref.all_sprites, bullets)
        if self.player.game_ref and self.player.game_ref.sound:
            self.player.game_ref.sound.play_overclock_sfx()
        return True

class PiercingShot(pygame.sprite.Sprite):
    def __init__(self, pos, target_pos, speed, color, damage, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(self.image, color, (0, 15, 40, 10))
        pygame.draw.rect(self.image, Color.WHITE, (5, 17, 30, 6))
        dx = target_pos[0] - pos[0]
        dy = target_pos[1] - pos[1]
        angle = math.degrees(math.atan2(-dy, dx))
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=pos)
        self.damage = damage
        self.is_piercing = True
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vel = [(dx/dist)*speed, (dy/dist)*speed]
        else:
            self.vel = [speed, 0]

    def update(self):
        self.rect.x += self.vel[0]
        self.rect.y += self.vel[1]
        if self.rect.x < -1000 or self.rect.x > WORLD_WIDTH+1000 or self.rect.y < -1000 or self.rect.y > WORLD_HEIGHT+1000:
            self.kill()

class ScannerWeapon(BaseWeapon):
    def __init__(self, player):
        super().__init__(player, "scanner")
        self.max_cooldown = 100
        self.damage = 3

    def on_level_up(self):
        self.damage += 2
        self.max_cooldown = max(40, self.max_cooldown - 10)

    def fire(self, bugs, all_sprites, bullets):
        if not bugs: return False
        closest = min(bugs, key=lambda b: math.hypot(b.rect.centerx-self.player.rect.centerx, b.rect.centery-self.player.rect.centery))
        PiercingShot(self.player.rect.center, closest.rect.center, 14, Color.SCANNER, self.damage, self.player.game_ref.all_sprites, bullets)
        if self.player.game_ref and self.player.game_ref.sound:
            self.player.game_ref.sound.play_scanner_sfx()
        return True

class FirewallWeapon(BaseWeapon):
    def __init__(self, player):
        super().__init__(player, "firewall")
        self.max_cooldown = 120
        self.angle = 0
        self.damage = 0.15
        self.sfx_timer = 0

    def on_level_up(self):
        self.damage += 0.1

    def update(self, bugs, all_sprites, bullets):
        self.angle += 0.05 + (self.level * 0.01)
        self.player.firewall_active = True
        self.player.firewall_angle = self.angle
        self.sfx_timer += 1
        if self.sfx_timer > 45:
            self.sfx_timer = 0
            if self.player.game_ref and self.player.game_ref.sound:
                self.player.game_ref.sound.play_firewall_sfx()

# ====================== 4. 遊戲實體類別 ======================

class Player(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.size = 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pts = []
        for i in range(6):
            angle = math.radians(i * 60)
            pts.append((self.size//2 + math.cos(angle)*self.size//2, self.size//2 + math.sin(angle)*self.size//2))
        pygame.draw.polygon(self.image, Color.PLAYER, pts)
        pygame.draw.polygon(self.image, Color.WHITE, pts, 2)
        self.rect = self.image.get_rect(center=(WORLD_WIDTH//2, WORLD_HEIGHT//2))
        self.speed = 5.0
        self.level = 1
        self.exp = 0
        self.max_exp = 10
        self.hp = 100
        self.max_hp = 100
        self.weapons = []
        self.buffs = {"ram": 0, "cache": 0, "regen": 0}
        self.firewall_active = False
        self.firewall_angle = 0
        self.hit_timer = 0
        self.game_ref = None
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_direction = [0, 0]
        self.is_dashing = False
        self.afterimage_timer = 0
        self.regen_timer = 0

    def update(self):
        if self.buffs["regen"] > 0:
            self.regen_timer += 1
            if self.regen_timer >= 600:
                self.regen_timer = 0
                heal_amount = self.max_hp * 0.01 * self.buffs["regen"]
                self.hp = min(self.max_hp, self.hp + heal_amount)

        if self.hit_timer > 0: self.hit_timer -= 1
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
        if dx != 0 and dy != 0: dx *= 0.707; dy *= 0.707
        
        if keys[pygame.K_SPACE] and self.dash_cooldown == 0 and (dx != 0 or dy != 0):
            self.is_dashing = True
            self.dash_timer = 12
            self.dash_cooldown = 60
            self.dash_direction = [dx, dy]
            if self.game_ref and self.game_ref.sound:
                self.game_ref.sound.play_dash_sfx()
        
        if self.is_dashing:
            self.rect.x += self.dash_direction[0] * 15.0
            self.rect.y += self.dash_direction[1] * 15.0
            self.dash_timer -= 1
            self.afterimage_timer += 1
            if self.afterimage_timer % 3 == 0:
                DashAfterimage(self.rect.center, self.image, self.groups())
            if self.dash_timer <= 0:
                self.is_dashing = False
        else:
            speed = self.speed * (1.0 + self.buffs["ram"] * 0.15)
            self.rect.x += dx * speed
            self.rect.y += dy * speed
            
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        self.rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))

class DashAfterimage(pygame.sprite.Sprite):
    def __init__(self, pos, img, *groups):
        super().__init__(*groups)
        self.image = img.copy()
        self.image.fill((0, 100, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)
        self.rect = self.image.get_rect(center=pos)
        self.alpha = 150
    def update(self):
        self.alpha -= 15
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.alpha)

class Bug(pygame.sprite.Sprite):
    def __init__(self, player, color=Color.BUG, size_range=(25, 40), hp_mult=1.0, speed_range=(1.5, 3.0), *groups):
        super().__init__(*groups)
        self.size = random.randint(*size_range)
        self.base_color = color
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.draw_bug(self.base_color)
        self.rect = self.image.get_rect()
        angle = random.uniform(0, math.pi * 2)
        dist = 800
        self.rect.center = (player.rect.centerx + math.cos(angle)*dist, player.rect.centery + math.sin(angle)*dist)
        self.hp = (1.2 + (player.level // 4)) * hp_mult
        self.speed = random.uniform(*speed_range) * 0.75
        self.player = player
        self.flash_timer = 0
        self.hit_by = set()

    def draw_bug(self, c):
        self.image.fill((0,0,0,0))
        pts = [(self.size//2, 0), (0, self.size), (self.size, self.size)]
        pygame.draw.polygon(self.image, c, pts)
        pygame.draw.polygon(self.image, Color.WHITE, pts, 1)

    def take_damage(self, amt, bullet=None):
        if bullet and hasattr(bullet, 'is_piercing'):
            if id(bullet) in self.hit_by: return False
            self.hit_by.add(id(bullet))
        self.hp -= amt
        self.flash_timer = 5
        self.draw_bug(Color.WHITE)
        return True

    def update(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.draw_bug(self.base_color)
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.rect.x += (dx/dist)*self.speed
            self.rect.y += (dy/dist)*self.speed

class FastBug(Bug):
    def __init__(self, p, *groups):
        super().__init__(p, Color.FAST_BUG, (18, 24), 0.6, (3.5, 5.0), *groups)
class TankBug(Bug):
    def __init__(self, p, *groups):
        super().__init__(p, Color.TANK_BUG, (55, 75), 6.0, (0.8, 1.2), *groups)

class BossBug(Bug):
    def __init__(self, p, boss_count, *groups):
        # 將基礎 HP 倍率從 80.0 進一步下調至 60.0，使挑戰更輕鬆
        hp_mult = 60.0 * (1.0 + boss_count * 0.4)
        speed_min = 2.5 + boss_count * 0.2
        speed_max = 3.2 + boss_count * 0.2
        super().__init__(p, (200, 0, 100), (120, 120), hp_mult, (speed_min, speed_max), *groups)
        self.max_hp = self.hp
        self.attack_timer = 0
        self.boss_count = boss_count
        self.name = f"【 核心威脅：邏輯炸彈 v{boss_count + 1}.0 】"
        self.rotation_angle = 0
        self.glitch_timer = 0

    def draw_bug(self, c):
        pass

    def update(self):
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed
        if self.flash_timer > 0:
            self.flash_timer -= 1
        self.rotation_angle += 0.05 + (self.boss_count * 0.01)
        self.glitch_timer += 1
        self.image.fill((0, 0, 0, 0))
        center = self.size // 2
        rect_size = self.size - 20
        surf = pygame.Surface((rect_size, rect_size), pygame.SRCALPHA)
        pygame.draw.rect(surf, (self.base_color[0], self.base_color[1], self.base_color[2], 120), (0, 0, rect_size, rect_size), 6)
        rot_surf = pygame.transform.rotate(surf, math.degrees(self.rotation_angle))
        self.image.blit(rot_surf, (center - rot_surf.get_width()//2, center - rot_surf.get_height()//2))
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 5
        core_size = 30 + pulse
        pygame.draw.circle(self.image, Color.WHITE, (center, center), int(core_size), 2)
        pygame.draw.rect(self.image, Color.BOSS_HP, (center-15, center-15, 30, 30))
        if self.glitch_timer % 10 < 3:
            gx, gy = random.randint(-15, 15), random.randint(-15, 15)
            pygame.draw.line(self.image, Color.SCANNER, (center-40+gx, center+gy), (center+40+gx, center+gy), 2)
        self.attack_timer += 1
        if self.attack_timer > 120:
            self.attack_timer = 0
            self.burst_fire()

    def burst_fire(self):
        if self.player.game_ref: 
            self.player.game_ref.screen_shake = 15
            bullet_count = 16 + self.boss_count * 4
            for i in range(bullet_count):
                angle = i * (math.pi * 2 / bullet_count)
                target = (self.rect.centerx + math.cos(angle)*100, self.rect.centery + math.sin(angle)*100)
                Projectile(self.rect.center, target, 5 + self.boss_count, Color.BOSS_HP, 6 + self.boss_count * 1.5, "boss", self.player.game_ref.all_sprites, self.player.game_ref.enemy_bullets)

class SkillChest(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)
        self.size = 60
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 215, 0), (5, 5, 50, 50))
        pygame.draw.rect(self.image, Color.WHITE, (5, 5, 50, 50), 3)
        font = pygame.font.SysFont("arial", 24, True)
        txt = font.render("SKILL", True, Color.BG)
        self.image.blit(txt, (self.size//2 - txt.get_width()//2, self.size//2 - txt.get_height()//2))
        self.rect = self.image.get_rect(center=pos)

class Crate(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.size = 50
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, Color.CRATE, (5, 5, 40, 40))
        pygame.draw.rect(self.image, Color.WHITE, (5, 5, 40, 40), 3)
        font = pygame.font.SysFont("arial", 30, True)
        txt = font.render("?", True, Color.WHITE)
        self.image.blit(txt, (self.size//2 - txt.get_width()//2, self.size//2 - txt.get_height()//2))
        self.rect = self.image.get_rect()
        self.rect.center = (random.randint(100, WORLD_WIDTH-100), random.randint(100, WORLD_HEIGHT-100))
        self.hp = 1
        self.base_color = Color.CRATE
    def take_damage(self, amt, bullet=None):
        self.hp -= amt
        return True

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, t, *groups):
        super().__init__(*groups)
        self.type = t
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        c = Color.PLAYER if t == "HP" else Color.MAGNET
        pygame.draw.circle(self.image, c, (15, 15), 12)
        pygame.draw.circle(self.image, Color.WHITE, (15, 15), 12, 2)
        font = pygame.font.SysFont("arial", 20, True)
        icon = "+" if t == "HP" else "M"
        txt = font.render(icon, True, Color.WHITE)
        self.image.blit(txt, (15 - txt.get_width()//2, 15 - txt.get_height()//2))
        self.rect = self.image.get_rect(center=pos)

class ExpOrb(pygame.sprite.Sprite):
    def __init__(self, pos, p, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(self.image, Color.EXP, (6, 6), 5)
        pygame.draw.circle(self.image, Color.WHITE, (6, 6), 2)
        self.rect = self.image.get_rect(center=pos)
        self.magnet_speed = 0
        self.player = p
        self.is_magnetized = False
    def update(self):
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if self.is_magnetized or dist < 150:
            self.magnet_speed = max(self.magnet_speed + 0.5, 8.0 if self.is_magnetized else 0)
            self.rect.x += (dx/dist)*self.magnet_speed
            self.rect.y += (dy/dist)*self.magnet_speed

class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, c, *groups):
        super().__init__(*groups)
        sz = random.randint(2, 5)
        self.image = pygame.Surface((sz, sz))
        self.image.fill(c)
        self.rect = self.image.get_rect(center=pos)
        a = random.uniform(0, math.pi*2)
        spd = random.uniform(2, 4)
        self.vel = [math.cos(a)*spd, math.sin(a)*spd]
        self.life = 20
    def update(self):
        self.rect.x += self.vel[0]
        self.rect.y += self.vel[1]
        self.life -= 1
        if self.life <= 0:
            self.kill()

# ====================== 5. 遊戲引擎 ======================

class GameEngine:
    def __init__(self):
        self.state = "MENU"
        self.all_sprites = pygame.sprite.Group()
        self.bugs = pygame.sprite.Group()
        self.exps = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.crates = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.player = Player(self.all_sprites)
        self.player.game_ref = self
        self.data_source = GitHubDataSource()
        self.font_title = pygame.font.SysFont("microsoft yahei", 60, True)
        self.font_ui = pygame.font.SysFont("microsoft yahei", 24)
        self.spawn_timer = 0
        self.crate_timer = 0
        self.score = 0
        self.game_time = 0
        self.camera_offset = pygame.Vector2(0, 0)
        self.screen_shake = 0
        self.sound = None
        self.player.weapons.append(AutoPatchWeapon(self.player))
        self.boss = None
        self.last_boss_score = 0
        self.boss_defeated_count = 0

    def reset(self):
        self.__init__()
        self.state = "PLAYING"
        self.data_source.fetch_data()
        if self.data_source.connected:
            issue_mod = min(30, self.data_source.stats["issues"] // 10)
            self.base_spawn_rate_mod = issue_mod
            star_bonus = min(100, self.data_source.stats["stars"] // 500)
            self.player.max_hp += star_bonus
            self.player.hp = self.player.max_hp
        else:
            self.base_spawn_rate_mod = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.state == "MENU" and event.key == pygame.K_RETURN:
                    self.reset()
                elif self.state == "LEVEL_UP":
                    idx = -1
                    if event.key == pygame.K_1:
                        idx = 0
                    elif event.key == pygame.K_2:
                        idx = 1
                    elif event.key == pygame.K_3:
                        idx = 2
                    elif event.key == pygame.K_4 and len(self.current_options) >= 4:
                        idx = 3
                    elif event.key == pygame.K_5 and len(self.current_options) >= 5:
                        idx = 4
                    if idx >= 0 and idx < len(self.current_options):
                        self.apply_upgrade(self.current_options[idx])
                elif self.state == "GAMEOVER" and event.key == pygame.K_RETURN:
                    self.reset()
        return True

    def apply_upgrade(self, opt):
        if opt["type"] == "WEAPON":
            existing = next((w for w in self.player.weapons if w.weapon_id == opt["id"]), None)
            if existing:
                existing.level_up()
            else:
                if opt["id"] == "firewall":
                    self.player.weapons.append(FirewallWeapon(self.player))
                elif opt["id"] == "patch":
                    self.player.weapons.append(AutoPatchWeapon(self.player))
                elif opt["id"] == "overclock":
                    self.player.weapons.append(OverclockWeapon(self.player))
                elif opt["id"] == "scanner":
                    self.player.weapons.append(ScannerWeapon(self.player))
        elif opt["type"] == "BUFF":
            self.player.buffs[opt["id"]] += 1
        self.state = "PLAYING"

    def update(self):
        if self.state == "PLAYING":
            self.game_time += 1/60
            if self.screen_shake > 0:
                self.screen_shake -= 1
            self.all_sprites.update()
            self.camera_offset.x = self.player.rect.centerx - SCREEN_WIDTH // 2
            self.camera_offset.y = self.player.rect.centery - SCREEN_HEIGHT // 2
            
            if self.score >= self.last_boss_score + 20000 and not self.boss:
                self.boss = BossBug(self.player, self.boss_defeated_count, self.all_sprites, self.bugs)
                self.last_boss_score = (self.score // 20000) * 20000
                
            # 生成 Bug (受 GitHub 數據影響)
            self.spawn_timer += 1
            # 降低生成加速度 (原本是 /10，改為 /15)
            base_rate = max(15, 50 - int(self.game_time/15) - getattr(self, 'base_spawn_rate_mod', 0))
            if self.spawn_timer > base_rate:
                    self.spawn_timer = 0
                    r = random.random()
                    if r < 0.1 and self.game_time > 30:
                        TankBug(self.player, self.all_sprites, self.bugs)
                    elif r < 0.25 and self.game_time > 15:
                        FastBug(self.player, self.all_sprites, self.bugs)
                    else:
                        Bug(self.player, Color.BUG, (25, 40), 1.0, (1.5, 3.0), self.all_sprites, self.bugs)
            
            self.crate_timer += 1
            if self.crate_timer > 60 * 20:
                self.crate_timer = 0
                Crate(self.all_sprites, self.crates)
                
            for w in self.player.weapons:
                w.update(self.bugs, self.all_sprites, self.bullets)
                
            hits = pygame.sprite.groupcollide(self.bullets, self.bugs, False, False)
            for bullet in hits:
                hit_s = False
                for bug in hits[bullet]:
                    if bug.take_damage(bullet.damage, bullet):
                        hit_s = True
                        if bug.hp <= 0 and bug.alive():
                            self.explode(bug.rect.center, bug.base_color)
                            if self.sound:
                                self.sound.play_explode()
                            if bug == self.boss:
                                SkillChest(bug.rect.center, self.all_sprites, self.items)
                                self.boss = None
                                self.boss_defeated_count += 1
                            else:
                                ExpOrb(bug.rect.center, self.player, self.all_sprites, self.exps)
                            bug.kill()
                            self.score += 150 if isinstance(bug, (TankBug, BossBug)) else 100
                if hit_s and not hasattr(bullet, 'is_piercing'):
                    bullet.kill()
                    
            crate_hits = pygame.sprite.groupcollide(self.bullets, self.crates, True, False)
            for b in crate_hits:
                for crate in crate_hits[b]:
                    crate.hp -= 1
                    if crate.hp <= 0:
                        self.explode(crate.rect.center, Color.CRATE)
                        if self.sound:
                            self.sound.play_explode()
                        PowerUp(crate.rect.center, random.choice(["HP", "MAGNET"]), self.all_sprites, self.items)
                        crate.kill()
                        
            item_collected = pygame.sprite.spritecollide(self.player, self.items, True)
            for item in item_collected:
                if isinstance(item, SkillChest):
                    self.trigger_level_up(is_super=True)
                elif item.type == "HP":
                    self.player.hp = min(self.player.max_hp, self.player.hp + 20)
                    if self.sound:
                        self.sound.play_pickup_hp()
                elif item.type == "MAGNET":
                    for exp in self.exps:
                        exp.is_magnetized = True
                        exp.magnet_speed = 8.0
                    if self.sound:
                        self.sound.play_pickup_magnet()
                    
            collected = pygame.sprite.spritecollide(self.player, self.exps, True)
            for orb in collected:
                self.player.exp += 1
                if self.player.exp >= self.player.max_exp:
                    self.player.level += 1
                    self.player.exp = 0
                    self.player.max_exp = int(self.player.max_exp * 1.4)
                    self.trigger_level_up()
                    if self.sound:
                        self.sound.play_level_up()
                    
            dmg_hits = pygame.sprite.spritecollide(self.player, self.bugs, False)
            bullet_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
            if (dmg_hits or bullet_hits) and self.player.hit_timer == 0:
                self.player.hp -= 10
                self.player.hit_timer = 20
                self.screen_shake = 12
                if self.player.hp <= 0:
                    self.state = "GAMEOVER"
                    
            if self.player.firewall_active:
                fw = next((w for w in self.player.weapons if w.weapon_id == "firewall"), None)
                fw_dmg = fw.damage if fw else 0.15
                for bug in self.bugs:
                    if abs(bug.rect.centerx - self.player.rect.centerx) < 150 and abs(bug.rect.centery - self.player.rect.centery) < 150:
                        dist = math.hypot(bug.rect.centerx - self.player.rect.centerx, bug.rect.centery - self.player.rect.centery)
                        if 80 < dist < 120:
                            if bug.take_damage(fw_dmg):
                                if bug.hp <= 0 and bug.alive():
                                    self.explode(bug.rect.center, Color.PATCH)
                                    if bug == self.boss:
                                        SkillChest(bug.rect.center, self.all_sprites, self.items)
                                        self.boss = None
                                        self.boss_defeated_count += 1
                                    else:
                                        ExpOrb(bug.rect.center, self.player, self.all_sprites, self.exps)
                                    bug.kill()
                                    self.score += 100
                for crate in self.crates:
                    dist = math.hypot(crate.rect.centerx - self.player.rect.centerx, crate.rect.centery - self.player.rect.centery)
                    if 80 < dist < 120:
                        crate.kill()
                        self.explode(crate.rect.center, Color.CRATE)
                        PowerUp(crate.rect.center, random.choice(["HP", "MAGNET"]), self.all_sprites, self.items)

    def trigger_level_up(self, is_super=False):
        self.state = "LEVEL_UP"
        available = []
        for opt in self.data_source.data:
            if opt["type"] == "WEAPON":
                w = next((x for x in self.player.weapons if x.weapon_id == opt["id"]), None)
                if w and w.level >= 5:
                    continue
            elif opt["type"] == "BUFF":
                if self.player.buffs.get(opt["id"], 0) >= 5:
                    continue
            available.append(opt)
        count = 5 if is_super else 3
        if len(available) >= count:
            self.current_options = random.sample(available, count)
        elif available:
            self.current_options = available
        else:
            self.state = "PLAYING"

    def explode(self, pos, color):
        if len(self.particles) < 100:
            for _ in range(5):
                Particle(pos, color, self.all_sprites, self.particles)

    def draw(self):
        screen.fill(Color.BG)
        shake = pygame.Vector2(0,0)
        if self.screen_shake > 0:
            shake.x = random.randint(-self.screen_shake, self.screen_shake)
            shake.y = random.randint(-self.screen_shake, self.screen_shake)
        draw_off = self.camera_offset + shake
        gsx = -int(draw_off.x) % 100
        gsy = -int(draw_off.y) % 100
        for x in range(gsx, SCREEN_WIDTH, 100):
            pygame.draw.line(screen, Color.GRID, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(gsy, SCREEN_HEIGHT, 100):
            pygame.draw.line(screen, Color.GRID, (0, y), (SCREEN_WIDTH, y))
            
        by_top = 0 - draw_off.y
        if -50 < by_top < SCREEN_HEIGHT + 50:
            pygame.draw.line(screen, Color.BORDER, (0-draw_off.x, by_top), (WORLD_WIDTH-draw_off.x, by_top), 5)
        by_bot = WORLD_HEIGHT - draw_off.y
        if -50 < by_bot < SCREEN_HEIGHT + 50:
            pygame.draw.line(screen, Color.BORDER, (0-draw_off.x, by_bot), (WORLD_WIDTH-draw_off.x, by_bot), 5)
        bx_l = 0 - draw_off.x
        if -50 < bx_l < SCREEN_WIDTH + 50:
            pygame.draw.line(screen, Color.BORDER, (bx_l, 0-draw_off.y), (bx_l, WORLD_HEIGHT-draw_off.y), 5)
        bx_r = WORLD_WIDTH - draw_off.x
        if -50 < bx_r < SCREEN_WIDTH + 50:
            pygame.draw.line(screen, Color.BORDER, (bx_r, 0-draw_off.y), (bx_r, WORLD_HEIGHT-draw_off.y), 5)
            
        if self.state in ["PLAYING", "LEVEL_UP"]:
            cam_rect = pygame.Rect(draw_off.x - 50, draw_off.y - 50, SCREEN_WIDTH + 100, SCREEN_HEIGHT + 100)
            for sprite in self.all_sprites:
                if cam_rect.colliderect(sprite.rect):
                    screen.blit(sprite.image, sprite.rect.topleft - draw_off)
            if self.player.firewall_active:
                for i in range(3):
                    a = self.player.firewall_angle + (i * math.pi * 2 / 3)
                    px = self.player.rect.centerx + math.cos(a)*100 - draw_off.x
                    py = self.player.rect.centery + math.sin(a)*100 - draw_off.y
                    pygame.draw.circle(screen, Color.PATCH, (int(px), int(py)), 15)
                    pygame.draw.circle(screen, Color.WHITE, (int(px), int(py)), 15, 2)
            
            pygame.draw.rect(screen, (50, 50, 50), (20, SCREEN_HEIGHT-40, 200, 20))
            hp_w = max(0, int(200*(self.player.hp/self.player.max_hp)))
            pygame.draw.rect(screen, Color.BUG if self.player.hp<30 else Color.PLAYER, (20, SCREEN_HEIGHT-40, hp_w, 20))
            exp_w = int(SCREEN_WIDTH * (self.player.exp/self.player.max_exp))
            pygame.draw.rect(screen, Color.EXP, (0,0,exp_w, 8))
            info = f"UPTIME: {int(self.game_time)}s | VER: {self.player.level}.0 | SCORE: {self.score}"
            screen.blit(self.font_ui.render(info, True, Color.UI_TEXT), (20, 20))
            
            if self.boss and self.boss.alive():
                bw, bh = 600, 25
                bx, by = SCREEN_WIDTH//2-bw//2, 70
                pygame.draw.rect(screen, (50,50,50), (bx, by, bw, bh))
                ratio = max(0, self.boss.hp / self.boss.max_hp)
                pygame.draw.rect(screen, Color.BOSS_HP, (bx, by, int(bw*ratio), bh))
                pygame.draw.rect(screen, Color.WHITE, (bx, by, bw, bh), 2)
                name_t = self.font_ui.render(self.boss.name, True, Color.WHITE)
                screen.blit(name_t, (SCREEN_WIDTH//2-name_t.get_width()//2, by-35))
                
        if self.state == "MENU":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,200))
            screen.blit(overlay, (0,0))
            t = self.font_title.render("代碼保衛戰 (Code Defender)", True, Color.PLAYER)
            h = self.font_ui.render("按下 ENTER 鍵 啟動系統防禦週期", True, Color.WHITE)
            
            ctrl_font = pygame.font.SysFont("microsoft yahei", 20)
            c1 = ctrl_font.render("移動: WASD / 方向鍵", True, (180, 180, 180))
            c2 = ctrl_font.render("衝刺: 空白鍵 (SPACE)", True, (180, 180, 180))
            
            screen.blit(t, (SCREEN_WIDTH//2 - t.get_width()//2, SCREEN_HEIGHT//2 - 100))
            screen.blit(h, (SCREEN_WIDTH//2 - h.get_width()//2, SCREEN_HEIGHT//2 - 10))
            screen.blit(c1, (SCREEN_WIDTH//2 - c1.get_width()//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(c2, (SCREEN_WIDTH//2 - c2.get_width()//2, SCREEN_HEIGHT//2 + 85))
            
            sc = (100,255,100) if self.data_source.connected else (150,150,150)
            status = f"數據同步庫: {self.data_source.stats['name']} | Issues: {self.data_source.stats['issues']}"
            s = self.font_ui.render(status, True, sc)
            screen.blit(s, (SCREEN_WIDTH//2-s.get_width()//2, SCREEN_HEIGHT-60))
            
        elif self.state == "LEVEL_UP":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((5,10,30,220))
            screen.blit(overlay, (0,0))
            title_text = "系統升級：選擇補丁封裝" if len(self.current_options) <= 3 else "!! 高階權限：選擇核心強化 !!"
            title = self.font_title.render(title_text, True, Color.PATCH if len(self.current_options) <= 3 else (255, 215, 0))
            screen.blit(title, (SCREEN_WIDTH//2-title.get_width()//2, 60))
            for i, opt in enumerate(self.current_options):
                box_h = 90
                box_y = 180 + i * (box_h + 15)
                pygame.draw.rect(screen, (20, 30, 50), (SCREEN_WIDTH//2-300, box_y, 600, box_h))
                color = Color.PATCH if len(self.current_options) <= 3 else (255,215,0)
                pygame.draw.rect(screen, color, (SCREEN_WIDTH//2-300, box_y, 600, box_h), 2)
                lvl_str = ""
                if opt["type"] == "WEAPON":
                    w = next((x for x in self.player.weapons if x.weapon_id == opt["id"]), None)
                    lvl_str = f" (升級 Lv.{w.level + 1})" if w else " (新安裝)"
                elif opt["type"] == "BUFF":
                    lvl_str = f" (Lv.{self.player.buffs[opt['id']] + 1})"
                name = self.font_ui.render(f"[{i+1}] {opt['name']}{lvl_str}", True, color)
                desc = self.font_ui.render(opt['desc'], True, (180, 200, 220))
                screen.blit(name, (SCREEN_WIDTH//2-280, box_y+10))
                screen.blit(desc, (SCREEN_WIDTH//2-280, box_y+45))
                
        elif self.state == "GAMEOVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((40,0,0,220))
            screen.blit(overlay, (0,0))
            t = self.font_title.render("系統崩潰 (SYSTEM CRASH)", True, Color.BUG)
            h = self.font_ui.render(f"維護績效: {self.score} | 按下 ENTER 重試", True, Color.WHITE)
            screen.blit(t, (SCREEN_WIDTH//2-t.get_width()//2, SCREEN_HEIGHT//2-60))
            screen.blit(h, (SCREEN_WIDTH//2-h.get_width()//2, SCREEN_HEIGHT//2+40))
        pygame.display.flip()

if __name__ == "__main__":
    try:
        sound = SoundManager()
        sound.play_bgm()
        game = GameEngine()
        while game.handle_events():
            game.sound = sound
            game.update()
            game.draw()
            clock.tick(FPS)
    finally:
        pygame.quit()
        sys.exit()
