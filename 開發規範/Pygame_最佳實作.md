# Guideline: Pygame 高階架構最佳實務

## 1. 狀態機架構 (State-Driven Architecture)
遊戲必須使用有限狀態機 (FSM) 來管理。
- **狀態劃分**: `MENU`, `PLAYING`, `PAUSED`, `GAMEOVER`。
- **邏輯解耦**: 每個狀態應有獨立的 `handle_events`, `update`, `draw` 方法。

## 2. 物件導向精靈管理 (Advanced Sprite Management)
- **組合優於繼承**: 善用 Pygame 的 `Sprite.Group` 機制進行批次渲染與碰撞檢測。
- **碰撞優化**: 對於非規則形狀，應優先使用 `pygame.sprite.collide_mask` 或圓形碰撞 `collide_circle` 提升精準度。

## 3. 事件解耦系統 (Event Decoupling)
- **按鍵狀態緩存**: 區分「瞬時按鍵」（KeyDown）與「持續按鍵」（get_pressed）。
- **廣播機制**: 重要遊戲事件（如玩家受傷、過關）應透過自定義事件 `pygame.USEREVENT` 進行廣播。

## 5. 防禦性常數管理 (Defensive Constant Management)
- **結構化配置**: 避免使用原始字典儲存核心配置。建議使用類別屬性（Class Attributes）或 `Enum`，這能在開發階段就透過靜態分析捕捉到名稱錯誤。
- **配置校驗**: 在遊戲初始化階段，應實施「配置完整性自檢」，確保所有 UI 調用的顏色或字型資源皆已就緒。
