import pygame
import sys
import os
import random
import math
import shutil
import heapq

# ====================== 1. 系統配置與初始化 ======================
pygame.init()
pygame.mixer.init()

try:
    pygame.key.stop_text_input()
except:
    pass

WIDTH, HEIGHT = 1000, 800
FPS = 60
GRID_SIZE = 40

class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (200, 0, 0)
    YELLOW = (255, 255, 0)      # 金鑰匙
    CYAN = (0, 255, 255)        # 銀鑰匙
    BLUE = (0, 100, 255)        # 鎖住的門
    GREEN = (0, 200, 0)
    BROWN = (139, 69, 19)
    GRAY = (50, 50, 50)
    STAMINA = (0, 200, 255)
    CABINET = (60, 40, 20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("屋影：多重噩夢 - Multi-Room Horror")
clock = pygame.time.Clock()

# ====================== 2. 資產管理 ======================
TARGET_SND_DIR = "遊戲資產/snd"

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.load_sounds()
        self.current_bgm = None
        self.walk_channel = pygame.mixer.Channel(1)
        self.run_channel = pygame.mixer.Channel(2)
        
    def load_sounds(self):
        if not os.path.exists(TARGET_SND_DIR): return
        for file in os.listdir(TARGET_SND_DIR):
            name = os.path.splitext(file)[0]
            path = os.path.join(TARGET_SND_DIR, file)
            try:
                if file.endswith(".mp3") or file.endswith(".wav"):
                    self.sounds[name] = pygame.mixer.Sound(path)
            except: pass

    def play_bgm(self, name, loop=-1):
        if self.current_bgm == name: return
        pygame.mixer.music.stop()
        path = os.path.join(TARGET_SND_DIR, f"{name}.mp3")
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loop)
            self.current_bgm = name

    def play_sfx(self, name):
        if name in self.sounds: self.sounds[name].play()

    def stop_bgm(self):
        pygame.mixer.music.stop()
        self.current_bgm = None

    def stop_movement_sounds(self):
        self.walk_channel.stop()
        self.run_channel.stop()

sound_manager = SoundManager()

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
    TITLE = FontManager.get_font(64, True)
    UI = FontManager.get_font(24)
    SMALL = FontManager.get_font(18)

# ====================== 3. 遊戲實體 ======================

class Pathfinder:
    def __init__(self, width, height, grid_size):
        self.grid_size = grid_size
        self.cols = width // grid_size
        self.rows = height // grid_size
        self.grid = [] # 0: walkable, 1: blocked

    def update_grid(self, walls):
        self.grid = [[0 for _ in range(self.rows)] for _ in range(self.cols)]
        for wall in walls:
            start_x = max(0, (wall.rect.left - 10) // self.grid_size)
            end_x = min(self.cols, ((wall.rect.right + 10) // self.grid_size) + 1)
            start_y = max(0, (wall.rect.top - 10) // self.grid_size)
            end_y = min(self.rows, ((wall.rect.bottom + 10) // self.grid_size) + 1)
            for x in range(start_x, end_x):
                for y in range(start_y, end_y):
                    self.grid[x][y] = 1

    def get_path(self, start_pos, end_pos):
        start = (int(start_pos[0] // self.grid_size), int(start_pos[1] // self.grid_size))
        end = (int(end_pos[0] // self.grid_size), int(end_pos[1] // self.grid_size))
        
        start = (max(0, min(self.cols-1, start[0])), max(0, min(self.rows-1, start[1])))
        end = (max(0, min(self.cols-1, end[0])), max(0, min(self.rows-1, end[1])))

        if self.grid[start[0]][start[1]] == 1:
            return [] 

        if self.grid[end[0]][end[1]] == 1:
            found = False
            for r in range(1, 4):
                for dx in range(-r, r+1):
                    for dy in range(-r, r+1):
                        nx, ny = end[0]+dx, end[1]+dy
                        if 0<=nx<self.cols and 0<=ny<self.rows and self.grid[nx][ny] == 0:
                            end = (nx, ny)
                            found = True; break
                    if found: break
                if found: break

        queue = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}

        while queue:
            current_priority, current = heapq.heappop(queue)
            if current == end: break

            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.cols and 0 <= neighbor[1] < self.rows:
                    if self.grid[neighbor[0]][neighbor[1]] == 1: continue
                    new_cost = cost_so_far[current] + (1.414 if dx!=0 and dy!=0 else 1)
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        priority = new_cost + math.hypot(end[0]-neighbor[0], end[1]-neighbor[1])
                        heapq.heappush(queue, (priority, neighbor))
                        came_from[neighbor] = current
        
        if end not in came_from: return []
        path = []
        curr = end
        while curr != start:
            path.append((curr[0] * self.grid_size + self.grid_size//2, curr[1] * self.grid_size + self.grid_size//2))
            curr = came_from[curr]
        path.reverse()
        return path

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.animations = {"left": [], "right": [], "idle": []}
        self.load_animations()
        self.facing = "right"
        self.frame_index = 0
        self.animation_speed = 0.2
        if self.animations["idle"]:
            self.image = self.animations["idle"][0]
        elif self.animations["right"]:
            self.image = self.animations["right"][0]
        else:
            self.image = pygame.Surface((30, 30))
            self.image.fill(Color.GREEN)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_walk = 3
        self.speed_run = 6
        self.stamina = 100
        self.is_running = False
        self.is_crouching = False
        self.is_hiding = False
        self.has_silver_key = False
        self.has_gold_key = False
        self.moving = False

    def load_animations(self):
        base_path = "遊戲資產/img"
        for direction in ["left", "right", "idle"]:
            dir_path = os.path.join(base_path, f"player_{direction}")
            if os.path.exists(dir_path):
                files = sorted([f for f in os.listdir(dir_path) if f.endswith(".png")])
                for file in files:
                    try:
                        img = pygame.image.load(os.path.join(dir_path, file)).convert_alpha()
                        # 放大角色尺寸，同時保持比例 (原始約 40x60 -> 60x90)
                        img = pygame.transform.scale(img, (60, 90))
                        self.animations[direction].append(img)
                    except: pass

    def update(self, keys, walls, cabinets):
        if self.is_hiding:
            self.moving = False
            sound_manager.stop_movement_sounds()
            return
        self.moving = False
        self.is_running = keys[pygame.K_LSHIFT] and self.stamina > 0
        self.is_crouching = keys[pygame.K_LCTRL]
        current_speed = self.speed_walk
        if self.is_running:
            current_speed = self.speed_run
            self.stamina -= 0.6
        elif self.is_crouching:
            current_speed = 1.5
            self.stamina = min(100, self.stamina + 0.1)
        else:
            self.stamina = min(100, self.stamina + 0.2)
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= current_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += current_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: 
            dx -= current_speed
            self.facing = "left"
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: 
            dx += current_speed
            self.facing = "right"
        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dx > 0: self.rect.right = wall.rect.left
                if dx < 0: self.rect.left = wall.rect.right
        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dy > 0: self.rect.bottom = wall.rect.top
                if dy < 0: self.rect.top = wall.rect.bottom
        if dx != 0 or dy != 0: 
            self.moving = True
            self.frame_index += self.animation_speed
            anim = self.animations[self.facing]
            if not anim: anim = self.animations["idle"]
            if anim:
                if self.frame_index >= len(anim):
                    self.frame_index = 0
                self.image = anim[int(self.frame_index)]
        else:
            if self.animations["idle"]:
                self.frame_index += 0.1
                if self.frame_index >= len(self.animations["idle"]):
                    self.frame_index = 0
                self.image = self.animations["idle"][int(self.frame_index)]
            elif self.animations[self.facing]:
                self.image = self.animations[self.facing][0]
        self.handle_sounds()

    def handle_sounds(self):
        if self.moving:
            if self.is_running:
                if not sound_manager.run_channel.get_busy():
                    sound_manager.run_channel.play(sound_manager.sounds["跑步"], -1)
                sound_manager.walk_channel.stop()
            elif not self.is_crouching:
                if not sound_manager.walk_channel.get_busy():
                    sound_manager.walk_channel.play(sound_manager.sounds["走路"], -1)
                sound_manager.run_channel.stop()
            else:
                sound_manager.stop_movement_sounds()
        else:
            sound_manager.stop_movement_sounds()

class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, room_id):
        super().__init__()
        self.image_orig = None
        try:
            self.image_orig = pygame.image.load("遊戲資產/img/ghost.png").convert_alpha()
            # 放大怪物尺寸 (50x50 -> 80x80)
            self.image_orig = pygame.transform.scale(self.image_orig, (80, 80))
            self.image = self.image_orig
        except:
            self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(self.image, Color.RED, (30, 30), 30)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_chase = 4.2
        self.speed_wander = 2.0
        self.current_room = room_id
        self.state = "WANDER"
        self.target_pos = [x, y]
        self.wander_timer = 0
        self.room_transition_timer = 0
        self.path = []
        self.path_update_timer = 0

    def update(self, player, walls, current_room_id, transitions, pathfinder):
        if self.current_room != current_room_id:
            self.state = "TRANSITION"
            for trans in transitions:
                if trans.target_room == current_room_id:
                    self.target_pos = trans.rect.center
                    break
            dist_to_door = math.hypot(self.target_pos[0] - self.rect.centerx, self.target_pos[1] - self.rect.centery)
            if dist_to_door < 10:
                self.room_transition_timer += 1
                if self.room_transition_timer > 60:
                    self.current_room = current_room_id
                    self.room_transition_timer = 0
        else:
            dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
            can_see = not player.is_hiding
            detection_range = 300
            if player.is_running: detection_range = 500
            if player.is_crouching: detection_range = 150
            is_making_noise = player.moving and not player.is_crouching
            sound_range = 400
            
            if can_see and (dist < detection_range or (is_making_noise and dist < sound_range)):
                self.state = "CHASE"
                self.speed = self.speed_chase
                self.path_update_timer -= 1
                if self.path_update_timer <= 0:
                    self.path = pathfinder.get_path(self.rect.center, player.rect.center)
                    self.path_update_timer = 20
                if self.path:
                    self.target_pos = self.path[0]
                    if math.hypot(self.target_pos[0] - self.rect.centerx, self.target_pos[1] - self.rect.centery) < 20:
                        self.path.pop(0)
                else:
                    self.target_pos = list(player.rect.center)
            else:
                if self.state == "CHASE":
                    self.state = "WANDER"
                    self.path = []
                self.speed = self.speed_wander
                self.wander_timer -= 1
                if self.wander_timer <= 0:
                    self.target_pos = [random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100)]
                    self.wander_timer = random.randint(150, 400)

        tx, ty = self.target_pos
        dx, dy = tx - self.rect.centerx, ty - self.rect.centery
        dist_to_target = math.hypot(dx, dy)
        if dist_to_target > 2:
            angle = math.atan2(dy, dx)
            if self.image_orig:
                if dx > 0: self.image = self.image_orig
                else: self.image = pygame.transform.flip(self.image_orig, True, False)
            
            mv_x, mv_y = math.cos(angle) * self.speed, math.sin(angle) * self.speed
            self.rect.x += mv_x
            for wall in walls:
                if self.rect.colliderect(wall.rect):
                    if mv_x > 0: self.rect.right = wall.rect.left
                    if mv_x < 0: self.rect.left = wall.rect.right
            self.rect.y += mv_y
            for wall in walls:
                if self.rect.colliderect(wall.rect):
                    if mv_y > 0: self.rect.bottom = wall.rect.top
                    if mv_y < 0: self.rect.top = wall.rect.bottom

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color=Color.GRAY):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

class Transition(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, target_room, spawn_pos):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((100, 100, 255, 100))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.target_room = target_room
        self.spawn_pos = spawn_pos

class Cabinet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.img_closed = None
        self.img_open = None
        try:
            self.img_closed = pygame.image.load("遊戲資產/img/cabinet_closed.png").convert_alpha()
            self.img_closed = pygame.transform.scale(self.img_closed, (80, 110))
            self.img_open = pygame.image.load("遊戲資產/img/cabinet_open.png").convert_alpha()
            self.img_open = pygame.transform.scale(self.img_open, (80, 110))
        except: pass
        
        if self.img_closed:
            self.image = self.img_closed
        else:
            self.image = pygame.Surface((60, 90))
            self.image.fill(Color.CABINET)
            pygame.draw.rect(self.image, Color.BLACK, (5, 5, 50, 80), 2)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_open = False

    def toggle(self, opening):
        self.is_open = opening
        if self.img_open and self.img_closed:
            self.image = self.img_open if self.is_open else self.img_closed

# ====================== 4. 遊戲核心 ======================

class Game:
    def __init__(self):
        self.state = "MENU"
        self.current_room_id = "HALL"
        self.player = Player(WIDTH//2, HEIGHT//2)
        self.ghost = Ghost(100, 100, "BASEMENT")
        self.pathfinder = Pathfinder(WIDTH, HEIGHT, GRID_SIZE)
        
        self.floor_img = None
        self.exit_img = None
        try:
            path = "遊戲資產/img/floor.jpg"
            if os.path.exists(path):
                self.floor_img = pygame.image.load(path).convert()
                self.floor_img = pygame.transform.scale(self.floor_img, (128, 128))
            
            path_exit = "遊戲資產/img/exit.png"
            if os.path.exists(path_exit):
                self.exit_img = pygame.image.load(path_exit).convert_alpha()
                # 放大出口尺寸 (60x60 -> 100x100)
                self.exit_img = pygame.transform.scale(self.exit_img, (100, 100))
        except: pass

        self.rooms = {
            "HALL": {
                "walls": [
                    Wall(0,0,WIDTH,20), Wall(0,HEIGHT-20,WIDTH,20),
                    Wall(0,0,20,HEIGHT), Wall(WIDTH-20,0,20,HEIGHT),
                    Wall(300, 200, 400, 20), Wall(500, 400, 20, 300)
                ],
                "transitions": [
                    Transition(WIDTH-40, 400, 40, 100, "BASEMENT", (100, 450)),
                    Transition(400, 0, 100, 40, "KITCHEN", (450, HEIGHT-120))
                ],
                "cabinets": [Cabinet(100, 100), Cabinet(800, 700)],
                "items": [("EXIT", 100, 700)]
            },
            "BASEMENT": {
                "walls": [
                    Wall(0,0,WIDTH,20), Wall(0,HEIGHT-20,WIDTH,20),
                    Wall(0,0,20,HEIGHT), Wall(WIDTH-20,0,20,HEIGHT),
                    Wall(100, 100, 20, 600), Wall(100, 100, 800, 20)
                ],
                "transitions": [
                    Transition(0, 400, 40, 100, "HALL", (WIDTH-100, 450))
                ],
                "cabinets": [Cabinet(500, 500)],
                "items": [("SILVER_KEY", 800, 600)]
            },
            "KITCHEN": {
                "walls": [
                    Wall(0,0,WIDTH,20), Wall(0,HEIGHT-20,WIDTH,20),
                    Wall(0,0,20,HEIGHT), Wall(WIDTH-20,0,20,HEIGHT),
                    Wall(200, 200, 600, 20)
                ],
                "transitions": [
                    Transition(400, HEIGHT-40, 100, 40, "HALL", (450, 120))
                ],
                "cabinets": [Cabinet(200, 600)],
                "items": [("GOLD_KEY_GATE", 800, 100)]
            }
        }
        self.pathfinder.update_grid(self.rooms[self.current_room_id]["walls"])

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if self.state == "MENU":
                    if event.key == pygame.K_RETURN:
                        self.state = "PLAYING"
                        sound_manager.play_bgm("過程")
                elif self.state in ["GAMEOVER", "WIN"]:
                    if event.key == pygame.K_RETURN: self.__init__()
                elif self.state == "PLAYING":
                    if event.key == pygame.K_e or event.key == pygame.K_SPACE:
                        if self.player.is_hiding:
                            self.player.is_hiding = False
                            sound_manager.play_sfx("關開鐵櫃")
                            for cab in self.rooms[self.current_room_id]["cabinets"]:
                                if self.player.rect.colliderect(cab.rect):
                                    cab.toggle(False)
                                    break
                        else:
                            for cab in self.rooms[self.current_room_id]["cabinets"]:
                                if self.player.rect.colliderect(cab.rect):
                                    self.player.is_hiding = True
                                    self.player.rect.center = cab.rect.center
                                    cab.toggle(True)
                                    sound_manager.play_sfx("關開鐵櫃")
                                    break
        return True

    def update(self):
        if self.state != "PLAYING": return
        room = self.rooms[self.current_room_id]
        self.player.update(pygame.key.get_pressed(), room["walls"], room["cabinets"])
        self.ghost.update(self.player, room["walls"], self.current_room_id, room["transitions"], self.pathfinder)
        if not self.player.is_hiding:
            for trans in room["transitions"]:
                if self.player.rect.colliderect(trans.rect):
                    self.current_room_id = trans.target_room
                    self.player.rect.center = trans.spawn_pos
                    self.pathfinder.update_grid(self.rooms[self.current_room_id]["walls"])
                    sound_manager.play_sfx("走路")
                    break
        for item in room["items"][:]:
            name, x, y = item
            # 擴大判定範圍 (40x40 -> 60x60)
            if self.player.rect.colliderect(pygame.Rect(x-30, y-30, 60, 60)):
                if name == "SILVER_KEY":
                    self.player.has_silver_key = True
                    room["items"].remove(item)
                    sound_manager.play_sfx("拿鑰匙")
                elif name == "GOLD_KEY_GATE":
                    if self.player.has_silver_key:
                        self.player.has_gold_key = True
                        room["items"].remove(item)
                        sound_manager.play_sfx("拿鑰匙")
                elif name == "EXIT":
                    if self.player.has_gold_key:
                        self.state = "WIN"
                        sound_manager.stop_movement_sounds()
                        sound_manager.play_bgm("結束")
        if self.current_room_id == self.ghost.current_room and not self.player.is_hiding:
            if self.player.rect.colliderect(self.ghost.rect):
                self.state = "GAMEOVER"
                sound_manager.stop_bgm()
                sound_manager.stop_movement_sounds()
                sound_manager.play_sfx("被抓到")
                pygame.time.delay(500)
                sound_manager.play_bgm("結束")
        if self.current_room_id == self.ghost.current_room and self.ghost.state == "CHASE":
            sound_manager.play_bgm("被鬼追")
        else:
            sound_manager.play_bgm("過程")

    def draw(self):
        if self.state == "PLAYING" and self.floor_img:
            for x in range(0, WIDTH, 128):
                for y in range(0, HEIGHT, 128):
                    screen.blit(self.floor_img, (x, y))
        else:
            screen.fill(Color.BLACK)

        if self.state == "MENU":
            sound_manager.play_bgm("開頭")
            t = Fonts.TITLE.render("屋影：多重噩夢", True, Color.RED)
            h = Fonts.UI.render("按下 Enter 開始逃生", True, Color.WHITE)
            screen.blit(t, (WIDTH//2 - t.get_width()//2, 200))
            screen.blit(h, (WIDTH//2 - h.get_width()//2, 350))
            c = ["WASD: 移動", "Shift: 奔跑", "Ctrl: 蹲下", "Space/E: 躲進櫃子", "目標: 找齊兩把鑰匙逃離"]
            for i, txt in enumerate(c):
                s = Fonts.SMALL.render(txt, True, Color.GRAY)
                screen.blit(s, (WIDTH//2 - s.get_width()//2, 450 + i*25))
        elif self.state == "PLAYING":
            room = self.rooms[self.current_room_id]
            for w in room["walls"]: pygame.draw.rect(screen, Color.GRAY, w.rect)
            for t in room["transitions"]: pygame.draw.rect(screen, (30, 30, 50), t.rect)
            for c in room["cabinets"]: screen.blit(c.image, c.rect)
            for item in room["items"]:
                name, x, y = item
                if name == "EXIT" and self.exit_img:
                    screen.blit(self.exit_img, (x-50, y-50))
                else:
                    color = Color.CYAN if name == "SILVER_KEY" else Color.YELLOW
                    # 放大鑰匙圖案 (10 -> 15)
                    pygame.draw.circle(screen, color, (x, y), 15)
            if not self.player.is_hiding:
                draw_pos = self.player.image.get_rect(midbottom=self.player.rect.midbottom)
                screen.blit(self.player.image, draw_pos)
            if self.ghost.current_room == self.current_room_id:
                screen.blit(self.ghost.image, self.ghost.rect)
            mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 180)) 
            rad = 180 if self.player.is_running else 120
            if not self.player.is_hiding:
                pygame.draw.circle(mask, (0, 0, 0, 0), self.player.rect.center, rad)
                pygame.draw.circle(mask, (0, 0, 0, 80), self.player.rect.center, rad + 40)
            screen.blit(mask, (0, 0))
            pygame.draw.rect(screen, Color.STAMINA, (20, 20, self.player.stamina*2, 10))
            txt = f"目前房間: {self.current_room_id}"
            if self.player.has_silver_key: txt += " | 已持銀鑰"
            if self.player.has_gold_key: txt += " | 已持金鑰"
            if self.player.is_hiding: txt += " [躲藏中]"
            screen.blit(Fonts.SMALL.render(txt, True, Color.WHITE), (20, 40))
        elif self.state == "GAMEOVER":
            t = Fonts.TITLE.render("你逃不掉的...", True, Color.RED)
            screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 50))
            screen.blit(Fonts.UI.render("按下 Enter 重試", True, Color.WHITE), (WIDTH//2 - 100, HEIGHT//2 + 50))
        elif self.state == "WIN":
            t = Fonts.TITLE.render("你活下來了！", True, Color.GREEN)
            screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 50))
        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    while game.handle_events():
        game.update()
        game.draw()
        clock.tick(FPS)
    pygame.quit()
