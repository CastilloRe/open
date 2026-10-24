# art/claude-face.webp: a "bare skin" copy of the face square (FACE in index.html), the eyes and the mouth
# filled in from the skin around them, transparent wherever hair crosses the face.
#   python3 face-plate.py shot.png ../art/claude-face.webp preview.png   (shot.png: from face-plate.html)
import sys
import numpy as np
from PIL import Image
src, out, preview = sys.argv[1:4]
im = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255
im = im[:512]
A, INFO = im[:, :512], im[:, 512:1024]
N, X0, Y0, SIZE = 512, -0.115, 0.64, 0.21
px = (np.arange(N) + 0.5) / N
X = X0 + px[None, :] * SIZE + np.zeros((N, 1))
Y = Y0 + SIZE - px[:, None] * SIZE + np.zeros((1, N))
z, nz = INFO[..., 0] * 0.2, INFO[..., 1] * 2 - 1
EYES = [(-0.0695, 0.759, 0.029, 0.784, 0.736, -1), (0.0375, 0.769, 0.026, 0.794, 0.745, 1)]
M = dict(x=-0.0065, y=0.715, hw=0.014, hh=0.0095)
U = np.zeros((N, N), bool)
for cx, cy, hw, top, bot, out_ in EYES:
    # wider toward the outer corner, where the lashes flick out
    ccx = cx + out_ * 0.006
    rx, ry_up, ry_dn = hw + 0.018, top + 0.014 - cy, cy - bot + 0.006
    dx = (X - ccx) / rx
    dy = np.where(Y > cy, (Y - cy) / ry_up, (cy - Y) / ry_dn)
    U |= dx * dx + dy * dy < 1
dx, dy = (X - M['x']) / (M['hw'] + 0.009), (Y - M['y']) / (M['hh'] + 0.008)
U |= dx * dx + dy * dy < 1
mx, mn = A.max(-1), A.min(-1)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-5), 0)
skin = (sat < 0.3) & (mx > 0.72) & (z > 0.04) & (z < 0.112) & (nz > 0.15)
K = skin & ~U
# normalized convolution with box blurs of growing size: each hole pixel takes the average of the nearest known skin
def box(a, r):
    c = np.cumsum(np.cumsum(np.pad(a, ((r + 1, r), (r + 1, r)) + ((0, 0),) * (a.ndim - 2)), 0), 1)
    return c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]
fill = np.zeros_like(A); done = np.zeros((N, N), bool)
w = K.astype(np.float32)
for r in (3, 6, 10, 16, 24, 36, 54, 80, 140, 260):
    num = box(A * w[..., None], r); den = box(w, r)
    ok = (den > 0.5) & ~done & U
    fill[ok] = num[ok] / den[ok, None]
    done |= ok
# smooth the fill a little so it has no blocky steps
sm = box(fill * done[..., None], 4) / np.maximum(box(done.astype(np.float32), 4), 1e-5)[..., None]
plate = np.where(U[..., None], sm, A)
# which pixels are her face at all: fit a smooth surface to the skin's depth; inside the holes, whatever
# sits on that surface is face (eye, lashes, mouth), and anything well in front of or behind it is hair
ks = K & (np.abs(X + 0.015) < 0.09) & (Y > 0.69) & (Y < 0.8)
F = lambda x, y: np.stack([np.ones_like(x), x, y, x * x, y * y, x * y], -1)
coef, *_ = np.linalg.lstsq(F(X[ks], Y[ks]), z[ks], rcond=None)
dev = z - F(X, Y) @ coef
# eyes and the open mouth sit a little inside the head, so only "in front of the surface" rules a pixel out;
# beside the eyes, orange is hair
tight = np.zeros((N, N), bool)
for cx, cy, hw, top, bot, out_ in EYES:
    dx = (X - cx) / (hw + 0.004); dy = np.where(Y > cy, (Y - cy) / (top - cy), (cy - Y) / (cy - bot + 0.008))
    tight |= dx * dx + dy * dy < 1
hue = np.where(mx == A[..., 0], ((A[..., 1] - A[..., 2]) / np.maximum(mx - mn, 1e-5)) % 6, 3) * 60
hair = (sat > 0.42) & (mx > 0.5) & (hue > 8) & (hue < 40)
dx, dy = (X - M['x']) / (M['hw'] + 0.003), (Y - M['y']) / (M['hh'] + 0.003)
tight |= dx * dx + dy * dy < 1
# lashes stand out from the face a little; the bangs stand out further and are orange
face = K | (U & (nz > -0.3) & np.where(hair, tight & (dev < 0.012), dev < 0.022))
alpha = box(face.astype(np.float32), 1) / 9
rgba = np.concatenate([np.clip(plate, 0, 1), alpha[..., None]], -1)
Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA').save(out, quality=92, method=6)
print('fit residual on skin', float(np.abs(dev[ks]).mean()))
prev = np.concatenate([A, plate * alpha[..., None], np.repeat(face[..., None], 3, -1) * 0.8 + np.repeat(U[..., None], 3, -1) * 0.2], 1)
Image.fromarray((np.clip(prev, 0, 1) * 255).astype(np.uint8)).save(preview)
print('holes', U.sum(), 'unfilled', (U & ~done).sum())
