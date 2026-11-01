"""The dragon illustration for 此即，最优解, off its paper and lit for the night: the paper estimated locally (the brightest
nearby, smoothed) and taken away, how much ink each pixel holds becoming its alpha; the blue ink turned to a pale
lilac light and the gold ink to a bright, saturated gold (lifted, since gold ink is paler than the blue), with a soft
glow baked in round every line, golden round the gold and violet round the rest.

    python3 -I dragon-ult-art.py <in.png> <out.webp>
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB')
a = np.asarray(im).astype(np.float32)
# the paper, wherever it is: the lines are thin, so the brightest pixel within 9 px is paper; smoothed after
paper = np.stack([np.asarray(Image.fromarray(a[..., c].astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(12))).astype(np.float32) for c in range(3)], -1)
diff = np.clip(paper - a, 0, None).max(-1)
ink = np.clip((diff - 14) / 100, 0, 1) ** 0.85
# gold where red is well above blue, blue ink otherwise
gold = np.clip((a[..., 0] - a[..., 2] - 16) / 36, 0, 1) * (ink > 0.05)
# gold ink is paler than the blue, so it is lifted to light up as strongly
ink = np.clip(ink * (1 + 0.9 * gold), 0, 1)
lilac = np.array([214, 204, 255], np.float32)
warm = np.array([255, 190, 50], np.float32)
line = lilac * (1 - gold[..., None]) + warm * gold[..., None]
# the strongest lilac strokes go nearly white; the gold stays gold
line = line + (255 - line) * (ink[..., None] ** 2) * 0.45 * (1 - gold[..., None])
blur = lambda m: np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7))).astype(np.float32) / 255
glow = np.clip(blur(ink) * 1.6, 0, 1) * 0.42
# the glow takes the colour of the lines it comes from: golden round the gold
gglow = np.clip(blur(ink * gold) / np.maximum(blur(ink), 1e-3), 0, 1)
glowc = np.array([168, 120, 255], np.float32) * (1 - gglow[..., None]) + np.array([255, 160, 30], np.float32) * gglow[..., None]
alpha = np.clip(ink + glow * (1 - ink), 0, 1)
rgb = (line * ink[..., None] + glowc * (glow * (1 - ink))[..., None]) / np.maximum(alpha[..., None], 1e-4)
rgba = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
res = Image.fromarray(rgba, 'RGBA')
# trimmed to the drawing, with a margin
bb = Image.fromarray((alpha > 0.04).astype(np.uint8) * 255).getbbox()
m = 12
box = (max(0, bb[0] - m), max(0, bb[1] - m), min(im.width, bb[2] + m), min(im.height, bb[3] + m))
res = res.crop(box)
res.save(out, 'WEBP', quality=80, method=6)
print('box', box, 'size', res.size)
