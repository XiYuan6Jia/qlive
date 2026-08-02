import pygame as pg
from gif_to_frames import extract_frames as read_gif
import threading, os, math
import pyaudio
import numpy as np
from collections import deque

# ── Windows API（通过 pywin32，参考 ex.py 的置顶逻辑）──
if os.name == 'nt':
    import win32gui
    import win32con
    import win32api

COLOR_KEY = (255, 0, 255)  # 品红色作为透明色键

# 窗口尺寸（所有动画资源统一 800×600）
WIN_W, WIN_H = 800, 600

# 右键拖拽缩放参数
MIN_SCALE, MAX_SCALE = 0.2, 4.0          # 缩放比例范围
RESIZE_THRESHOLD = 6                     # 判定为"拖拽缩放"的最小移动像素
RESIZE_SENSITIVITY = 400.0               # 灵敏度：鼠标每移动 N 像素 → 比例变化 100%


def get_cursor_screen_pos():
    """获取鼠标在屏幕上的绝对坐标"""
    return win32gui.GetCursorPos()


def get_window_screen_pos(hwnd):
    """获取窗口左上角在屏幕上的绝对坐标"""
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    return left, top


def force_topmost(hwnd):
    """强制窗口置顶（参考 ex.py：SWP_NOMOVE | SWP_NOSIZE 不改变位置尺寸）"""
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)


def set_window_pos(hwnd, x, y):
    """移动窗口到屏幕坐标 (x, y)，保持置顶但不抢焦点"""
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, x, y, 0, 0,
                          win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)


def make_window_transparent_and_topmost(hwnd, color_key=COLOR_KEY):
    """设置窗口为透明背景 + 总是置顶 + 不显示在任务栏"""
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    color_ref = win32api.RGB(*color_key)
    win32gui.SetLayeredWindowAttributes(hwnd, color_ref, 0, win32con.LWA_COLORKEY)

    # SWP_FRAMECHANGED 使扩展样式生效
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE)


class gif:
    def __init__(self, path, scale=1, speed=1, start_frame=1):
        self.frames = read_gif(path, start_frame)
        self.scale = scale
        self.current_frame = 0
        self.current_frame_time = 0.0
        self.total_frames = len(self.frames)
        self.image_surfaces = [self.pil_to_surface(frame) for frame in self.frames]
        self.speed = speed

    def pil_to_surface(self, pil_image):
        """Convert a PIL Image to a Pygame Surface."""
        mode = pil_image.mode
        size = pil_image.size
        data = pil_image.tobytes()

        if mode == "RGBA":
            surface = pg.image.fromstring(data, size, mode).convert_alpha()
        else:
            surface = pg.image.fromstring(data, size, mode).convert_alpha()

        if self.scale != 1:
            new_size = (int(size[0] * self.scale), int(size[1] * self.scale))
            surface = pg.transform.scale(surface, new_size)

        return surface

    def get_frame(self):
        """Get the current frame as a Pygame Surface."""
        frame_surface = self.image_surfaces[self.current_frame]
        self.current_frame_time = (self.current_frame_time + self.speed) % self.total_frames
        self.current_frame = int(round(self.current_frame_time)) % self.total_frames
        return frame_surface


class qlive_desktop:
    def __init__(self):
        pg.init()

        # 使用固定 800×600 窗口（所有动画资源统一尺寸）
        self.screen = pg.display.set_mode((WIN_W, WIN_H), pg.NOFRAME)
        pg.display.set_caption("Qlive Desktop")

        hwnd = pg.display.get_wm_info()["window"]
        make_window_transparent_and_topmost(hwnd)

        # 保存 hwnd 供 flip 后重置置顶
        self._hwnd = hwnd

        # 将窗口定位到屏幕右下角
        screen_w = win32api.GetSystemMetrics(0)
        screen_h = win32api.GetSystemMetrics(1)
        set_window_pos(hwnd, screen_w - WIN_W - 40, screen_h - WIN_H - 80)

        self.clock = pg.time.Clock()
        self.running = True
        self.fps = 30

        # ── 拖拽状态（基于屏幕绝对坐标，避免反馈循环） ──
        self.dragging = False
        self._drag_anchor_win_x = 0
        self._drag_anchor_win_y = 0
        self._drag_anchor_mouse_x = 0
        self._drag_anchor_mouse_y = 0

        # ── 右键拖拽缩放状态 ──
        self.window_scale = 1.0           # 当前窗口缩放比例
        self._rmb_down = False            # 右键是否按下
        self._resizing = False            # 是否正在拖拽缩放
        self._resize_anchor_mouse_x = 0   # 缩放起始鼠标屏幕坐标
        self._resize_anchor_mouse_y = 0
        self._resize_start_scale = 1.0    # 缩放起始时的比例
        self._window_size = (WIN_W, WIN_H)

        # 逻辑画布：固定 800×600，最终用最邻近算法缩放到窗口尺寸
        self._render_surf = pg.Surface((WIN_W, WIN_H))

        # 右键菜单
        self._menu_visible = False
        self._menu_rects = []

        # 用共享变量+锁替代Queue，只保留最新值
        self.db_lock = threading.Lock()
        self.latest_db = 0.0
        self.db_history = deque(maxlen=5)
        self.is_db_monitoring = True
        self.start_db_monitoring()

        self.force_play = False

    def start_db_monitoring(self):
        if self.is_db_monitoring:
            db_thread = threading.Thread(target=self.db_monitor, daemon=True)
            db_thread.start()

    def db_monitor(self):
        """使用pyaudio进行分贝检测，通过共享变量实时传递最新值（无延迟）"""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        p = pyaudio.PyAudio()
        stream = None

        try:
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)

                rms = np.sqrt(np.mean(audio_data ** 2))

                if rms > 0:
                    db = 20 * math.log10(rms / 32768.0)
                    db = max(0, db + 60)
                else:
                    db = 0

                with self.db_lock:
                    self.latest_db = db

        except Exception as e:
            print(f"DB监测错误: {e}")
        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()
            p.terminate()

    def load_gif(self):
        self.gif0 = gif("animations/default.gif", scale=1)
        self.gif1 = gif("animations/wizzle2.gif", scale=1, speed=0.75)
        self.gif2 = gif("animations/shoot.gif", scale=1, speed=0.75)
        self.gif_speak = gif("animations/speak.gif", scale=1, speed=1.25)

        self.layer_1 = self.gif0

    def display_gif(self, gifx: gif, x=0, y=0):
        frame = gifx.get_frame()
        self._render_surf.blit(frame, (x, y))

    def _to_logical_pos(self, pos):
        """将窗口物理坐标转换为逻辑坐标（固定 800×600 画布空间）"""
        w, h = self.screen.get_size()
        if w == WIN_W and h == WIN_H:
            return pos
        return (int(pos[0] * WIN_W / w), int(pos[1] * WIN_H / h))

    def _apply_window_scale(self):
        """按 self.window_scale 重建窗口以匹配新尺寸，保持右下角锚点不变"""
        new_w = max(1, int(round(WIN_W * self.window_scale)))
        new_h = max(1, int(round(WIN_H * self.window_scale)))
        if (new_w, new_h) == self._window_size:
            return

        # 记录当前窗口右下角作为缩放锚点
        hwnd = pg.display.get_wm_info()["window"]
        _l, _t, right, bottom = win32gui.GetWindowRect(hwnd)
        anchor_right, anchor_bottom = right, bottom

        self._window_size = (new_w, new_h)
        # 重建窗口以匹配新尺寸（SDL 窗口尺寸即绘制表面尺寸）
        self.screen = pg.display.set_mode((new_w, new_h), pg.NOFRAME)
        pg.display.set_caption("Qlive Desktop")
        hwnd = pg.display.get_wm_info()["window"]
        make_window_transparent_and_topmost(hwnd)
        self._hwnd = hwnd

        # 保持窗口右下角固定
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST,
                              anchor_right - new_w, anchor_bottom - new_h, 0, 0,
                              win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

    # ── 右键菜单 ──
    def _show_context_menu(self, mouse_x, mouse_y):
        """在鼠标位置显示右键菜单"""
        self._menu_visible = True
        self._menu_rects = []
        font = pg.font.Font(None, 22)

        items = [
            ("退出 (Exit)", "exit"),
        ]

        item_h = 28
        padding = 12
        max_w = 0
        for label, _ in items:
            w = font.size(label)[0] + padding * 2
            if w > max_w:
                max_w = w

        menu_rect = pg.Rect(mouse_x, mouse_y, max_w, item_h * len(items) + 6)
        # 防止菜单超出窗口
        if menu_rect.right > WIN_W:
            menu_rect.x = mouse_x - max_w
        if menu_rect.bottom > WIN_H:
            menu_rect.y = mouse_y - menu_rect.height

        for i, (label, key) in enumerate(items):
            item_rect = pg.Rect(menu_rect.x + 2, menu_rect.y + 2 + i * item_h,
                                max_w - 4, item_h)
            self._menu_rects.append((item_rect, label, key))

        self._menu_bg_rect = menu_rect

    def _draw_context_menu(self):
        """绘制右键菜单"""
        if not self._menu_visible:
            return
        font = pg.font.Font(None, 22)

        bg_surf = pg.Surface((self._menu_bg_rect.width, self._menu_bg_rect.height))
        bg_surf.fill((60, 60, 60))
        pg.draw.rect(bg_surf, (140, 140, 140), bg_surf.get_rect(), 1)
        self._render_surf.blit(bg_surf, (self._menu_bg_rect.x, self._menu_bg_rect.y))

        mouse_pos = self._to_logical_pos(pg.mouse.get_pos())
        for item_rect, label, _key in self._menu_rects:
            if item_rect.collidepoint(mouse_pos):
                hover_surf = pg.Surface((item_rect.width, item_rect.height))
                hover_surf.fill((80, 120, 200))
                self._render_surf.blit(hover_surf, (item_rect.x, item_rect.y))

            text_surf = font.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(midleft=(item_rect.x + 8, item_rect.centery))
            self._render_surf.blit(text_surf, text_rect)

    def _handle_context_menu_click(self, pos):
        """处理右键菜单点击"""
        for item_rect, _label, key in self._menu_rects:
            if item_rect.collidepoint(pos):
                if key == "exit":
                    self.running = False
                break
        self._menu_visible = False
        self._menu_rects = []

    def run(self):
        while self.running:
            # 麦克风：从共享变量读取最新dB值
            if self.is_db_monitoring:
                with self.db_lock:
                    current_db = self.latest_db
                self.db_history.append(current_db)
                smoothed_db = sum(self.db_history) / len(self.db_history)

                if not self.force_play:
                    if smoothed_db < 15:
                        self.layer_1 = self.gif0
                    else:
                        self.layer_1 = self.gif_speak

            # 事件处理
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

                # 右键菜单显示时：点击任意位置处理菜单（坐标转逻辑空间）
                if self._menu_visible:
                    if event.type == pg.MOUSEBUTTONDOWN:
                        self._handle_context_menu_click(self._to_logical_pos(event.pos))
                    continue

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.running = False
                    if event.key == pg.K_KP0 and pg.key.get_mods() & pg.KMOD_CTRL:
                        self.layer_1 = self.gif0
                        self.force_play = False
                    if event.key == pg.K_KP1 and pg.key.get_mods() & pg.KMOD_CTRL:
                        self.layer_1 = self.gif1
                        self.force_play = True
                    if event.key == pg.K_KP2 and pg.key.get_mods() & pg.KMOD_CTRL:
                        self.layer_1 = self.gif2
                        self.force_play = True

                # ── 左键拖拽：按下时记录锚点 ──
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.dragging:
                        hwnd = pg.display.get_wm_info()["window"]
                        self._drag_anchor_win_x, self._drag_anchor_win_y = \
                            get_window_screen_pos(hwnd)
                        self._drag_anchor_mouse_x, self._drag_anchor_mouse_y = \
                            get_cursor_screen_pos()
                        self.dragging = True

                if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = False

                # ── 右键拖拽缩放窗口 ──
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                    if not self._rmb_down:
                        self._rmb_down = True
                        self._resizing = False
                        self._resize_anchor_mouse_x, self._resize_anchor_mouse_y = \
                            get_cursor_screen_pos()
                        self._resize_start_scale = self.window_scale

                if event.type == pg.MOUSEBUTTONUP and event.button == 3:
                    if self._rmb_down:
                        self._rmb_down = False
                        if not self._resizing:
                            # 右键单击（未发生拖拽）→ 弹出菜单
                            self._show_context_menu(*self._to_logical_pos(event.pos))
                        self._resizing = False

                # 按住右键移动超过阈值 → 进入缩放模式
                if event.type == pg.MOUSEMOTION and self._rmb_down and not self._resizing:
                    cur_x, cur_y = get_cursor_screen_pos()
                    dx = cur_x - self._resize_anchor_mouse_x
                    dy = cur_y - self._resize_anchor_mouse_y
                    if math.hypot(dx, dy) > RESIZE_THRESHOLD:
                        self._resizing = True

            # ── 拖拽更新：基于屏幕绝对坐标差移动窗口 ──
            if self.dragging:
                cur_x, cur_y = get_cursor_screen_pos()
                new_x = self._drag_anchor_win_x + (cur_x - self._drag_anchor_mouse_x)
                new_y = self._drag_anchor_win_y + (cur_y - self._drag_anchor_mouse_y)
                hwnd = pg.display.get_wm_info()["window"]
                set_window_pos(hwnd, new_x, new_y)

            # ── 右键拖拽缩放更新：按鼠标位移计算缩放比例 ──
            if self._rmb_down and self._resizing:
                cur_x, cur_y = get_cursor_screen_pos()
                dx = cur_x - self._resize_anchor_mouse_x
                dy = cur_y - self._resize_anchor_mouse_y
                new_scale = self._resize_start_scale * (1.0 + (dx + dy) / RESIZE_SENSITIVITY)
                new_scale = max(MIN_SCALE, min(MAX_SCALE, new_scale))
                if new_scale != self.window_scale:
                    self.window_scale = new_scale
                    self._apply_window_scale()

            # 在逻辑画布（固定 800×600）上绘制内容
            self._render_surf.fill(COLOR_KEY)

            # 图层1
            self.display_gif(self.layer_1)

            # 右键菜单（最顶层绘制）
            self._draw_context_menu()

            # 用最邻近算法将逻辑画布缩放到窗口尺寸并显示
            win_w, win_h = self.screen.get_size()
            if (win_w, win_h) == (WIN_W, WIN_H):
                self.screen.blit(self._render_surf, (0, 0))
            else:
                pg.transform.scale(self._render_surf, (win_w, win_h), self.screen)

            pg.display.flip()
            # flip() 可能被 SDL 重置 Z-order → 立即修复置顶
            force_topmost(self._hwnd)
            self.clock.tick(self.fps)

        self._topmost_running = False
        pg.quit()


if __name__ == "__main__":
    app = qlive_desktop()
    app.load_gif()
    app.run()
