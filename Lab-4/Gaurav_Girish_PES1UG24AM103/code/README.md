# Climber Repair Lab

This project is a single-file vertical-platformer clone using **Pygame**. It introduces students to platform collision, a scrolling camera, and item pickups using a small, readable object-oriented codebase.

---

## What's Provided

A working Climber game with:

- A player-controlled climber with gravity, jumping, and collision that only lands from above (never snaps up through a platform from below)
- A generated column of platforms leading to the top of the level, with a camera that scrolls up as the player climbs (and never scrolls back down)
- Coins scattered on some platforms that add to the score when collected
- Lives, scoring, and win/lose conditions (falling off the bottom of the screen costs a life; reaching the top wins)

It has **one deliberate bug** and **three optional features** left as empty functions. You are expected to **analyze**, **interact with an AI assistant**, and **complete/fix** the game to make it fully functional and more interesting.

### **Use an LLM (e.g. ChatGPT or Claude) as your debugging and pair-programming partner for this lab.**

---

## Getting Started

### Setup

1. Make sure you have Python 3.10+ installed.
2. Install dependencies:

```bash
pip install pygame
```

3. Run the game:

```bash
python game.py
```

**Controls:** A/Left or D/Right to move, Space/W/Up to jump, `R` to reset.

---

## Tasks to Complete

Each task must be completed using an iterative process involving LLM suggestions and your critical code review.

### Task 1: Fix the height-score bug

> The "Height" shown in the HUD is meant to track the *best* height the player has ever reached during a run — like every real climbing or endless-runner score, it should never go down. In the current build, the height recalculates fresh every frame from the player's current position, so climbing up and then coming back down (for example, after riding a moving platform, or backtracking to grab a coin) makes the displayed height drop instead of holding at its peak. Look at where `self.height` is assigned in `Game.update` and compare it with how the height is actually meant to behave.

### Task 2: Implement `platform_color(index, total)`

> Called once per platform, at generation time, as `self.color = platform_color(index, total) or (100, 180, 100)` inside `Platform.__init__`. `index` is the platform's position in the climb (0 is the ground, higher numbers are higher up); `total` is the total number of generated platforms. Return an `(r, g, b)` color, or `None` to keep the default green. Idea: shift the color gradually as `index` approaches `total`, so higher platforms look different from lower ones.

### Task 3: Implement `moving_platform_speed(index, total)`

> Called once per (non-ground) platform, at generation time, as part of `self.speed = moving_platform_speed(index, total) or 0`. It receives the same `index`/`total` as above and should return a horizontal oscillation speed in pixels per frame, or `None`/`0` to keep that platform static. The oscillation mechanism itself — bouncing between bounds, carrying the player along while they stand on it — is already implemented in the `Platform` class and `Game.update`; you only need to decide which platforms move and how fast. Idea: return a small speed for every third platform.

### Task 4: Implement `on_coin_collected(coin, score)`

> Called from `Game.update` the instant the player touches a coin, right after its 50 points have been added to the score and the coin has been marked collected. It receives the `Coin` that was collected and the score after it was added. Its return value is ignored. Idea: a sparkle effect at the coin's position, or a running "combo" counter for coins collected without falling.

---

## Expected Behavior

- The player only lands on a platform when falling onto it from above; it can't be snapped up onto a platform's underside or side
- The camera scrolls upward as the player climbs and never scrolls back down, even if the player falls
- Coins disappear the moment they're touched and immediately add to the score
- Falling off the bottom of the screen costs a life and respawns the player at their last safe platform; the game ends when lives reach zero
- Reaching the topmost platform ends the game with a win

---

## Changes Made

| Task | Change |
|------|--------|
| 1. Height-score bug | `Game.update` now keeps `self.height = max(self.height, current_height)`, so the HUD shows the best height of the run and never drops when the player falls or rides back down. `reset()` still sets it to 0. |
| 2. `platform_color` | Platforms fade through green → teal → violet → pink → gold as `index` approaches `total`; the ground keeps the default green. |
| 3. `moving_platform_speed` | Every third platform moves. Speed ramps from 1 to 3 px/frame with height, and the starting direction alternates. |
| 4. `on_coin_collected` | Collecting a coin bursts sparkle particles, shows a floating "+50" label, and increments a combo counter (coins in a row without losing a life). The HUD shows the current and best combo. Losing a life resets the combo, and `R` clears everything. |

---

## Folder Structure

```
climber/
├── game.py
└── README.md
```

---

## Submission Checklist

Submission is only the following three things:

- [] A 10-second video of gameplay **before** your changes, showing the bug/broken behavior
- [] A 10-second video of gameplay **after** your changes, showing the bug fixed and the new features working
- [] The Chat/LLM used page link, with the complete chat history
