# 錯誤診斷紀錄 (ERROR_TRACKING.md)

本文件用於自動化追蹤開發與執行過程中的錯誤與異常。

| 日期 | 問題類型 | 錯誤現象 | 重現條件 | 修正方案 | 預防措施 |
| 2026-05-28 | Documentation | README 結構不一致 | 發布檢查 | 更新 README 以符合 PixelForge 標準專案結構 | 強制執行標準化 README 模板以確保各專案發布的一致性。 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-05-28 | DevOps | 發布錯誤：意外推送 Agent 架構檔案 | 發布流程 | 於遊戲目錄內重新初始化 git 並強制推送 | 強制發布流程必須在專案子目錄進行 git init，嚴禁在根目錄執行 git 操作。 |
| 2026-05-28 | Physics | 無限跳躍 (Infinite Jump) | 在空中持續按空白鍵 | `is_on_ground` 狀態未正確更新 | 嚴格限制跳躍僅在 `is_on_ground` 為真時觸發，並增加牆壁跳躍的能量與狀態限制 |
| 2026-05-28 | Input/Physics | 吸附機制無反應/卡住 | 貼牆時按鍵操作 | 碰撞檢測範圍不足且與移動邏輯耦合過緊 | 使用 `inflate` 擴大碰撞檢測區域，並將吸附邏輯與移動物理分離，獨立判斷 |
| 2026-05-28 | Code Syntax | AttributeError: module 'pygame' has no attribute 'flip' | Running main.py | Replaced incorrect `pygame.flip()` with `pygame.display.flip()` | 加強代碼靜態審計，在正式部署前必須執行自動化檢查。 |
| 2026-05-28 | Input | 按住 Shift 會切換中文輸入法，導致遊戲操作失效 | 操作 Shift 鍵 | 將操作鍵改為 L-CTRL | 未來定義操作鍵時，強制避開作業系統快捷鍵保留鍵。 |
| 2026-05-28 | Physics | 牆面與地板碰撞後穿模 | 垂直掉落至平台邊緣 | 優化 spritecollideany 的碰撞條件與位置重置邏輯 | 設計平台類物件時，統一規範碰撞處理邏輯 (Ground-Platform Logic)。 |
| 2026-05-28 | Game Logic | 能量歸零後角色仍懸浮 | 能量歸零時邏輯未斷開 | 在 update 函式中強制加入能量檢查條件 | 強化狀態機 (FSM) 對資源消耗的狀態依賴檢查。 |
| 2026-05-28 | Logic | 角色失控 (Runaway Player) | 代碼合併錯誤 (嵌套函數定義) | 修正程式碼結構，正確移除重複定義的 update 函數 | 導入自動化代碼檢查工具 (Linting)，防止語法結構性錯誤。 |
| 2026-05-28 | Code Syntax | KeyError: 'climb' | 讀取 TEXTS 字典 | 於字典中補齊 climb 對應的語系內容 | 嚴格執行「字典定義與代碼渲染同步」檢查清單。 |
| 2026-05-28 | UX/UI | 選單文字超出邊界 | 顯示選單頁面 | 改用 draw_centered_text 進行置中與偏移計算 | UI 渲染必須統一使用置中函數，嚴禁硬編碼座標。 |

