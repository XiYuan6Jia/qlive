# -*- coding: utf-8 -*-
"""从 icon.ico 提取源图，中心裁剪为正方形并缩放到 256x256，重存为多尺寸 ICO。"""
from PIL import Image
import os

BASE = os.path.dirname(os.path.abspath(__file__))   # build/
ROOT = os.path.dirname(BASE)                        # 项目根
SRC = os.path.join(ROOT, "icon.ico")

TARGET = 256
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main():
    im = Image.open(SRC)
    im.seek(0)
    rgba = im.convert("RGBA")
    w, h = rgba.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    square = rgba.crop((left, top, left + side, top + side))
    main_img = square.resize((TARGET, TARGET), Image.LANCZOS)

    # 备份旧图标
    bak = os.path.join(BASE, "icon_old_backup.ico")
    if not os.path.exists(bak):
        im.save(bak)
        print("backup ->", bak)
    im.close()  # 释放原文件句柄，避免覆盖失败

    # 先写临时文件再替换（Windows 下目标文件可能被占用）
    tmp = SRC + ".tmp"
    main_img.save(tmp, format="ICO", sizes=SIZES)
    os.replace(tmp, SRC)
    print("saved:", SRC, os.path.getsize(SRC), "bytes")
    print("sizes:", Image.open(SRC).info.get("sizes"))


if __name__ == "__main__":
    main()
