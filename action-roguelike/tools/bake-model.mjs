// Turns the Tripo export of 克劳德大小姐 into art/claude.glb:
// faces +Z, feet on y = 0, body axis on x = z = 0, smaller textures,
// and a _REGION attribute (legL, legR, arm, hair weights) for the vertex-shader animation.
// The joint heights here have to agree with MODEL_JOINTS in index.html.
//
//   npm i @gltf-transform/cli@4.1.1 @gltf-transform/core@4.1.1 sharp
//   npx gltf-transform weld tripo.glb welded.glb                       # also decodes Draco
//   npx gltf-transform simplify welded.glb simple.glb --ratio 0.03 --error 0.01
//   node bake-model.mjs simple.glb ../art/claude.glb [regions.glb]     # regions.glb paints the weights as colours
import { NodeIO, Accessor } from '@gltf-transform/core';
import sharp from 'sharp';

const [src, out, debugOut] = process.argv.slice(2);
if (!src || !out) { console.error('usage: node bake-model.mjs simple.glb out.glb [regions.glb]'); process.exit(1); }
const io = new NodeIO();
const doc = await io.read(src);
const prim = doc.getRoot().listMeshes()[0].listPrimitives()[0];
const P = prim.getAttribute('POSITION'), N = prim.getAttribute('NORMAL'), UV = prim.getAttribute('TEXCOORD_0');
const pos = P.getArray(), nor = N.getArray(), uv = UV.getArray();
const n = pos.length / 3;

// old model faces +X with feet at y = -0.4903; the body axis sits at old (x, z) = (0.035, -0.007)
const Y0 = -0.4903, CX = 0.035, CZ = -0.007;
for (let i = 0; i < n; i++) {
  const x = pos[i * 3], y = pos[i * 3 + 1], z = pos[i * 3 + 2];
  pos[i * 3] = -(z - CZ); pos[i * 3 + 1] = y - Y0; pos[i * 3 + 2] = x - CX;
  const nx = nor[i * 3], nz = nor[i * 3 + 2];
  nor[i * 3] = -nz; nor[i * 3 + 2] = nx;
}
P.setArray(pos); N.setArray(nor);

// sample the base colour under each vertex
const mat = prim.getMaterial();
const colTex = mat.getBaseColorTexture();
const { data: px, info } = await sharp(Buffer.from(colTex.getImage())).raw().toBuffer({ resolveWithObject: true });
const sample = (u, v) => {
  const x = Math.min(info.width - 1, Math.max(0, Math.floor(u * info.width)));
  const y = Math.min(info.height - 1, Math.max(0, Math.floor(v * info.height)));
  const o = (y * info.width + x) * info.channels;
  return [px[o] / 255, px[o + 1] / 255, px[o + 2] / 255];
};
const sstep = (a, b, v) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
const hsv = ([r, g, b]) => {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d > 1e-5) h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [(h * 60 + 360) % 360, mx > 0 ? d / mx : 0, mx];
};

// [x, y, z, radius] at shoulder, wrist and fingertips
const ARM_R = [[0.1, 0.605, 0.01, 0.07], [0.205, 0.485, 0.005, 0.045], [0.258, 0.425, -0.02, 0.052]];
const ARM_L = [[-0.1, 0.605, 0.01, 0.07], [-0.215, 0.485, 0.005, 0.045], [-0.276, 0.435, -0.02, 0.052]];
const region = new Uint8Array(n * 4);
const stats = { legL: 0, legR: 0, arm: 0, hair: 0 };
for (let i = 0; i < n; i++) {
  const x = pos[i * 3], y = pos[i * 3 + 1], z = pos[i * 3 + 2];
  const [h, s, v] = hsv(sample(uv[i * 2], uv[i * 2 + 1]));
  const orange = h > 5 && h < 45 && s > 0.42 && v > 0.35 ? 1 : 0;
  // legs: everything below the skirt hem, split down the middle
  const leg = sstep(0.226, 0.205, y);
  const legL = x < 0 ? leg : 0, legR = x >= 0 ? leg : 0;
  // arms: a tapered capsule from shoulder to wrist to fingertips;
  // the weight fades in from the shoulder so the sleeve bends instead of tearing
  const ARM = x < 0 ? ARM_L : ARM_R;
  let best = 9, along = 0;
  for (let k = 0; k < 2; k++) {
    const a = ARM[k], b = ARM[k + 1];
    const abx = b[0] - a[0], aby = b[1] - a[1], abz = b[2] - a[2];
    const t = Math.min(1, Math.max(0, ((x - a[0]) * abx + (y - a[1]) * aby + (z - a[2]) * abz) / (abx * abx + aby * aby + abz * abz)));
    const d = Math.hypot(x - a[0] - abx * t, y - a[1] - aby * t, z - a[2] - abz * t) - (a[3] + (b[3] - a[3]) * t);
    if (d < best) { best = d; along = k + t; }
  }
  // a soft edge: skirt and hair touching the arm give a little with it instead of tearing away
  const arm = (1 - 0.7 * orange) * sstep(0.05, -0.006, best) * sstep(0.06, 0.32, along);
  // hair: orange, above the hem, mostly behind or beside her head
  const hair = orange * sstep(0.36, 0.42, y) * Math.max(sstep(0.0, -0.06, z), sstep(0.14, 0.18, Math.abs(x)));
  region[i * 4] = Math.round(legL * 255); region[i * 4 + 1] = Math.round(legR * 255);
  region[i * 4 + 2] = Math.round(arm * 255); region[i * 4 + 3] = Math.round(hair * 255);
  if (legL > 0.5) stats.legL++; if (legR > 0.5) stats.legR++; if (arm > 0.5) stats.arm++; if (hair > 0.5) stats.hair++;
}
console.log('vertices', n, stats);

// the eyes sit in hollows with sculpted lashes standing out of them, and the mouth is a hole; the game paints
// its own lids, lashes and mouths over them (FACE in index.html), which only reads on a smooth surface. So
// press eyes, lashes and mouth flat onto "the face", a smooth surface fitted to the skin around the eyes:
// z = a + b x + c y + d x² + e y² + f x y. Her painted eyes and mouth stay as they are, just level with the skin.
const EYES = [[-0.0695, 0.759, 0.029, 0.784, 0.736, -1], [0.0375, 0.769, 0.026, 0.794, 0.745, 1]];
const MOUTH = [-0.0065, 0.715, 0.014, 0.0095];
const terms = (x, y) => [1, x, y, x * x, y * y, x * y];
{
  const AtA = Array.from({ length: 6 }, () => new Float64Array(6)), Atb = new Float64Array(6);
  for (let i = 0; i < n; i++) {
    const x = pos[i * 3], y = pos[i * 3 + 1], z = pos[i * 3 + 2];
    if (Math.abs(x + 0.015) > 0.09 || y < 0.69 || y > 0.8 || z < 0.04 || z > 0.112 || nor[i * 3 + 2] < 0.15) continue;
    const [, s, v] = hsv(sample(uv[i * 2], uv[i * 2 + 1]));
    if (s > 0.3 || v < 0.72) continue;
    const t = terms(x, y);
    for (let a = 0; a < 6; a++) { Atb[a] += t[a] * z; for (let b = 0; b < 6; b++) AtA[a][b] += t[a] * t[b]; }
  }
  // Gaussian elimination
  const M = AtA.map((r, a) => [...r, Atb[a]]);
  for (let c = 0; c < 6; c++) {
    let p = c; for (let r = c + 1; r < 6; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    for (let r = 0; r < 6; r++) if (r !== c) { const f = M[r][c] / M[c][c]; for (let k = c; k < 7; k++) M[r][k] -= f * M[c][k]; }
  }
  const coef = M.map((r, a) => r[6] / r[a]);
  const fit = (x, y) => terms(x, y).reduce((acc, t, a) => acc + t * coef[a], 0);
  let flat = 0;
  for (let i = 0; i < n; i++) {
    const x = pos[i * 3], y = pos[i * 3 + 1], z = pos[i * 3 + 2];
    if (x < -0.13 || x > 0.11 || y < 0.66 || y > 0.83) continue;
    const dev = z - fit(x, y), [h, sat, v] = hsv(sample(uv[i * 2], uv[i * 2 + 1]));
    // the orange bangs hang in front of the face and stay; the back of the head is far behind
    const orange = h > 5 && h < 45 && sat > 0.42 && v > 0.5;
    if (dev > 0.03 || dev < -0.04 || (orange && dev > 0.008)) continue;
    // how far into an eye or the mouth (1 inside, fading out just past the edge)
    let r = 9;
    for (const [cx, cy, hw, top, bot, out] of EYES) {
      const dx = (x - cx - out * 0.006) / (hw + 0.02), dy = y > cy ? (y - cy) / (top + 0.016 - cy) : (cy - y) / (cy - bot + 0.012);
      r = Math.min(r, Math.hypot(dx, dy));
    }
    r = Math.min(r, Math.hypot((x - MOUTH[0]) / (MOUTH[2] + 0.01), (y - MOUTH[1]) / (MOUTH[3] + 0.009)));
    const press = sstep(1.3, 1.0, r);
    if (press > 0) { pos[i * 3 + 2] = z - dev * press + 0.0005 * press; flat++; }
    // light the whole face as one smooth surface, fading back to the model's own normals at its edges
    const smooth = Math.max(press, (orange ? 0 : 1) * sstep(0.105, 0.08, Math.abs(x + 0.015)) * sstep(0.68, 0.7, y) * sstep(0.815, 0.795, y) * sstep(0.012, 0.006, Math.abs(dev)));
    if (smooth > 0) {
      const gx = coef[1] + 2 * coef[3] * x + coef[5] * y, gy = coef[2] + 2 * coef[4] * y + coef[5] * x, l = Math.hypot(gx, gy, 1);
      const nx = nor[i * 3] + (-gx / l - nor[i * 3]) * smooth, ny = nor[i * 3 + 1] + (-gy / l - nor[i * 3 + 1]) * smooth, nz = nor[i * 3 + 2] + (1 / l - nor[i * 3 + 2]) * smooth;
      const m = Math.hypot(nx, ny, nz) || 1;
      nor[i * 3] = nx / m; nor[i * 3 + 1] = ny / m; nor[i * 3 + 2] = nz / m;
    }
  }
  P.setArray(pos); N.setArray(nor);
  console.log('eye and mouth vertices pressed flat', flat);
}
const acc = doc.createAccessor('region').setType(Accessor.Type.VEC4).setArray(region).setNormalized(true).setBuffer(doc.getRoot().listBuffers()[0]);
prim.setAttribute('_REGION', acc);

// smaller textures: colour stays 1K, the normal and ORM maps drop to 512, all as JPEG
async function shrink(tex, size, q) {
  if (!tex) return;
  const img = await sharp(Buffer.from(tex.getImage())).resize(size, size).jpeg({ quality: q, mozjpeg: true }).toBuffer();
  tex.setImage(new Uint8Array(img)).setMimeType('image/jpeg').setURI('');
}
await shrink(colTex, 1024, 86);
await shrink(mat.getNormalTexture(), 512, 90);
await shrink(mat.getMetallicRoughnessTexture(), 512, 85);
mat.setName('claude');
doc.getRoot().listMeshes()[0].setName('claude');
doc.getRoot().listNodes()[0].setName('claude');

await io.write(out, doc);

if (debugOut) {
  // a copy that shows the regions as vertex colours instead of the texture
  const dbg = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) {
    const l = (region[i * 4] + region[i * 4 + 1]) / 255, a = region[i * 4 + 2] / 255, hr = region[i * 4 + 3] / 255;
    dbg[i * 4] = 0.3 + 0.7 * Math.max(a, hr); dbg[i * 4 + 1] = 0.3 + 0.7 * l; dbg[i * 4 + 2] = 0.3 + 0.7 * Math.max(a, region[i * 4] / 255); dbg[i * 4 + 3] = 1;
  }
  prim.setAttribute('COLOR_0', doc.createAccessor('dbg').setType('VEC4').setArray(dbg).setBuffer(doc.getRoot().listBuffers()[0]));
  await io.write(debugOut, doc);
}
