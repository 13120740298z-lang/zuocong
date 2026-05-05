# Dumpling（团子）桌宠（tkinter）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver `团子.py` (single-file tkinter desktop pet) + `build.bat` (PyInstaller onefile .exe packaging) with transparent always-on-top frameless window, drag, context menu, state-machine animations, and optional OpenAI-compatible chat.

**Architecture:** Single tkinter process. `App` owns window/canvas/events; `StateMachine` computes animation params; renderer redraws full frame each tick; chat runs in background thread and reports back via a queue polled by `after`.

**Tech Stack:** Python 3 standard library + tkinter, Windows transparent color-key, PyInstaller (packaging).

---

## File Structure

- Create: `/workspace/团子.py`
- Create: `/workspace/build.bat`
- (Optional) Modify: `/workspace/README.md` to add Python build/run instructions

---

### Task 1: Implement `团子.py` application skeleton (window, canvas, events)

**Files:**
- Create: `/workspace/团子.py`

- [ ] **Step 1: Create top-level config constants**

```python
API_URL = "http://127.0.0.1:8000/v1"
API_KEY = ""
MODEL = "deepseek-chat"
```

- [ ] **Step 2: Create Tk root window with required attributes**

```python
root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-topmost", True)
root.configure(bg="#ffffff")
try:
    root.wm_attributes("-transparentcolor", "#ffffff")
except tk.TclError:
    pass
```

- [ ] **Step 3: Create a 300x300 Canvas with pure-white background**

```python
canvas = tk.Canvas(root, width=300, height=300, bg="#ffffff", highlightthickness=0)
canvas.pack(fill="both", expand=True)
```

- [ ] **Step 4: Initial position bottom-right**

```python
sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
x, y = max(0, sw - 300), max(0, sh - 300)
root.geometry(f"300x300+{x}+{y}")
```

- [ ] **Step 5: Drag-to-move bindings**

```python
canvas.bind("<ButtonPress-1>", on_press)
canvas.bind("<B1-Motion>", on_drag)
```

- [ ] **Step 6: Context menu (聊天/散步/睡觉/退出)**

```python
menu = tk.Menu(root, tearoff=False)
menu.add_command(label="聊天", command=on_chat)
menu.add_command(label="散步", command=on_walk)
menu.add_command(label="睡觉", command=on_sleep)
menu.add_separator()
menu.add_command(label="退出", command=root.destroy)
canvas.bind("<Button-3>", on_right_click)
```

- [ ] **Step 7: Syntax check**

Run:

```bash
python -m py_compile /workspace/团子.py
```

Expected: exit code 0.

---

### Task 2: Implement renderer: Dumpling drawing (no external assets)

**Files:**
- Modify: `/workspace/团子.py`

- [ ] **Step 1: Implement `Renderer.draw(frame_params)`**

Drawing requirements:
- body: warm white circle (avoid pure white)
- glow: multi-layer circles using stipple patterns
- eyes: dots / blink lines / sleep >< lines
- blush: pink ellipses with stipple
- hair: smooth curve via `create_line(..., smooth=True)`

- [ ] **Step 2: Implement speech bubble drawing**

Bubble requirements:
- rounded look approximated with rectangle + tail
- wrap text to max width
- auto-hide after 10 seconds

- [ ] **Step 3: Syntax check**

Run:

```bash
python -m py_compile /workspace/团子.py
```

Expected: exit code 0.

---

### Task 3: Implement animation state machine (idle/blink/bounce/think/walk/sleep)

**Files:**
- Modify: `/workspace/团子.py`

- [ ] **Step 1: Create `StateMachine` with mode + timers**

Modes: `idle`, `blink`, `bounce`, `think`, `walk`, `sleep`

- [ ] **Step 2: Random triggers**

- blink every 4–8 seconds when idle
- bounce every 20–30 seconds when idle

- [ ] **Step 3: Per-mode param calculation**

- idle: yOffset sin(t, 3s), hair sway
- blink: eyes lines for 0.2s
- bounce: two bounces (sin² with decay)
- think: tilt -5°, show "…"
- walk: window move +150px and back + body sway
- sleep: 3s, eyes `><`, body drawn with stipple/washed colors

- [ ] **Step 4: Main loop `tick()` via `after(16, ...)`**

Each tick:
- update state
- redraw canvas
- poll chat queue for replies and update bubble

- [ ] **Step 5: Syntax check**

Run:

```bash
python -m py_compile /workspace/团子.py
```

Expected: exit code 0.

---

### Task 4: Implement chat input + optional OpenAI-compatible call (threaded)

**Files:**
- Modify: `/workspace/团子.py`

- [ ] **Step 1: Implement a lightweight input dialog (Toplevel)**

Requirements:
- shows on “聊天”
- submit text triggers think mode

- [ ] **Step 2: Implement `ChatClient.complete(text)`**

If `API_KEY` empty: return mock cute reply.  
Else:
- POST `API_URL + "/chat/completions"`
- JSON:

```json
{"model":"deepseek-chat","messages":[{"role":"user","content":"..."}],"temperature":0.7}
```

- Read `choices[0].message.content`

- [ ] **Step 3: Background thread + queue**

Requirements:
- never block tkinter main loop
- bubble shows “团子正在听~” immediately, then actual reply on completion

- [ ] **Step 4: Syntax check**

Run:

```bash
python -m py_compile /workspace/团子.py
```

Expected: exit code 0.

---

### Task 5: Implement `build.bat` (onefile .exe, no console) + icon generation

**Files:**
- Create: `/workspace/build.bat`
- Modify: `/workspace/团子.py` (add `--gen-icon` mode)

- [ ] **Step 1: Add `--gen-icon` mode in `团子.py`**

Behavior:
- if `--gen-icon` passed: write `团子.ico` (PNG-in-ICO, base64 embedded) and exit(0)

- [ ] **Step 2: Create `build.bat`**

```bat
@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

if not exist 团子.ico (
  python 团子.py --gen-icon
)

python -m pip install --upgrade pip
python -m pip install pyinstaller

pyinstaller --onefile --noconsole --icon=团子.ico 团子.py
echo.
echo 打包完成：dist\\团子.exe
pause
```

- [ ] **Step 3: Validate script syntax in CI**

Run:

```bash
python -m py_compile /workspace/团子.py
```

Expected: exit code 0.

---

## Self-Review Checklist

- Transparent color key uses pure white background; dumpling draw colors never use pure white fills.
- All animations exist and transitions are time-based and smooth.
- No network call blocks UI; chat always returns (mock or real).
- No secrets are printed or logged.
- `build.bat` produces a single-file exe without console.

