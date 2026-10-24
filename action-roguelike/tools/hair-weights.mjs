// Recomputes the hair channel (w) of _REGION in art/claude.glb so her hair can swing without tearing:
//   1. hair-coloured (orange) vertices from the hem up, except the bangs and the front of the dress
//   2. only the ones joined, through other hair-coloured vertices, to the hair on the back of her head;
//      the orange bows and skirt panels are not
//   3. small specks inside the hair that missed the colour test (highlights, dark strands) are filled in
//   4. the weight fades in from the edge of the hair over a few centimetres measured along the surface,
//      so a lock that swings bends away from the dress instead of stretching off it
// Run it where @gltf-transform/core, @gltf-transform/extensions, meshoptimizer and sharp are installed:
//   node hair-weights.mjs art/claude.glb art/claude.glb
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';

const [src, out] = process.argv.slice(2);
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read(src);
const node = doc.getRoot().listNodes()[0], prim = doc.getRoot().listMeshes()[0].listPrimitives()[0];
const T = node.getTranslation(), S = node.getScale()[0];
const P = prim.getAttribute('POSITION'), UV = prim.getAttribute('TEXCOORD_0'), R = prim.getAttribute('_REGION');
const n = P.getCount(), pos = new Float32Array(n * 3), e = [0, 0, 0], uv = [0, 0];
for (let i = 0; i < n; i++) { P.getElement(i, e); for (let k = 0; k < 3; k++) pos[i * 3 + k] = e[k] * S + T[k]; }

// hair-coloured vertices
const { data: px, info } = await sharp(Buffer.from(prim.getMaterial().getBaseColorTexture().getImage())).raw().toBuffer({ resolveWithObject: true });
const orange = new Uint8Array(n);
for (let i = 0; i < n; i++) {
  UV.getElement(i, uv);
  const x = Math.min(info.width - 1, Math.max(0, Math.floor(uv[0] * info.width))), y = Math.min(info.height - 1, Math.max(0, Math.floor(uv[1] * info.height)));
  const o = (y * info.width + x) * info.channels, r = px[o] / 255, g = px[o + 1] / 255, b = px[o + 2] / 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0;
  if (d > 1e-5) h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  h = (h * 60 + 360) % 360;
  orange[i] = h > 5 && h < 45 && mx > 0.35 && d / mx > 0.42 ? 1 : 0;
}

// neighbours along the mesh's edges. The texture seams split it into some 1,700 pieces with their own copies of
// the vertices along each seam; copies at the same spot are treated as one vertex, so the hair is traced across
// seams and both sides of a seam get the same weight (otherwise the seam would open when the hair moves)
const raw = P.getArray(), first = new Map(), rep = new Int32Array(n);
for (let i = 0; i < n; i++) { const k = raw[i * 3] + ',' + raw[i * 3 + 1] + ',' + raw[i * 3 + 2]; if (!first.has(k)) first.set(k, i); rep[i] = first.get(k); }
for (let i = 0; i < n; i++) orange[rep[i]] = Math.max(orange[rep[i]], orange[i]);
const idx = prim.getIndices().getArray();
const nb = Array.from({ length: n }, () => new Set());
for (let t = 0; t < idx.length; t += 3) for (let k = 0; k < 3; k++) { const a = rep[idx[t + k]], b = rep[idx[t + (k + 1) % 3]]; if (a !== b) { nb[a].add(b); nb[b].add(a); } }
const isRep = i => rep[i] === i;
const len = (a, b) => Math.hypot(pos[a * 3] - pos[b * 3], pos[a * 3 + 1] - pos[b * 3 + 1], pos[a * 3 + 2] - pos[b * 3 + 2]);
const X = i => pos[i * 3], Y = i => pos[i * 3 + 1], Z = i => pos[i * 3 + 2];

// 1-2: hair-coloured, above the hem, not the bangs or the front of the dress, joined to the back of her head
const cand = i => orange[i] && Y(i) > 0.24 && (Z(i) < 0.02 || Math.abs(X(i)) > 0.13);
const hair = new Uint8Array(n), queue = [];
for (let i = 0; i < n; i++) if (isRep(i) && cand(i) && Y(i) > 0.72 && Z(i) < -0.04) { hair[i] = 1; queue.push(i); }
for (let q = 0; q < queue.length; q++) for (const j of nb[queue[q]]) if (!hair[j] && cand(j)) { hair[j] = 1; queue.push(j); }

// 3: fill specks of non-hair enclosed by hair
const seen = new Uint8Array(n);
let filled = 0;
for (let i = 0; i < n; i++) {
  if (!isRep(i) || hair[i] || seen[i]) continue;
  const comp = [i];
  let touches = false;
  seen[i] = 1;
  for (let q = 0; q < comp.length; q++) for (const j of nb[comp[q]]) { if (hair[j]) touches = true; else if (!seen[j]) { seen[j] = 1; comp.push(j); } }
  if (touches && comp.length <= 40) { for (const j of comp) hair[j] = 1; filled += comp.length; }
}

// 4: distance along the surface from the nearest non-hair vertex, then a smooth ramp
const FADE = 0.035;
const dist = new Float32Array(n).fill(Infinity);
const heap = [];
const push = (d, i) => { heap.push([d, i]); let c = heap.length - 1; while (c > 0) { const p = (c - 1) >> 1; if (heap[p][0] <= heap[c][0]) break; [heap[p], heap[c]] = [heap[c], heap[p]]; c = p; } };
const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let c = 0; for (;;) { const l = c * 2 + 1, r = l + 1; let m = c; if (l < heap.length && heap[l][0] < heap[m][0]) m = l; if (r < heap.length && heap[r][0] < heap[m][0]) m = r; if (m === c) break; [heap[m], heap[c]] = [heap[c], heap[m]]; c = m; } } return top; };
for (let i = 0; i < n; i++) if (isRep(i) && !hair[i]) { dist[i] = 0; push(0, i); }
while (heap.length) {
  const [d, i] = pop();
  if (d > dist[i] || d > FADE) continue;
  for (const j of nb[i]) { const dj = d + len(i, j); if (dj < dist[j]) { dist[j] = dj; push(dj, j); } }
}
const reg = R.getArray(), bands = {};
for (let i = 0; i < n; i++) {
  const t = Math.min(1, dist[rep[i]] / FADE), w = t * t * (3 - 2 * t);
  reg[i * 4 + 3] = Math.round(w * 255);
  const b = (Math.floor(Y(i) * 10) / 10).toFixed(1);
  bands[b] = bands[b] || [0, 0];
  bands[b][0]++; if (w > 0.5) bands[b][1]++;
}
R.setArray(reg);
console.log('separate vertices', first.size, 'of', n, '; hair', hair.reduce((a, b) => a + b, 0), '; specks filled', filled);
console.log('by height (all, weight > 0.5):', JSON.stringify(bands));
// written back with meshopt's filters, as `gltf-transform meshopt --level high` did
doc.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.FILTER });
await io.write(out, doc);
