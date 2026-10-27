// Prepares the automatic rig of art/dragon.glb (ChatGPT 龙娘) for the game, after welding and simplifying it.
//   1. The second tail. The model came with two tails: one curling out behind her, and one curling round in front of
//      her legs. The front one goes. It is light lavender, and so are bits of the skirt's hem in front of her shins;
//      walking the lavender there from the tail's tip along the surface, it stays a narrow tube until it reaches the
//      hem, where it spreads out. The tube up to there is the tail, and everything within its radius of its centre
//      line is cut, whatever its colour (the frill of spikes along its top).
//   1b. The second face. The back of her head is her face again, mirrored; it is painted over with hair.
//   2. Arms and legs. The rig weighted most of her long hair, the wings and the sleeves' frills to the arm bones and
//      the whole skirt and the other tail to the legs, so lifting an arm or kicking a leg dragged them along. Limb
//      weight is kept only within a capsule along each limb's bones, fading out at its edge; what it takes away goes
//      to the collarbone on that side (arms) or the pelvis (legs).
//   3. Wings and tail. Neither has bones, so the game moves them in the vertex shader; _SWAY says how much: x for the
//      wings (violet at shoulder height behind her, still at the roots and free at the tips), y for the tail behind
//      her (found like the front one, still where it leaves the skirt and free at the tip).
//   4. Only the colour map is kept: toon shading has no use for the normal and metal/roughness maps.
// Run it where @gltf-transform/cli, core, extensions, meshoptimizer and sharp are installed:
//   gltf-transform weld src.glb welded.glb && gltf-transform simplify welded.glb simple.glb --ratio 0.03 --error 0.01
//   node dragon-model.mjs simple.glb rigged.glb
//   gltf-transform webp rigged.glb webp.glb --slots baseColorTexture --quality 84
//   gltf-transform meshopt webp.glb dragon.glb --level high
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';

const [src, out] = process.argv.slice(2);
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read(src);
const node = doc.getRoot().listNodes().find(n => n.getMesh());
const joints = node.getSkin().listJoints(), names = joints.map(j => j.getName());
const at = Object.fromEntries(joints.map(j => { const m = j.getWorldMatrix(); return [j.getName(), [m[12], m[13], m[14]]]; }));
const prim = node.getMesh().listPrimitives()[0];
const PA = prim.getAttribute('POSITION'), J = prim.getAttribute('JOINTS_0'), W = prim.getAttribute('WEIGHTS_0'), UV = prim.getAttribute('TEXCOORD_0');
const n = PA.getCount(), P = PA.getArray();
const { data: px, info } = await sharp(Buffer.from(prim.getMaterial().getBaseColorTexture().getImage())).raw().toBuffer({ resolveWithObject: true });

// copies of a vertex along texture seams are one vertex here
const first = new Map(), rep = new Int32Array(n);
for (let i = 0; i < n; i++) { const k = P[i * 3] + ',' + P[i * 3 + 1] + ',' + P[i * 3 + 2]; if (!first.has(k)) first.set(k, i); rep[i] = first.get(k); }
const hsv = new Float32Array(n * 3), uv = [0, 0];
for (let i = 0; i < n; i++) {
  UV.getElement(i, uv);
  const x = Math.min(info.width - 1, Math.max(0, Math.floor(uv[0] * info.width))), y = Math.min(info.height - 1, Math.max(0, Math.floor(uv[1] * info.height)));
  const o = (y * info.width + x) * info.channels, r = px[o] / 255, g = px[o + 1] / 255, b = px[o + 2] / 255;
  const mx = Math.max(r, g, b), d = mx - Math.min(r, g, b);
  hsv[i * 3] = d < 0.03 || mx !== b ? -1 : ((r - g) / d + 4) * 60; hsv[i * 3 + 1] = mx ? d / mx : 0; hsv[i * 3 + 2] = mx;
}
const lavender = i => hsv[i * 3] > 235 && hsv[i * 3] < 295 && hsv[i * 3 + 1] > 0.1 && hsv[i * 3 + 2] > 0.5;
const violet = i => hsv[i * 3] > 245 && hsv[i * 3] < 300 && hsv[i * 3 + 1] > 0.14 && hsv[i * 3 + 2] > 0.3;
const X = i => P[i * 3], Y = i => P[i * 3 + 1], Z = i => P[i * 3 + 2];
const dist = (a, b) => Math.hypot(X(a) - X(b), Y(a) - Y(b), Z(a) - Z(b));
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const segD = (p, a, b) => {
  const ab = sub(b, a), ap = sub(p, a), t = Math.max(0, Math.min(1, (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / (ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2 || 1)));
  return [Math.hypot(ap[0] - ab[0] * t, ap[1] - ab[1] * t, ap[2] - ab[2] * t), t];
};
const idx = prim.getIndices().getArray();
const neighbours = ok => {
  const nb = Array.from({ length: n }, () => []);
  for (let t = 0; t < idx.length; t += 3) for (let k = 0; k < 3; k++) { const a = rep[idx[t + k]], b = rep[idx[t + (k + 1) % 3]]; if (a !== b && ok[a] && ok[b]) { nb[a].push(b); nb[b].push(a); } }
  return nb;
};

// a tail: from the tip, the surface distance to every vertex of the lavender piece; then its centre line and radius in
// bands of that distance up to `reach`; returns each vertex's distance along the tail (Infinity if not on it)
function tail(cand, tipOf, reach) {
  const nb = neighbours(cand);
  let tip = -1;
  for (let i = 0; i < n; i++) if (cand[i] && (tip < 0 || tipOf(i) > tipOf(tip))) tip = i;
  const D = new Float64Array(n).fill(Infinity), done = new Uint8Array(n), heap = [[0, tip]];
  D[tip] = 0;
  while (heap.length) {
    let bi = 0; for (let i = 1; i < heap.length; i++) if (heap[i][0] < heap[bi][0]) bi = i;
    const [d, v] = heap[bi]; heap[bi] = heap[heap.length - 1]; heap.pop();
    if (done[v]) continue; done[v] = 1;
    for (const w of nb[v]) { const nd = d + dist(v, w); if (nd < D[w]) { D[w] = nd; heap.push([nd, w]); } }
  }
  const B = 0.02, line = [];
  for (let b = 0; b * B < reach; b++) {
    const a = []; for (let i = 0; i < n; i++) if (rep[i] === i && D[i] >= b * B && D[i] < (b + 1) * B) a.push(i);
    if (!a.length) continue;
    const c = [0, 0, 0]; for (const i of a) for (let k = 0; k < 3; k++) c[k] += P[i * 3 + k] / a.length;
    const ds = a.map(i => Math.hypot(X(i) - c[0], Y(i) - c[1], Z(i) - c[2])).sort((x, y) => x - y);
    line.push({ c, d: (b + 0.5) * B, r: Math.min(0.08, Math.max(0.03, ds[Math.floor(ds.length * 0.9)] * 1.15)) });
  }
  const along = new Float64Array(n).fill(Infinity);
  for (let i = 0; i < n; i++) {
    if (rep[i] !== i) continue;
    if (D[i] < reach) { along[i] = D[i]; continue; }
    const p = [X(i), Y(i), Z(i)];
    for (let s = 0; s + 1 < line.length; s++) {
      const [d, t] = segD(p, line[s].c, line[s + 1].c);
      if (d < line[s].r * (1 - t) + line[s + 1].r * t) { along[i] = line[s].d * (1 - t) + line[s + 1].d * t; break; }
    }
  }
  console.log(`tail from ${[X(tip), Y(tip), Z(tip)].map(v => v.toFixed(3))}: ${along.filter(v => v < Infinity).length} vertices`);
  return along;
}

// 1. the front tail: lavender in front of her shins (she faces -x), the tip furthest out to her left (+z)
{
  const cand = new Uint8Array(n);
  for (let i = 0; i < n; i++) if (X(i) < -0.12 && Y(i) < 0.38 && lavender(i)) cand[rep[i]] = 1;
  const along = tail(cand, i => Z(i), 0.33);
  const keep = [];
  for (let t = 0; t < idx.length; t += 3) if (![0, 1, 2].some(k => along[rep[idx[t + k]]] < Infinity)) keep.push(idx[t], idx[t + 1], idx[t + 2]);
  console.log(`front tail cut: ${idx.length / 3} -> ${keep.length / 3} triangles`);
  prim.getIndices().setArray(idx.constructor.from(keep));
}

// 1b. the second face: the back of her head is a mirror of her face, eyes and all. Over an oval there (the back
// half of the head, between the choker and the top of the bangs) the colour map is painted over with hair: for each
// texel of each triangle there, the point of the surface it colours gets a colour from a pattern of strands running
// down the back of the head, silver to lavender in her hair's own colours, with a band of sheen across; towards the
// oval's edge it fades into what was there
{
  const ALL = idx.length; // the triangle list as it stands after the tail cut
  const tri = prim.getIndices().getArray(), tex = prim.getMaterial().getBaseColorTexture();
  const Wt = info.width, Ht = info.height, C = info.channels, img = Buffer.from(px);
  const cy = 0.775, cz = -0.016, ry = 0.105, rz = 0.118, backX = -0.075;
  const oval = (y, z) => Math.hypot((y - cy) / ry, (z - cz) / rz);
  const lo = [204, 193, 224], mid = [228, 219, 238], hi = [245, 241, 250];
  const hairAt = (x, y, z) => {
    // strands fanning down from the crown, in clumps of different widths, bent a little as they fall
    const th = Math.atan2(z - cz, 0.92 - y), a = th * 38 + Math.sin(y * 30 + th * 5) * 0.8;
    const s1 = Math.sin(a) * 0.45 + Math.sin(a * 1.7 + 1.3 + y * 8) * 0.35 + Math.sin(th * 11 + y * 6) * 0.2;
    let t = 0.55 + 0.32 * s1;
    // darker down towards the nape and out at the sides, a band of sheen across the crown
    t *= 0.8 + 0.2 * Math.min(1, (y - 0.68) / 0.12);
    const sheen = Math.max(0, 1 - Math.abs(y - 0.84) / 0.025) * (0.6 + 0.4 * Math.sin(z * 90));
    const c = t < 0.5 ? lo.map((v, k) => v + (mid[k] - v) * t * 2) : mid.map((v, k) => v + (hi[k] - v) * (t - 0.5) * 2);
    return c.map((v, k) => v + (255 - v) * sheen * 0.5);
  };
  let painted = 0, tris = 0;
  const uvs = UV.getArray();
  for (let t = 0; t < tri.length; t += 3) {
    const v = [tri[t], tri[t + 1], tri[t + 2]];
    const gx = (X(v[0]) + X(v[1]) + X(v[2])) / 3, gy = (Y(v[0]) + Y(v[1]) + Y(v[2])) / 3, gz = (Z(v[0]) + Z(v[1]) + Z(v[2])) / 3;
    if (gx < backX || oval(gy, gz) > 1) continue;
    tris++;
    const q = v.map(i => [uvs[i * 2] * Wt - 0.5, uvs[i * 2 + 1] * Ht - 0.5]);
    const det = (q[1][1] - q[2][1]) * (q[0][0] - q[2][0]) + (q[2][0] - q[1][0]) * (q[0][1] - q[2][1]);
    if (Math.abs(det) < 1e-9) continue;
    const x0 = Math.max(0, Math.floor(Math.min(q[0][0], q[1][0], q[2][0])) - 1), x1 = Math.min(Wt - 1, Math.ceil(Math.max(q[0][0], q[1][0], q[2][0])) + 1);
    const y0 = Math.max(0, Math.floor(Math.min(q[0][1], q[1][1], q[2][1])) - 1), y1 = Math.min(Ht - 1, Math.ceil(Math.max(q[0][1], q[1][1], q[2][1])) + 1);
    for (let py = y0; py <= y1; py++) for (let pxx = x0; pxx <= x1; pxx++) {
      const b0 = ((q[1][1] - q[2][1]) * (pxx - q[2][0]) + (q[2][0] - q[1][0]) * (py - q[2][1])) / det;
      const b1 = ((q[2][1] - q[0][1]) * (pxx - q[2][0]) + (q[0][0] - q[2][0]) * (py - q[2][1])) / det, b2 = 1 - b0 - b1;
      // a texel's width over the edge too, so the seams don't show the old colour
      const m = -1.5 / Math.max(1, Math.sqrt(Math.abs(det)));
      if (b0 < m || b1 < m || b2 < m) continue;
      const x = b0 * X(v[0]) + b1 * X(v[1]) + b2 * X(v[2]), y = b0 * Y(v[0]) + b1 * Y(v[1]) + b2 * Y(v[2]), z = b0 * Z(v[0]) + b1 * Z(v[1]) + b2 * Z(v[2]);
      const c = hairAt(x, y, z), f = Math.min(1, Math.max(0, (1 - oval(y, z)) / 0.15)), o = (py * Wt + pxx) * C;
      for (let k = 0; k < 3; k++) img[o + k] = Math.round(img[o + k] + (c[k] - img[o + k]) * f);
      painted++;
    }
  }
  const out = await sharp(img, { raw: { width: Wt, height: Ht, channels: C } }).png().toBuffer();
  tex.setImage(out).setMimeType('image/png');
  console.log(`second face painted over: ${tris} triangles, ${painted} texels`);
}

// 2. arm and leg weights kept to capsules along the bones
const limb = {}, catcher = {};
for (const s of ['L', 'R']) {
  // the rig put her left wrist joint well behind her hand; the right one is where the hand is, so the left arm's
  // capsule mirrors the right forearm
  const sh = at[s + '_Upperarm'], el = at[s + '_Forearm'], rf = sub(at.R_Hand, at.R_Forearm);
  const wr = s === 'L' ? [el[0] + rf[0], el[1] + rf[1], el[2] - rf[2]] : at.R_Hand, d = sub(wr, el), tip = [wr[0] + d[0] * 0.7, wr[1] + d[1] * 0.7, wr[2] + d[2] * 0.7];
  limb[s + 'arm'] = p => Math.min(segD(p, sh, el)[0], segD(p, el, wr)[0], segD(p, wr, tip)[0]);
  const hip = at[s + '_Thigh'], kn = at[s + '_Calf'], an = at[s + '_Foot'], toe = at[s + '_ToeBase'];
  limb[s + 'leg'] = p => Math.min(segD(p, hip, kn)[0], segD(p, kn, an)[0], segD(p, an, toe)[0]);
  catcher[s + 'arm'] = names.indexOf(s + '_Clavicle'); catcher[s + 'leg'] = names.indexOf('Pelvis');
}
const limbOf = names.map(s => { const m = /^(L|R)_(Upperarm|Forearm|Hand|Thigh|Calf|Foot|ToeBase)/.exec(s); return m ? m[1] + (/arm|Forearm|Hand/.test(m[2]) ? 'arm' : 'leg') : ''; });
const RAD = { arm: [0.06, 0.09], leg: [0.06, 0.09] };
{
  const e = [0, 0, 0], jj = [0, 0, 0, 0], ww = [0, 0, 0, 0];
  let changed = 0;
  for (let i = 0; i < n; i++) {
    J.getElement(i, jj); W.getElement(i, ww);
    if (!jj.some((j, k) => limbOf[j] && ww[k] > 0)) continue;
    PA.getElement(i, e);
    const out = {};
    let take = 0;
    for (let k = 0; k < 4; k++) {
      if (ww[k] <= 0) continue;
      const s = limbOf[jj[k]];
      let keep = 1;
      if (s) {
        const [r0, r1] = RAD[s.slice(1)], d = limb[s](e);
        keep = d <= r0 ? 1 : d >= r1 ? 0 : (r1 - d) / (r1 - r0);
        take += ww[k] * (1 - keep);
        if (keep < 1) { const c = catcher[s]; out[c] = (out[c] || 0) + ww[k] * (1 - keep); }
      }
      if (keep > 0) out[jj[k]] = (out[jj[k]] || 0) + ww[k] * keep;
    }
    if (take < 1e-4) continue;
    changed++;
    const list = Object.entries(out).map(([j, w]) => [+j, w]).sort((a, b) => b[1] - a[1]).slice(0, 4);
    const sum = list.reduce((s, v) => s + v[1], 0);
    for (let k = 0; k < 4; k++) { jj[k] = list[k] ? list[k][0] : 0; ww[k] = list[k] ? list[k][1] / sum : 0; }
    J.setElement(i, jj); W.setElement(i, ww);
  }
  console.log(`limb weights trimmed on ${changed} vertices`);
}

// 3. sway: the wings, the biggest violet piece on each side of her back at shoulder height; and the tail behind her
const ss = (a, b, v) => { const t = Math.max(0, Math.min(1, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
const sway = new Uint8Array(n * 2);
{
  const cand = new Uint8Array(n);
  for (let i = 0; i < n; i++) if (X(i) > -0.02 && Y(i) > 0.47 && Y(i) < 0.78 && Math.abs(Z(i) + 0.01) > 0.045 && violet(i)) cand[rep[i]] = 1;
  const nb = neighbours(cand), comp = new Int32Array(n).fill(-1), sizes = [];
  for (let i = 0; i < n; i++) {
    if (!cand[i] || comp[i] >= 0) continue;
    const q = [i]; comp[i] = sizes.length;
    for (let k = 0; k < q.length; k++) for (const j of nb[q[k]]) if (comp[j] < 0) { comp[j] = sizes.length; q.push(j); }
    sizes.push({ id: sizes.length, n: q.length, side: Math.sign(q.reduce((s, v) => s + Z(v), 0)) });
  }
  const wings = [1, -1].map(side => sizes.filter(c => c.side === side).sort((a, b) => b.n - a.n)[0].id);
  // still at the root by her spine, freest at the far edge
  let nw = 0;
  for (let i = 0; i < n; i++) {
    const r = rep[i];
    if (!wings.includes(comp[r])) continue;
    sway[i * 2] = Math.round(255 * ss(0.05, 0.24, Math.hypot(Z(r) + 0.01, (Y(r) - 0.62) * 0.6))); nw++;
  }
  console.log(`wings: ${nw} vertices`);
}
{
  const cand = new Uint8Array(n);
  for (let i = 0; i < n; i++) if (X(i) > 0.02 && Y(i) < 0.42 && lavender(i)) cand[rep[i]] = 1;
  const REACH = 0.36, along = tail(cand, i => X(i), REACH);
  for (let i = 0; i < n; i++) { const d = along[rep[i]]; if (d < Infinity) sway[i * 2 + 1] = Math.round(255 * ss(REACH, 0.06, d)); }
}
prim.setAttribute('_SWAY', doc.createAccessor().setType('VEC2').setArray(sway).setNormalized(true).setBuffer(PA.getBuffer()));

// 4. toon shading uses only the colour map: the normal and metal/roughness maps go
const mat = prim.getMaterial();
for (const t of [mat.getNormalTexture(), mat.getMetallicRoughnessTexture()]) if (t) t.dispose();
await io.write(out, doc);
