# Lab 4: VibeCoding (Climber Repair Lab)

**Name:** Gaurav Girish  **SRN:** PES1UG24AM103
**Assigned repo:** https://github.com/SETAPESU26/37_climber
**My repo (updated code, one commit per task):** https://github.com/gaurav-2030/37_climber
**LLM used:** Claude (Claude Code)

## Contents

| File | Description |
|------|-------------|
| `before_changes.mp4` | 10 s of gameplay before any changes. The HUD height climbs to 81m, then drops to 62m when the climber falls back down (the bug). |
| `after_changes.mp4` | 10 s of gameplay on the same level after all changes. Shows the platform colour gradient, moving platforms, coin sparkles with "+50 / combo" popups, the combo counter, and the height holding at its peak (108m) after a fall. |
| `code/game.py` | Updated game code |
| `code/README.md` | Assignment README with a "Changes Made" section |
| `chat_history.pdf` | Complete chat history with the LLM |

## Tasks

1. **Height-score bug fixed.** `self.height = max(self.height, current_height)`, so the height never goes down during a run.
2. **`platform_color`.** Green → teal → violet → pink → gold gradient from the ground to the top.
3. **`moving_platform_speed`.** Every third platform oscillates, 1 to 3 px/frame, faster higher up.
4. **`on_coin_collected`.** Sparkle burst, floating "+50" label, and a combo counter (reset when a life is lost).

Run: `pip install pygame` then `python code/game.py`
