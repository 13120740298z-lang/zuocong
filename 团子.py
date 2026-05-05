import json
import math
import queue
import random
import sys
import textwrap
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request

API_URL = "http://127.0.0.1:8000/v1"
API_KEY = ""
MODEL = "deepseek-chat"

WINDOW_SIZE = 300
TRANSPARENT_KEY = "#ffffff"

BODY_COLOR = "#fff7f0"
BODY_OUTLINE = "#ffe7d6"
EYE_COLOR = "#1f1f1f"
BLUSH_COLOR = "#ffb3c7"
HAIR_COLOR = "#fff2ea"
GLOW_COLOR_1 = "#ffe9d6"
GLOW_COLOR_2 = "#fff1e6"


def clamp(v, a, b):
    return max(a, min(b, v))


def ease_in_out_sine(x):
    t = clamp(x, 0.0, 1.0)
    return -(math.cos(math.pi * t) - 1.0) / 2.0


def now_ms():
    return time.time() * 1000.0


class ChatClient:
    def __init__(self, api_url, api_key, model):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def _mock_reply(self, user_text):
        picks = [
            "团子正在听~",
            "嗯嗯！团子记住啦。",
            "你说的我懂，团子点点头。",
            "让我想想……我觉得你很有道理。",
            "好耶！团子开心地蹦了一下。",
        ]
        if user_text:
            snippet = user_text.strip().replace("\n", " ")[:18]
            return random.choice(picks[:-1]) + f"（你刚刚说：{snippet}…）"
        return random.choice(picks)

    def complete(self, user_text):
        if not self.api_key:
            return self._mock_reply(user_text)

        url = f"{self.api_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": user_text}],
            "temperature": 0.7,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url=url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
            raise RuntimeError(f"HTTP {e.code} {e.reason}{(' - ' + raw) if raw else ''}") from None
        except Exception as e:
            raise RuntimeError(str(e)) from None

        try:
            obj = json.loads(raw)
            content = obj["choices"][0]["message"]["content"]
        except Exception:
            raise RuntimeError("响应解析失败") from None

        if not content:
            raise RuntimeError("模型未返回内容")
        return content


class StateMachine:
    def __init__(self):
        self.mode = "idle"
        self.mode_since = now_ms()
        self.mode_until = None
        self.next_blink_at = now_ms() + random.uniform(4000, 8000)
        self.next_bounce_at = now_ms() + random.uniform(20000, 30000)
        self.bubble_text = None
        self.bubble_until = 0
        self.think_active = False
        self.walk_base_x = None
        self.walk_target_dx = 150

    def set_mode(self, mode, duration_ms=None):
        self.mode = mode
        self.mode_since = now_ms()
        self.mode_until = self.mode_since + duration_ms if duration_ms else None

    def schedule_idle_triggers(self):
        t = now_ms()
        self.next_blink_at = t + random.uniform(4000, 8000)
        self.next_bounce_at = t + random.uniform(20000, 30000)

    def set_bubble(self, text, ttl_ms=10000):
        self.bubble_text = text
        self.bubble_until = now_ms() + ttl_ms

    def clear_bubble_if_expired(self):
        if self.bubble_text and now_ms() >= self.bubble_until:
            self.bubble_text = None
            self.bubble_until = 0

    def update(self):
        t = now_ms()
        if self.mode_until and t >= self.mode_until:
            self.set_mode("idle")

        if self.mode == "idle":
            if t >= self.next_blink_at:
                self.set_mode("blink", 220)
                self.schedule_idle_triggers()
            elif t >= self.next_bounce_at:
                self.set_mode("bounce", 1400)
                self.schedule_idle_triggers()

        self.clear_bubble_if_expired()

    def frame_params(self, t0_ms):
        t = (now_ms() - t0_ms) / 1000.0
        idle_hover = math.sin((t / 3.0) * math.tau) * 8.0
        hair_swing = math.sin(t * math.tau * 0.8) * 0.35

        y_offset = idle_hover
        tilt_deg = 0.0
        eye_mode = "normal"
        sleep_style = False
        sway = 0.0

        if self.mode == "blink":
            eye_mode = "blink"

        if self.mode == "bounce":
            dt = (now_ms() - self.mode_since) / 1000.0
            p = clamp(dt / 1.2, 0.0, 1.0)
            amp = 26.0 * (1.0 - 0.45 * p)
            y_offset += -(math.sin(p * math.tau) ** 2) * amp

        if self.mode == "think":
            tilt_deg = -5.0
            y_offset += math.sin(t * math.tau * 0.6) * 2.0

        if self.mode == "walk":
            dt = (now_ms() - self.mode_since) / 1000.0
            p = clamp(dt / 2.8, 0.0, 1.0)
            if p < 0.5:
                w = ease_in_out_sine(p * 2.0)
                sway = math.sin(p * math.tau * 4.0) * 3.0
                walk_dx = self.walk_target_dx * w
            else:
                w = ease_in_out_sine((p - 0.5) * 2.0)
                sway = math.sin(p * math.tau * 4.0) * 3.0
                walk_dx = self.walk_target_dx * (1.0 - w)
            return {
                "y_offset": y_offset,
                "tilt_deg": tilt_deg,
                "hair_swing": hair_swing,
                "eye_mode": eye_mode,
                "sleep_style": sleep_style,
                "sway": sway,
                "walk_dx": walk_dx,
                "show_think": False,
            }

        if self.mode == "sleep":
            eye_mode = "sleep"
            sleep_style = True
            y_offset *= 0.35

        return {
            "y_offset": y_offset,
            "tilt_deg": tilt_deg,
            "hair_swing": hair_swing,
            "eye_mode": eye_mode,
            "sleep_style": sleep_style,
            "sway": sway,
            "walk_dx": 0.0,
            "show_think": self.mode == "think",
        }


class Renderer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.font = ("Segoe UI", 11)

    def _draw_glow(self, cx, cy, r, sleep_style):
        s1 = "gray25" if not sleep_style else "gray50"
        s2 = "gray12" if not sleep_style else "gray25"
        self.canvas.create_oval(
            cx - (r + 22),
            cy - (r + 22),
            cx + (r + 22),
            cy + (r + 22),
            fill=GLOW_COLOR_2,
            outline="",
            stipple=s2,
        )
        self.canvas.create_oval(
            cx - (r + 14),
            cy - (r + 14),
            cx + (r + 14),
            cy + (r + 14),
            fill=GLOW_COLOR_1,
            outline="",
            stipple=s1,
        )

    def _draw_body(self, cx, cy, r, sleep_style):
        stip = "gray50" if sleep_style else ""
        fill = "#fffaf6" if sleep_style else BODY_COLOR
        self.canvas.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            fill=fill,
            outline=BODY_OUTLINE,
            width=2,
            stipple=stip,
        )

    def _draw_hair(self, cx, cy, r, hair_swing, sleep_style):
        w = 5
        fill = "#fff8f3" if sleep_style else HAIR_COLOR
        dx = hair_swing * 10.0
        x0, y0 = cx, cy - r + 6
        p1 = (x0 - 8 - dx, y0 - 18)
        p2 = (x0 + 2 + dx * 0.4, y0 - 34)
        self.canvas.create_line(
            x0 - 2,
            y0,
            p1[0],
            p1[1],
            p2[0],
            p2[1],
            smooth=True,
            splinesteps=24,
            width=w,
            fill=fill,
            capstyle="round",
        )

    def _draw_face(self, cx, cy, eye_mode, sleep_style):
        eye_y = cy - 10
        left_x = cx - 15
        right_x = cx + 15
        if eye_mode == "normal":
            self.canvas.create_oval(left_x - 4, eye_y - 4, left_x + 4, eye_y + 4, fill=EYE_COLOR, outline="")
            self.canvas.create_oval(right_x - 4, eye_y - 4, right_x + 4, eye_y + 4, fill=EYE_COLOR, outline="")
        elif eye_mode == "blink":
            self.canvas.create_line(left_x - 7, eye_y, left_x + 7, eye_y, fill=EYE_COLOR, width=3, capstyle="round")
            self.canvas.create_line(right_x - 7, eye_y, right_x + 7, eye_y, fill=EYE_COLOR, width=3, capstyle="round")
        elif eye_mode == "sleep":
            k = 9
            self.canvas.create_line(left_x - k, eye_y - k / 2, left_x + k, eye_y + k / 2, fill=EYE_COLOR, width=3, capstyle="round")
            self.canvas.create_line(left_x - k, eye_y + k / 2, left_x + k, eye_y - k / 2, fill=EYE_COLOR, width=3, capstyle="round")
            self.canvas.create_line(right_x - k, eye_y - k / 2, right_x + k, eye_y + k / 2, fill=EYE_COLOR, width=3, capstyle="round")
            self.canvas.create_line(right_x - k, eye_y + k / 2, right_x + k, eye_y - k / 2, fill=EYE_COLOR, width=3, capstyle="round")

        blush_stip = "gray50" if not sleep_style else "gray75"
        self.canvas.create_oval(cx - 36, cy + 4, cx - 18, cy + 16, fill=BLUSH_COLOR, outline="", stipple=blush_stip)
        self.canvas.create_oval(cx + 18, cy + 4, cx + 36, cy + 16, fill=BLUSH_COLOR, outline="", stipple=blush_stip)

    def _draw_bubble(self, x, y, text):
        lines = textwrap.wrap(text, width=14)[:5]
        if not lines:
            return
        w = 210
        line_h = 16
        h = 12 + len(lines) * line_h
        bx = clamp(x, 8, WINDOW_SIZE - w - 8)
        by = clamp(y, 8, WINDOW_SIZE - h - 18)
        self.canvas.create_rectangle(
            bx,
            by,
            bx + w,
            by + h,
            fill="#fffdfb",
            outline="#ffd9c2",
            width=2,
        )
        tail = [bx + 60, by + h, bx + 78, by + h, bx + 68, by + h + 14]
        self.canvas.create_polygon(tail, fill="#fffdfb", outline="#ffd9c2", width=2)
        for i, line in enumerate(lines):
            self.canvas.create_text(bx + 10, by + 8 + i * line_h, anchor="nw", text=line, font=self.font, fill="#3a3a3a")

    def draw(self, params, bubble_text=None, think_text=None):
        self.canvas.delete("all")
        bg = self.canvas["bg"]
        if bg != TRANSPARENT_KEY:
            self.canvas.configure(bg=TRANSPARENT_KEY)

        cx = WINDOW_SIZE / 2
        cy = 160 + params["y_offset"]

        r = 60
        sleep_style = params["sleep_style"]

        sway = params.get("sway", 0.0)
        cx2 = cx + sway

        tilt = math.radians(params["tilt_deg"])

        def rot(px, py):
            dx = px - cx2
            dy = py - cy
            rx = dx * math.cos(tilt) - dy * math.sin(tilt)
            ry = dx * math.sin(tilt) + dy * math.cos(tilt)
            return cx2 + rx, cy + ry

        self._draw_glow(cx2, cy, r, sleep_style)
        self._draw_body(cx2, cy, r, sleep_style)

        hx, hy = rot(cx2, cy - r + 8)
        self._draw_hair(cx2, cy, r, params["hair_swing"], sleep_style)

        self._draw_face(cx2, cy, params["eye_mode"], sleep_style)

        if think_text:
            self._draw_bubble(cx2 + 30, cy - 170, think_text)
        if bubble_text:
            self._draw_bubble(cx2 + 26, cy - 188, bubble_text)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT_KEY)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(self.root, width=WINDOW_SIZE, height=WINDOW_SIZE, bg=TRANSPARENT_KEY, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._place_bottom_right()

        self.drag_anchor = None
        self.window_anchor = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Button-3>", self.on_right_click)

        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label="聊天", command=self.on_chat)
        self.menu.add_command(label="散步", command=self.on_walk)
        self.menu.add_command(label="睡觉", command=self.on_sleep)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.root.destroy)

        self.state = StateMachine()
        self.renderer = Renderer(self.canvas)

        self.chat = ChatClient(API_URL, API_KEY, MODEL)
        self.chat_q = queue.Queue()
        self.t0_ms = now_ms()

        self.root.after(16, self.tick)

    def _place_bottom_right(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, sw - WINDOW_SIZE)
        y = max(0, sh - WINDOW_SIZE)
        self.root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}+{x}+{y}")

    def on_press(self, e):
        self.drag_anchor = (e.x_root, e.y_root)
        self.window_anchor = (self.root.winfo_x(), self.root.winfo_y())

    def on_drag(self, e):
        if not self.drag_anchor or not self.window_anchor:
            return
        dx = e.x_root - self.drag_anchor[0]
        dy = e.y_root - self.drag_anchor[1]
        x = self.window_anchor[0] + dx
        y = self.window_anchor[1] + dy
        self.root.geometry(f"+{int(x)}+{int(y)}")

    def on_right_click(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def on_sleep(self):
        self.state.set_mode("sleep", 3000)
        self.state.set_bubble("Zzz", 3000)

    def on_walk(self):
        if self.state.mode == "walk":
            return
        self.state.walk_base_x = self.root.winfo_x()
        self.state.set_mode("walk", 2800)

    def _open_chat_dialog(self):
        top = tk.Toplevel(self.root)
        top.overrideredirect(True)
        top.wm_attributes("-topmost", True)
        top.configure(bg="#ffffff")
        try:
            top.wm_attributes("-transparentcolor", "#ffffff")
        except tk.TclError:
            pass

        w, h = 260, 64
        x = self.root.winfo_x() + (WINDOW_SIZE - w) // 2
        y = self.root.winfo_y() + WINDOW_SIZE - h - 18
        top.geometry(f"{w}x{h}+{x}+{y}")

        frame = tk.Frame(top, bg="#fffdfb", bd=1, highlightbackground="#ffd9c2", highlightthickness=1)
        frame.pack(fill="both", expand=True)

        entry = tk.Entry(frame, font=("Segoe UI", 10), bd=0, relief="flat")
        entry.insert(0, "")
        entry.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        btn = tk.Button(frame, text="发送", font=("Segoe UI", 10), bd=0, bg="#ffc8aa", activebackground="#ffc2a0")
        btn.pack(side="right", padx=10, pady=10)

        def close():
            try:
                top.destroy()
            except Exception:
                pass

        def send():
            text = entry.get().strip()
            if not text:
                close()
                return
            close()
            self.start_chat(text)

        btn.configure(command=send)
        entry.bind("<Return>", lambda _e: send())
        entry.bind("<Escape>", lambda _e: close())

        entry.focus_force()

    def on_chat(self):
        self._open_chat_dialog()

    def start_chat(self, text):
        self.state.set_mode("think")
        self.state.set_bubble("团子正在听~", 10000)

        def worker():
            try:
                reply = self.chat.complete(text)
                self.chat_q.put(("ok", reply))
            except Exception as e:
                self.chat_q.put(("err", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_walk_window_move(self, dx):
        if self.state.walk_base_x is None:
            self.state.walk_base_x = self.root.winfo_x()
        x = int(self.state.walk_base_x + dx)
        y = int(self.root.winfo_y())
        self.root.geometry(f"+{x}+{y}")

    def tick(self):
        self.state.update()
        params = self.state.frame_params(self.t0_ms)

        if self.state.mode == "walk":
            self._apply_walk_window_move(params.get("walk_dx", 0.0))
        if self.state.mode != "walk":
            self.state.walk_base_x = None

        think_text = "…" if params.get("show_think") else None
        bubble_text = self.state.bubble_text
        self.renderer.draw(params, bubble_text=bubble_text, think_text=think_text)

        try:
            while True:
                kind, payload = self.chat_q.get_nowait()
                if kind == "ok":
                    self.state.set_bubble(payload, 10000)
                else:
                    self.state.set_bubble(f"（请求失败）{payload}", 10000)
                if self.state.mode == "think":
                    self.state.set_mode("idle")
        except queue.Empty:
            pass

        self.root.after(16, self.tick)

    def run(self):
        self.root.mainloop()


def write_icon(path_):
    w = 64
    h = 64
    cx = w / 2
    cy = h / 2
    r = 26.5

    def inside_circle(x, y):
        dx = x + 0.5 - cx
        dy = y + 0.5 - cy
        return dx * dx + dy * dy <= r * r

    pixels = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            if not inside_circle(x, y):
                pixels += bytes((0, 0, 0, 0))
                continue

            col = (0xF0, 0xF7, 0xFF, 0xFF)
            if 26 <= y <= 33 and 22 <= x <= 25:
                col = (0x1F, 0x1F, 0x1F, 0xFF)
            if 26 <= y <= 33 and 38 <= x <= 41:
                col = (0x1F, 0x1F, 0x1F, 0xFF)
            if 34 <= y <= 39 and 16 <= x <= 21:
                col = (0xC7, 0xB3, 0xFF, 0xFF)
            if 34 <= y <= 39 and 43 <= x <= 48:
                col = (0xC7, 0xB3, 0xFF, 0xFF)

            pixels += bytes((col[0], col[1], col[2], col[3]))

    row_bytes = ((w + 31) // 32) * 4
    mask = bytearray()
    for y in range(h - 1, -1, -1):
        b = bytearray(row_bytes)
        for x in range(w):
            bit = 1 if not inside_circle(x, y) else 0
            if bit:
                byte_index = x // 8
                bit_index = 7 - (x % 8)
                b[byte_index] |= 1 << bit_index
        mask += b

    dib = bytearray()
    dib += (40).to_bytes(4, "little")
    dib += (w).to_bytes(4, "little", signed=True)
    dib += (h * 2).to_bytes(4, "little", signed=True)
    dib += (1).to_bytes(2, "little")
    dib += (32).to_bytes(2, "little")
    dib += (0).to_bytes(4, "little")
    dib += (len(pixels) + len(mask)).to_bytes(4, "little")
    dib += (0).to_bytes(4, "little")
    dib += (0).to_bytes(4, "little")
    dib += (0).to_bytes(4, "little")
    dib += (0).to_bytes(4, "little")

    image = dib + pixels + mask

    header = bytearray()
    header += (0).to_bytes(2, "little")
    header += (1).to_bytes(2, "little")
    header += (1).to_bytes(2, "little")

    entry = bytearray()
    entry += (w).to_bytes(1, "little")
    entry += (h).to_bytes(1, "little")
    entry += (0).to_bytes(1, "little")
    entry += (0).to_bytes(1, "little")
    entry += (1).to_bytes(2, "little")
    entry += (32).to_bytes(2, "little")
    entry += (len(image)).to_bytes(4, "little")
    entry += (6 + 16).to_bytes(4, "little")

    with open(path_, "wb") as f:
        f.write(header)
        f.write(entry)
        f.write(image)


def main():
    if "--gen-icon" in sys.argv:
        write_icon("团子.ico")
        return

    app = App()
    app.run()


if __name__ == "__main__":
    main()
