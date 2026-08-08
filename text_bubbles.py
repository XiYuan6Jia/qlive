"""
text_bubbles.py —— 8 种风格的 pygame 文本气泡模块

风格一览:
  classic  经典圆角气泡    圆角矩形 + 三角尾巴 + 描边
  speech   漫画对话气泡    白底黑边双线框
  thought  思考气泡        云朵形状 + 渐变小圆尾巴
  burst    惊呼气泡        锯齿星形爆炸（漫画风）
  banner   缎带横幅        两端斜切燕尾（无尾巴）
  chat     聊天气泡        Messenger 风圆润小尾巴
  neon     霓虹气泡        多层辉光描边
  pixel    像素气泡        硬边方块 + 阶梯像素尾巴

快速开始:
    from text_bubbles import TextBubble
    bubble = TextBubble("你好呀~", style="neon", tail="down")
    bubble.blit(screen, (400, 200))      # 气泡按 anchor 对齐到 (400,200)

    # 改内容:
    bubble.text = "新内容"; bubble.rebuild()
    # 改位置:
    bubble.pos = (x, y); bubble.blit(screen)

出现 / 消失动画（每种风格对应专属动画）:
    bubble.show()            # 播放"出现"动画
    bubble.hide()            # 播放"消失"动画
    bubble.update(dt)        # 每帧调用推进动画，dt 单位秒
    bubble.blit(screen, pos) # 动画期间自动应用透明度/缩放/位移

运行演示:
    python demo_bubbles.py                  # 交互演示
    python demo_bubbles.py --save out.png   # 保存一帧预览图
"""

import math

import pygame as pg

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
STYLES = ("classic", "speech", "thought", "burst", "banner", "chat", "neon", "pixel")

TAIL_UP = "up"
TAIL_DOWN = "down"
TAIL_LEFT = "left"
TAIL_RIGHT = "right"

# 各风格默认配色（可用参数覆盖）
_PALETTES = {
    "classic": dict(bg=(44, 48, 62),    border=(96, 102, 128), border_w=2, radius=16),
    "speech":  dict(bg=(255, 255, 255), border=(24, 24, 28),   border_w=3, radius=12),
    "thought": dict(bg=(240, 240, 248), border=(110, 115, 135), border_w=2, radius=18),
    "burst":   dict(bg=(255, 196, 0),   border=(255, 255, 255), border_w=5, radius=0),
    "banner":  dict(bg=(222, 55, 60),   border=(255, 255, 255), border_w=0, radius=0),
    "chat":    dict(bg=(30, 132, 255),  border=None,            border_w=0, radius=20),
    "neon":    dict(bg=(18, 12, 40),    border=(80, 210, 255),  border_w=2, radius=14),
    "pixel":   dict(bg=(52, 54, 74),    border=(255, 255, 255), border_w=3, radius=0),
}
_TEXT_COLORS = {
    "speech":  (30, 30, 34),
    "thought": (45, 45, 65),
    "burst":   (255, 255, 255),
    "banner":  (255, 255, 255),
    "chat":    (255, 255, 255),
}

# 各风格出现/消失动画时长 (enter, exit) 单位: 秒
_ANIM_DUR = {
    "classic": (0.25, 0.18),
    "speech":  (0.30, 0.16),
    "thought": (0.40, 0.25),
    "burst":   (0.30, 0.15),
    "banner":  (0.35, 0.20),
    "chat":    (0.30, 0.20),
    "neon":    (0.45, 0.35),
    "pixel":   (0.35, 0.20),
}


# ---- 缓动函数 ----
def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def _ease_in_cubic(t):
    return t ** 3


def _ease_in_quad(t):
    return t * t


def _ease_out_back(t):
    """带回弹的缓出（会略超过 1 再回落）。"""
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


class TextBubble:
    """文本气泡。

    参数:
        text        显示的文字（支持 \\n 与自动换行）
        style       风格: classic / speech / thought / burst / banner / chat / neon / pixel
        pos         锚点位置（blit 时使用）
        font        pg.font.Font 对象；None 则用默认字体（font_size 生效）
        font_size   默认字体大小
        text_color  文字颜色；None 使用风格默认
        bg_color    主体背景色；None 使用风格默认
        border_color 描边色；None 使用风格默认（可为 None 表示无描边）
        border_width 描边宽度
        padding     内边距 (x, y)
        tail        尾巴方向: up / down / left / right / None
        tail_size   尾巴长度
        radius      圆角半径（部分风格）
        anchor      对齐点: center / topleft / midbottom / midtop / midleft / midright ...
        max_width   自动换行最大宽度（px），None 不换行
        glow_color  霓虹风格辉光颜色
        bold        粗体；None 时 burst/speech 默认粗体
    """

    def __init__(self, text, style="classic", pos=(0, 0), font=None, font_size=26,
                 text_color=None, bg_color=None, border_color=None, border_width=None,
                 padding=(18, 12), tail=TAIL_DOWN, tail_size=16, radius=None,
                 anchor="center", max_width=None, glow_color=None, bold=None,
                 line_spacing=4):
        if style not in STYLES:
            raise ValueError(f"未知风格 {style!r}，可选: {', '.join(STYLES)}")
        self.style = style
        self.text = text
        self.pos = pos
        self.font = font
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.padding = padding
        self.tail = tail
        self.tail_size = tail_size
        self.anchor = anchor
        self.max_width = max_width
        self.glow_color = glow_color or (80, 210, 255)
        self.bold = (style in ("burst", "speech")) if bold is None else bold

        pal = _PALETTES[style]
        self.bg_color = bg_color if bg_color is not None else pal["bg"]
        self.border_color = border_color if border_color is not None else pal["border"]
        self.border_width = border_width if border_width is not None else pal["border_w"]
        self.radius = radius if radius is not None else pal["radius"]
        self.text_color = text_color if text_color is not None else _TEXT_COLORS.get(style, (255, 255, 255))

        # 霓虹风格需要预留辉光外扩空间
        self.margin = 28 if style == "neon" else 0

        self._rect = None

        # ---- 动画状态 ----
        self.visible = True        # 是否显示（hide 动画结束后置 False）
        self.animating = False     # 是否正在播放动画
        self.anim_kind = None      # "enter" / "exit"
        self.anim_time = 0.0       # 当前动画已进行时间（秒）
        self.anim_duration = 0.0   # 当前动画总时长（秒）
        self.on_complete = None    # 动画结束回调 callback(bubble)

        self.rebuild()

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def rebuild(self):
        """根据当前属性重新生成气泡表面（改文字/颜色/尾巴后调用）。"""
        if self.font is None:
            self.font = pg.font.SysFont(None, self.font_size)
        if self.bold:
            self.font.set_bold(True)

        # 1. 渲染文字（自动换行）
        self.text_lines = [self.font.render(ln, True, self.text_color)
                           for ln in self._wrap_text(self.text)]
        tw = max((s.get_width() for s in self.text_lines), default=0)
        th = (sum(s.get_height() for s in self.text_lines)
              + self.line_spacing * (len(self.text_lines) - 1))
        pad_x, pad_y = self.padding
        body_w, body_h = tw + pad_x * 2, th + pad_y * 2

        # 2. 尾巴尺寸（banner/burst 无尾巴）
        if self.tail and self.style not in ("banner", "burst"):
            if self.style == "thought":
                self.tail_h = int(self.tail_size * 2.0) + 4
            elif self.style == "pixel":
                self.tail_h = int(self.tail_size * 1.5)
            else:
                self.tail_h = self.tail_size
        else:
            self.tail = None
            self.tail_h = 0

        m = self.margin
        # 3. 计算表面尺寸与主体矩形
        if self.tail == TAIL_DOWN:
            w, h = body_w + m * 2, body_h + self.tail_h + m * 2
            self.body_rect = pg.Rect(m, m, body_w, body_h)
        elif self.tail == TAIL_UP:
            w, h = body_w + m * 2, body_h + self.tail_h + m * 2
            self.body_rect = pg.Rect(m, m + self.tail_h, body_w, body_h)
        elif self.tail == TAIL_LEFT:
            w, h = body_w + self.tail_h + m * 2, body_h + m * 2
            self.body_rect = pg.Rect(m + self.tail_h, m, body_w, body_h)
        elif self.tail == TAIL_RIGHT:
            w, h = body_w + self.tail_h + m * 2, body_h + m * 2
            self.body_rect = pg.Rect(m, m, body_w, body_h)
        else:
            w, h = body_w + m * 2, body_h + m * 2
            self.body_rect = pg.Rect(m, m, body_w, body_h)

        self.surf = pg.Surface((w, h), pg.SRCALPHA)
        if self.tail:
            self._draw_tail()   # 内部先画尾巴再画主体，保证两者无缝衔接
        else:
            self._draw_body()
        self._draw_text()

    def blit(self, screen, pos=None):
        """把气泡绘制到 screen，使 anchor 对齐到 pos（默认 self.pos）。

        动画期间会自动应用透明度 / 缩放 / 位移；
        消失动画结束后且未重新显示时，什么都不画。
        """
        if not self.visible and not self.animating:
            return None
        p = pos if pos is not None else self.pos
        alpha, scale, dx, dy = self._anim_state()

        surf = self.surf
        if scale != 1.0:
            w = max(1, int(surf.get_width() * scale))
            h = max(1, int(surf.get_height() * scale))
            surf = pg.transform.smoothscale(surf, (w, h))
        rect = surf.get_rect()
        setattr(rect, self.anchor, (p[0] + dx, p[1] + dy))
        if alpha < 255:
            surf.set_alpha(alpha)
        screen.blit(surf, rect)
        if alpha < 255:
            surf.set_alpha(255)
        self._rect = rect
        return rect

    def get_size(self):
        return self.surf.get_size()

    @property
    def rect(self):
        return self._rect

    @property
    def is_visible(self):
        return self.visible

    # ------------------------------------------------------------------
    # 动画接口
    # ------------------------------------------------------------------
    def show(self, duration=None, on_complete=None):
        """播放"出现"动画并显示气泡。

        duration: 动画时长（秒），None 用风格默认。
        on_complete: 动画结束回调 callback(bubble)。
        """
        self.visible = True
        self._start_anim("enter", duration, on_complete)

    def hide(self, duration=None, on_complete=None):
        """播放"消失"动画；结束后 visible 置为 False。"""
        if not self.visible and not self.animating:
            return
        self._start_anim("exit", duration, on_complete)

    def update(self, dt):
        """每帧调用推进动画，dt 单位秒。

        返回 True 表示本帧动画刚好结束（可用于链式触发下一步）。
        """
        if not self.animating:
            return False
        self.anim_time += dt
        if self.anim_time >= self.anim_duration:
            self.animating = False
            if self.anim_kind == "exit":
                self.visible = False
            cb, self.on_complete = self.on_complete, None
            if cb:
                cb(self)
            return True
        return False

    def _start_anim(self, kind, duration, on_complete):
        if duration is None:
            d = _ANIM_DUR.get(self.style, (0.3, 0.2))
            duration = d[0] if kind == "enter" else d[1]
        self.anim_kind = kind
        self.anim_time = 0.0
        self.anim_duration = max(0.05, duration)
        self.animating = True
        self.on_complete = on_complete

    def _anim_state(self):
        """根据当前动画进度返回 (alpha, scale, offset_x, offset_y)。"""
        if not self.animating:
            return 255, 1.0, 0, 0
        t = max(0.0, min(1.0, self.anim_time / self.anim_duration))
        kind = self.anim_kind
        s = self.style

        if s == "classic":      # 淡入上浮 / 淡出下沉
            if kind == "enter":
                e = _ease_out_cubic(t)
                return int(255 * e), 1.0, 0, int(20 * (1 - e))
            e = _ease_in_quad(t)
            return int(255 * (1 - e)), 1.0, 0, int(14 * e)
        if s == "speech":       # 漫画弹跳放大 / 快速缩小
            if kind == "enter":
                return int(255 * _ease_out_cubic(t)), _ease_out_back(t), 0, 0
            e = _ease_in_cubic(t)
            return int(255 * (1 - e)), max(0.1, 1 - 0.8 * e), 0, 0
        if s == "thought":      # 轻飘淡入 / 淡出
            if kind == "enter":
                e = _ease_out_cubic(t)
                return int(255 * e), 0.9 + 0.1 * e, 0, int(14 * (1 - e))
            e = _ease_in_quad(t)
            return int(255 * (1 - e)), 1 - 0.15 * e, 0, 0
        if s == "burst":        # 爆炸式放大回弹 / 急速收缩
            if kind == "enter":
                return int(255 * _ease_out_cubic(t)), 0.2 + 0.8 * _ease_out_back(t), 0, 0
            e = _ease_in_quad(t)
            return int(255 * (1 - e)), max(0.05, 1 - 0.9 * e), 0, 0
        if s == "banner":       # 从左甩入带过冲 / 向右甩出
            if kind == "enter":
                return int(255 * _ease_out_cubic(t)), 1.0, int(-36 * (1 - _ease_out_back(t))), 0
            e = _ease_in_quad(t)
            return int(255 * (1 - e)), 1.0, int(44 * e), 0
        if s == "chat":         # 聊天上滑出现 / 下滑消失
            if kind == "enter":
                e = _ease_out_cubic(t)
                return int(255 * e), 1.0, 0, int(34 * (1 - e))
            e = _ease_in_quad(t)
            return int(255 * (1 - e)), 1.0, 0, int(26 * e)
        if s == "neon":         # 辉光渐亮 / 辉光渐灭
            if kind == "enter":
                e = _ease_out_cubic(t)
                return int(255 * e), 0.94 + 0.06 * e, 0, 0
            e = _ease_out_cubic(t)
            return int(255 * (1 - e)), 1 - 0.1 * e, 0, 0
        # pixel：方块式阶跃显现 / 阶跃消失
        if kind == "enter":
            steps = 5.0
            q = math.ceil(t * steps) / steps
        else:
            steps = 4.0
            q = math.floor((1 - t) * steps) / steps
        return int(255 * q), 0.5 + 0.5 * q, 0, 0

    # ------------------------------------------------------------------
    # 文字
    # ------------------------------------------------------------------
    def _wrap_text(self, text):
        if not self.max_width:
            return text.split("\n")
        lines = []
        for para in text.split("\n"):
            words = para.split(" ")
            cur = ""
            for w in words:
                trial = (cur + " " + w).strip()
                if self.font.size(trial)[0] <= self.max_width:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
        return lines or [""]

    def _draw_text(self):
        if not self.text_lines:
            return
        line_h = self.text_lines[0].get_height()
        total_h = line_h * len(self.text_lines) + self.line_spacing * (len(self.text_lines) - 1)
        y = self.body_rect.centery - total_h // 2
        for ln in self.text_lines:
            x = self.body_rect.centerx - ln.get_width() // 2
            self.surf.blit(ln, (x, y))
            y += line_h + self.line_spacing

    # ------------------------------------------------------------------
    # 主体绘制（各风格分发）
    # ------------------------------------------------------------------
    def _draw_body(self):
        r = self.body_rect
        s = self.style
        if s == "classic":
            self._rounded(r, self.bg_color, self.radius,
                          self.border_color, self.border_width)
        elif s == "speech":
            self._rounded(r, self.bg_color, self.radius,
                          self.border_color, self.border_width)
            inner = r.inflate(-self.border_width * 4, -self.border_width * 4)
            self._rounded(inner, None, max(4, self.radius - self.border_width * 2),
                          self.border_color, self.border_width)
        elif s == "thought":
            self._draw_cloud(r)
        elif s == "burst":
            self._draw_burst(r)
        elif s == "banner":
            self._draw_banner(r)
        elif s == "chat":
            self._rounded(r, self.bg_color, self.radius,
                          self.border_color, self.border_width)
        elif s == "neon":
            self._draw_neon(r)
        elif s == "pixel":
            self._draw_pixel_body(r)

    def _rounded(self, rect, color, radius, border=None, border_w=0):
        radius = max(0, min(radius, rect.w // 2, rect.h // 2))
        if color is not None:
            pg.draw.rect(self.surf, color, rect, border_radius=radius)
        if border is not None and border_w > 0:
            pg.draw.rect(self.surf, border, rect, width=border_w, border_radius=radius)

    def _draw_cloud(self, r):
        """思考气泡主体：圆角矩形 + 顶部两个鼓包，形成云朵轮廓。"""
        cx = r.centerx
        bump = max(8, r.h // 3)
        dx = int(r.w * 0.22)
        pg.draw.rect(self.surf, self.bg_color, r, border_radius=self.radius)
        for bx in (cx - dx, cx + dx):
            pg.draw.circle(self.surf, self.bg_color, (bx, r.top), bump)
        if self.border_color is not None and self.border_width > 0:
            pg.draw.rect(self.surf, self.border_color, r,
                         width=self.border_width, border_radius=self.radius)
            # 只描鼓包的上半圆弧，避免内部出现干扰线
            for bx in (cx - dx, cx + dx):
                arc_rect = pg.Rect(bx - bump, r.top - bump, bump * 2, bump * 2)
                pg.draw.arc(self.surf, self.border_color, arc_rect,
                            math.pi, 2 * math.pi, self.border_width)

    def _draw_burst(self, r):
        """惊呼气泡：锯齿星形爆炸。"""
        cx, cy = r.centerx, r.centery
        rx, ry = r.w / 2.0, r.h / 2.0
        n = 12  # 尖角数量
        points = []
        for i in range(n * 2):
            angle = math.pi * i / n
            k = 1.0 if i % 2 == 0 else 0.72
            points.append((cx + math.cos(angle) * rx * k,
                           cy + math.sin(angle) * ry * k))
        pg.draw.polygon(self.surf, self.bg_color, points)
        if self.border_color is not None and self.border_width > 0:
            pg.draw.polygon(self.surf, self.border_color, points,
                            width=self.border_width)

    def _draw_banner(self, r):
        """缎带横幅：两端斜切燕尾 + 顶部高光。"""
        notch = min(20, r.h // 2)
        x, y, w, h = r
        pts = [(x + notch, y), (x + w - notch, y), (x + w, y + h // 2),
               (x + w - notch, y + h), (x + notch, y + h), (x, y + h // 2)]
        pg.draw.polygon(self.surf, self.bg_color, pts)
        if self.border_color is not None and self.border_width > 0:
            pg.draw.polygon(self.surf, self.border_color, pts,
                            width=self.border_width)
        # 顶部高光
        light = tuple(min(255, c + 45) for c in self.bg_color[:3])
        pg.draw.line(self.surf, light, (x + notch + 8, y + 4), (x + w - notch - 8, y + 4), 3)

    def _draw_neon(self, r):
        """霓虹气泡：多层由淡到亮的辉光描边。"""
        self._rounded(r, self.bg_color, self.radius)
        glow = self.glow_color
        steps = 8
        for i in range(steps, 0, -1):
            alpha = int(220 * ((i / steps) ** 2.2))
            infl = i * 3
            pg.draw.rect(self.surf, (*glow[:3], alpha),
                         r.inflate(infl * 2, infl * 2), width=max(1, i),
                         border_radius=self.radius + infl)
        # 亮芯描边
        pg.draw.rect(self.surf, glow, r, width=self.border_width,
                     border_radius=self.radius)

    def _draw_pixel_body(self, r):
        """像素气泡主体：硬边方块 + 四角断口，retro 括号感。"""
        pg.draw.rect(self.surf, self.bg_color, r)
        if self.border_color is not None and self.border_width > 0:
            pg.draw.rect(self.surf, self.border_color, r, width=self.border_width)
        # 四角用背景色方块"咬掉"边框 → 像素化断口
        s = 6
        for bx, by in ((r.left, r.top), (r.right - s, r.top),
                       (r.left, r.bottom - s), (r.right - s, r.bottom - s)):
            pg.draw.rect(self.surf, self.bg_color, (bx, by, s, s))

    # ------------------------------------------------------------------
    # 尾巴绘制
    # ------------------------------------------------------------------
    def _draw_tail(self):
        r = self.body_rect
        if self.style == "thought":
            self._thought_tail(r)
            return
        if self.style == "pixel":
            self._pixel_tail(r)
            return

        t = self.tail_size
        cx, cy = r.centerx, r.centery
        bc, bw = self.border_color, self.border_width

        if self.tail == TAIL_DOWN:
            pts = [(cx - t, r.bottom), (cx + t, r.bottom), (cx, r.bottom + t)]
            base = (cx - t, r.bottom, cx + t, r.bottom)
            diag = [((cx - t, r.bottom), (cx, r.bottom + t)),
                    ((cx + t, r.bottom), (cx, r.bottom + t))]
        elif self.tail == TAIL_UP:
            pts = [(cx - t, r.top), (cx + t, r.top), (cx, r.top - t)]
            base = (cx - t, r.top, cx + t, r.top)
            diag = [((cx - t, r.top), (cx, r.top - t)),
                    ((cx + t, r.top), (cx, r.top - t))]
        elif self.tail == TAIL_LEFT:
            pts = [(r.left, cy - t), (r.left, cy + t), (r.left - t, cy)]
            base = (r.left, cy - t, r.left, cy + t)
            diag = [((r.left, cy - t), (r.left - t, cy)),
                    ((r.left, cy + t), (r.left - t, cy))]
        else:  # RIGHT
            pts = [(r.right, cy - t), (r.right, cy + t), (r.right + t, cy)]
            base = (r.right, cy - t, r.right, cy + t)
            diag = [((r.right, cy - t), (r.right + t, cy)),
                    ((r.right, cy + t), (r.right + t, cy))]

        # 1) 尾巴填充
        pg.draw.polygon(self.surf, self.bg_color, pts)
        # 2) 主体（盖住尾巴与主体交界处的填充缝）
        self._draw_body()
        # 3) 尾巴两条斜边描边
        if bc is not None and bw > 0:
            for a, b in diag:
                pg.draw.line(self.surf, bc, a, b, bw)
            # 4) 擦除交界处的边框线，让尾巴与主体无缝衔接
            pg.draw.line(self.surf, self.bg_color, base[:2], base[2:], bw + 2)
        # 5) chat 风格圆润尾巴（在两个底角补圆）
        if self.style == "chat":
            rad = max(2, t // 3)
            if self.tail in (TAIL_DOWN, TAIL_UP):
                y = r.bottom if self.tail == TAIL_DOWN else r.top
                for dx in (-t, t):
                    pg.draw.circle(self.surf, self.bg_color, (cx + dx, y), rad)
            else:
                x = r.right if self.tail == TAIL_RIGHT else r.left
                for dy in (-t, t):
                    pg.draw.circle(self.surf, self.bg_color, (x, cy + dy), rad)

    def _thought_tail(self, r):
        """思考气泡尾巴：3 个渐变小圆。"""
        bc, bw = self.border_color, self.border_width
        th = self.tail_h
        sizes = [max(3, int(th * 0.3)), max(2, int(th * 0.22)), max(2, int(th * 0.13))]
        if self.tail == TAIL_DOWN:
            ys = [r.bottom + 3, r.bottom + th // 2, r.bottom + th - 4]
            pts = [(r.centerx, y) for y in ys]
        elif self.tail == TAIL_UP:
            ys = [r.top - 3, r.top - th // 2, r.top - th + 4]
            pts = [(r.centerx, y) for y in ys]
        elif self.tail == TAIL_LEFT:
            xs = [r.left - 3, r.left - th // 2, r.left - th + 4]
            pts = [(x, r.centery) for x in xs]
        else:
            xs = [r.right + 3, r.right + th // 2, r.right + th - 4]
            pts = [(x, r.centery) for x in xs]
        for (x, y), s in zip(pts, sizes):
            pg.draw.circle(self.surf, self.bg_color, (x, y), s)
            if bc is not None and bw > 0:
                pg.draw.circle(self.surf, bc, (x, y), s, width=bw)

    def _pixel_tail(self, r):
        """像素气泡尾巴：阶梯递减小方块。"""
        bc, bw = self.border_color, self.border_width
        th = self.tail_h
        sizes = [max(3, int(th * 0.55)), max(2, int(th * 0.35)), max(2, int(th * 0.2))]
        cx, cy = r.centerx, r.centery
        if self.tail == TAIL_DOWN:
            y = r.bottom
            for s in sizes:
                pg.draw.rect(self.surf, self.bg_color, (cx - s // 2, y, s, s))
                if bc is not None and bw > 0:
                    pg.draw.rect(self.surf, bc, (cx - s // 2, y, s, s), width=bw)
                y += s - 2
        elif self.tail == TAIL_UP:
            y = r.top - sizes[0]
            for s in sizes:
                pg.draw.rect(self.surf, self.bg_color, (cx - s // 2, y, s, s))
                if bc is not None and bw > 0:
                    pg.draw.rect(self.surf, bc, (cx - s // 2, y, s, s), width=bw)
                y += s - 2
        elif self.tail == TAIL_LEFT:
            x = r.left - sizes[0]
            for s in sizes:
                pg.draw.rect(self.surf, self.bg_color, (x, cy - s // 2, s, s))
                if bc is not None and bw > 0:
                    pg.draw.rect(self.surf, bc, (x, cy - s // 2, s, s), width=bw)
                x += s - 2
        else:
            x = r.right
            for s in sizes:
                pg.draw.rect(self.surf, self.bg_color, (x, cy - s // 2, s, s))
                if bc is not None and bw > 0:
                    pg.draw.rect(self.surf, bc, (x, cy - s // 2, s, s), width=bw)
                x += s - 2
