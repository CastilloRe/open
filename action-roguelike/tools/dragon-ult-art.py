"""The dragon illustration for 此即，最优解, exactly as drawn: its own pixels, ink and paper, untouched; only the paper far
from the drawing is let go. How much ink each pixel holds is found against the paper round it (the brightest nearby,
smoothed); the paper stays where there is ink near it, as a pale cloud round the dragon that fades out away from it.

    python3 -I dragon-ult-art.py <in.png> <out.webp>

The result is the sheet with a 90 px margin of paper round it (DRAGON_ART in index.html counts it).
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

src, out = sys.argv[1], sys.argv[2]
PAD = 90
orig = Image.open(src).convert('RGB')
# a margin of plain paper all round, so the cloud can fade out past the edges of the sheet instead of stopping at them
im = Image.new('RGB', (orig.width + 2 * PAD, orig.height + 2 * PAD), tuple(int(v) for v in np.median(np.asarray(orig).reshape(-1, 3), 0)))
im.paste(orig, (PAD, PAD))
a = np.asarray(im).astype(np.float32)
paper = np.stack([np.asarray(Image.fromarray(a[..., c].astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(12))).astype(np.float32) for c in range(3)], -1)
ink = np.clip((np.clip(paper - a, 0, None).max(-1) - 14) / 100, 0, 1)
blur = lambda m, r: np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255
# where the drawing is: its ink spread wide, then eased so the cloud is solid near the lines and soft at its rim
near = blur(blur(blur(ink, 6) * 6, 30) * 2.4, 34)
cloud = np.clip(near * 1.9, 0, 1) ** 1.6
alpha = np.maximum(ink, cloud * 0.9)
res = Image.fromarray(np.dstack([a, alpha * 255]).astype(np.uint8), 'RGBA')
res.save(out, 'WEBP', quality=82, method=6)
print('size', res.size)
