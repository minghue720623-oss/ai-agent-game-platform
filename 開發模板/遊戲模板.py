import pygame
import sys
import os

# ====================== 自動建立資產資料夾 ======================
for folder in ["assets/img", "assets/snd", "assets/fonts"]:
    os.makedirs(folder, exist_ok=True)

# ====================== 初始化 ======================
pygame.init()
pygame.display.set_caption("遊戲名稱")
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# ====================== 字型設定（中文支援） ======================
font_size = 36
try:
    font = pygame.font.SysFont("microsoft yahei", font_size)
except:
    try:
        font = pygame.font.SysFont("simhei", font_size)
    except:
        font = pygame.font.SysFont(None, font_size)

# ====================== 遊戲變數 ======================
running = True

# ====================== 主迴圈 ======================
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 填滿背景
    screen.fill((30, 30, 40))

    # 在這裡撰寫你的遊戲內容...

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()