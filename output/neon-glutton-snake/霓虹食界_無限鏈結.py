import pygame
import sys
import random
import os

# ====================== 遊戲總監：藝術命名 ======================
# 遊戲名稱：霓虹食界：無限鏈結 (Neon Glutton: Infinite Link)
# 願景：在充滿電子感的高速空間中，不斷吞噬能量塊以維持鏈結穩定。

# ====================== 初始化 ======================
pygame.init()
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("霓虹食界：無限鏈結")
CLOCK = pygame.time.Clock()

# 顏色定義
BG_COLOR = (10, 10, 15)      # 深電子紫
SNAKE_COLOR = (0, 255, 127)  # 春之綠 (霓虹感)
FOOD_COLOR = (255, 50, 50)   # 亮紅
TEXT_COLOR = (200, 200, 255) # 淡藍白

# 字型設定
try:
    FONT = pygame.font.SysFont("microsoft yahei", 30)
except:
    FONT = pygame.font.SysFont(None, 30)

class SnakeGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.snake = [(WIDTH // 2, HEIGHT // 2)]
        self.direction = random.choice([(GRID_SIZE, 0), (-GRID_SIZE, 0), (0, GRID_SIZE), (0, -GRID_SIZE)])
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False

    def spawn_food(self):
        while True:
            food_pos = (random.randint(0, (WIDTH - GRID_SIZE) // GRID_SIZE) * GRID_SIZE,
                        random.randint(0, (HEIGHT - GRID_SIZE) // GRID_SIZE) * GRID_SIZE)
            if food_pos not in self.snake:
                return food_pos

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset()
                else:
                    if event.key == pygame.K_UP and self.direction != (0, GRID_SIZE):
                        self.direction = (0, -GRID_SIZE)
                    elif event.key == pygame.K_DOWN and self.direction != (0, -GRID_SIZE):
                        self.direction = (0, GRID_SIZE)
                    elif event.key == pygame.K_LEFT and self.direction != (GRID_SIZE, 0):
                        self.direction = (-GRID_SIZE, 0)
                    elif event.key == pygame.K_RIGHT and self.direction != (-GRID_SIZE, 0):
                        self.direction = (GRID_SIZE, 0)

    def update(self):
        if self.game_over:
            return

        new_head = (self.snake[0][0] + self.direction[0], self.snake[0][1] + self.direction[1])

        # 碰撞邊界或自己
        if (new_head[0] < 0 or new_head[0] >= WIDTH or
            new_head[1] < 0 or new_head[1] >= HEIGHT or
            new_head in self.snake):
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        # 吃到食物
        if new_head == self.food:
            self.score += 10
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def draw(self):
        SCREEN.fill(BG_COLOR)
        
        # 畫食物
        pygame.draw.rect(SCREEN, FOOD_COLOR, (*self.food, GRID_SIZE - 2, GRID_SIZE - 2))

        # 畫蛇
        for i, (x, y) in enumerate(self.snake):
            color = SNAKE_COLOR if i == 0 else (0, 200, 100)
            pygame.draw.rect(SCREEN, color, (x, y, GRID_SIZE - 2, GRID_SIZE - 2))

        # 顯示分數
        score_surface = FONT.render(f"能量點: {self.score}", True, TEXT_COLOR)
        SCREEN.blit(score_surface, (10, 10))

        if self.game_over:
            over_surface = FONT.render("系統崩潰！按 R 重啟鏈結", True, FOOD_COLOR)
            rect = over_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            SCREEN.blit(over_surface, rect)

        pygame.display.flip()

def main():
    game = SnakeGame()
    while True:
        game.handle_input()
        game.update()
        game.draw()
        CLOCK.tick(15)

if __name__ == "__main__":
    main()
