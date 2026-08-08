"""
demo_bubbles.py —— text_bubbles 模块演示

用法:
    python demo_bubbles.py                      # 交互演示
    python demo_bubbles.py --auto               # 自动循环播放出现/消失动画
    python demo_bubbles.py --save preview.png   # 渲染一帧静态预览图
    python demo_bubbles.py --anim out.gif       # 渲染出现/消失动画 GIF

交互键:
    空格  换文字并播放出现动画      H  全部隐藏(消失动画)
    S     全部显示(出现动画)       ESC 退出
    方向键 改尾巴方向并重播出现动画
"""

import sys
from io import BytesIO

import pygame as pg

import text_bubbles as tb

W, H = 1000, 680

TEXTS = [
    "经典圆角气泡",
    "漫画对话气泡",
    "思考一下…",
    "哇塞！太棒了!!",
    "直播间横幅",
    "新消息来啦~",
    "霓虹灯效Bubble",
    "像素风 8-BIT",
]


def _cjk(size):
    """找一个支持中文的字体。"""
    for name in ("microsoftyaheiui", "microsoftyahei", "simhei", "simsun",
                 "pingfangsc", "notosanscjk", "arialunicodems"):
        if pg.font.match_font(name):
            return pg.font.SysFont(name, size)
    return pg.font.Font(None, size)


def make_bubbles(text):
    bubbles = []
    for i, style in enumerate(tb.STYLES):
        bubbles.append(tb.TextBubble(text[i % len(text)], style=style,
                                     font=_cjk(24), tail="down",
                                     glow_color=(80, 210, 255)))
    return bubbles


def draw_frame(screen, bubbles, label_font, hint=None):
    screen.fill((24, 26, 34))
    cols, rows = 4, 2
    cw, ch = W // cols, H // rows
    for i, b in enumerate(bubbles):
        col, row = i % cols, i // cols
        cx = cw * col + cw // 2
        cy = ch * row + ch // 2 - 24
        b.anchor = "center"
        b.blit(screen, (cx, cy))
        lbl = label_font.render(tb.STYLES[i], True, (150, 160, 180))
        screen.blit(lbl, lbl.get_rect(center=(cx, ch * row + ch - 16)))
    if hint:
        h = label_font.render(hint, True, (120, 130, 150))
        screen.blit(h, (12, H - 30))


def save(path, text):
    pg.init()
    screen = pg.display.set_mode((W, H))
    label_font = _cjk(18)
    draw_frame(screen, make_bubbles(text), label_font)
    pg.image.save(screen, path)
    print(f"已保存预览图: {path}")
    pg.quit()


def main():
    pg.init()
    screen = pg.display.set_mode((W, H))
    pg.display.set_caption("text_bubbles 演示 — 空格:换文字  S:出现  H:消失  方向键:改尾巴  ESC:退出")
    clock = pg.time.Clock()
    label_font = _cjk(18)

    auto = "--auto" in sys.argv
    auto_timer = 0.0
    auto_phase = 0

    bubbles = make_bubbles(TEXTS)
    tail_dir = "down"
    text_idx = 0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    running = False
                    continue
                changed = False
                if e.key == pg.K_SPACE:
                    text_idx = (text_idx + 1) % len(TEXTS)
                    changed = True
                elif e.key == pg.K_UP:
                    tail_dir = tb.TAIL_UP; changed = True
                elif e.key == pg.K_DOWN:
                    tail_dir = tb.TAIL_DOWN; changed = True
                elif e.key == pg.K_LEFT:
                    tail_dir = tb.TAIL_LEFT; changed = True
                elif e.key == pg.K_RIGHT:
                    tail_dir = tb.TAIL_RIGHT; changed = True
                elif e.key in (pg.K_s, pg.K_RETURN):
                    for b in bubbles:
                        b.show()
                elif e.key == pg.K_h:
                    for b in bubbles:
                        b.hide()
                if changed:
                    for i, b in enumerate(bubbles):
                        b.text = TEXTS[(text_idx + i) % len(TEXTS)]
                        b.tail = tail_dir
                        b.rebuild()
                        b.show()

        # 自动演示：换文字出现 → 消失 → 再次出现，循环
        if auto:
            auto_timer += dt
            if auto_timer >= 2.8:
                auto_timer = 0.0
                auto_phase = (auto_phase + 1) % 3
                if auto_phase == 0:
                    text_idx = (text_idx + 1) % len(TEXTS)
                    for i, b in enumerate(bubbles):
                        b.text = TEXTS[(text_idx + i) % len(TEXTS)]
                        b.rebuild()
                        b.show()
                elif auto_phase == 1:
                    for b in bubbles:
                        b.hide()
                else:
                    for b in bubbles:
                        b.show()

        for b in bubbles:
            b.update(dt)

        hint = (f"空格:换文字  S:出现  H:消失  方向键:改尾巴({tail_dir})  ESC:退出"
                + ("  [自动演示中]" if auto else ""))
        draw_frame(screen, bubbles, label_font, hint)
        pg.display.flip()
    pg.quit()


def anim_gif(path):
    """渲染一个出现/消失循环动画 GIF，用于预览各风格动画效果。"""
    try:
        from PIL import Image
    except ImportError:
        print("需要 pillow 才能输出 GIF: pip install pillow")
        return
    pg.init()
    screen = pg.display.set_mode((W, H))
    label_font = _cjk(18)
    bubbles = make_bubbles(TEXTS)
    for b in bubbles:
        b.visible = False  # 初始隐藏

    fps = 30
    dt = 1.0 / fps
    cycle = 1.9          # 每个循环时长
    frames = []
    total = int(cycle * 2 * fps)   # 渲染两个循环
    t = 0.0
    for _ in range(total):
        t += dt
        tt = t % cycle
        for i, b in enumerate(bubbles):
            local = tt - i * 0.08   # 各气泡错开 0.08s 依次出现
            if local < 0:
                continue
            if local < 0.35:
                if not b.animating and not b.visible:
                    b.show()
            elif local < 0.85:
                if not b.animating and b.visible:
                    b.hide()
            b.update(dt)
        draw_frame(screen, bubbles, label_font)
        pg.display.flip()
        bio = BytesIO()
        pg.image.save(screen, bio, "PNG")
        bio.seek(0)
        frames.append(Image.open(bio).convert("RGBA"))
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=1000 // fps, loop=0)
    print(f"已保存动画: {path} ({len(frames)} 帧)")
    pg.quit()


if __name__ == "__main__":
    text = TEXTS
    if "--text" in sys.argv:
        text = [sys.argv[sys.argv.index("--text") + 1]] * len(TEXTS)
    if "--save" in sys.argv:
        save(sys.argv[sys.argv.index("--save") + 1], text)
    elif "--anim" in sys.argv:
        anim_gif(sys.argv[sys.argv.index("--anim") + 1])
    else:
        main()
