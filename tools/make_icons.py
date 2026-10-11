# -*- coding: utf-8 -*-
"""숙제 아이콘 (연필 + 줄 공책) → icon-192.png, icon-512.png, apple-touch-icon.png
쓰는 법: python tools/make_icons.py   (Pillow 필요)"""
import os
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def make(S, name):
    k = 4; W = S * k; u = W / 100
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y in range(W):                                  # 배경: 주황 그라데이션 (maskable: 가득 채움)
        t = y / W; d.line([(0, y), (W, y)], fill=(int(234 - 30 * t), int(108 - 40 * t), int(40 - 20 * t), 255))
    d.rounded_rectangle([24 * u, 22 * u, 72 * u, 78 * u], radius=6 * u, fill=(255, 250, 242, 255))      # 공책
    for i, y in enumerate((38, 50, 62)):
        d.line([(32 * u, y * u), ((64 if i < 2 else 50) * u, y * u)], fill=(214, 196, 178, 255), width=int(3 * u))
    d.line([(32 * u, 30 * u), (56 * u, 30 * u)], fill=(194, 65, 12, 255), width=int(4 * u))
    # 연필 (대각선)
    pen = Image.new("RGBA", (W, W), (0, 0, 0, 0)); p = ImageDraw.Draw(pen)
    cx, cy, L, T = 50 * u, 50 * u, 46 * u, 9 * u
    p.rectangle([cx - L / 2, cy - T / 2, cx + L / 2 - 10 * u, cy + T / 2], fill=(255, 196, 0, 255))
    p.rectangle([cx - L / 2, cy - T / 2, cx - L / 2 + 6 * u, cy + T / 2], fill=(255, 140, 160, 255))
    p.polygon([(cx + L / 2 - 10 * u, cy - T / 2), (cx + L / 2, cy), (cx + L / 2 - 10 * u, cy + T / 2)], fill=(245, 222, 179, 255))
    p.polygon([(cx + L / 2 - 3.5 * u, cy - 1.6 * u), (cx + L / 2, cy), (cx + L / 2 - 3.5 * u, cy + 1.6 * u)], fill=(60, 50, 40, 255))
    pen = pen.rotate(40, center=(cx, cy), resample=Image.BICUBIC).transform((W, W), Image.AFFINE, (1, 0, -10 * u, 0, 1, -8 * u))
    im.alpha_composite(pen)
    im.resize((S, S), Image.LANCZOS).save(os.path.join(OUT, name))
make(192, "icon-192.png"); make(512, "icon-512.png"); make(180, "apple-touch-icon.png")
print("ok")
