// Prepares the automatic rig of art/whale.glb (大肥鱼) for the game.
//   1. Arms. The rig weighted more than half the mesh to the arm bones (most of her long hair and much of the skirt),
//      so lifting an arm dragged the hair out like a wing. Arm weight is kept only on what is actually the arm:
//      within a capsule along the bones from the shoulder to past the hand, fading out at its edge, and never on
//      hair-blue vertices more than a sleeve's width out. Whatever weight it takes away goes to the collarbone on
//      that side, which only moves with her chest.
//   2. Hair and tail. Neither has bones, so the game sways them in the vertex shader; _SWAY says how much: x for the
//      hair (blue vertices joined to the top of her head, still at the roots and free at the tips), y for the tail
//      (the blue fin behind her, still where it leaves the skirt).
// Run it where @gltf-transform/core, @gltf-transform/extensions, meshoptimizer and sharp are installed, on the
// model before meshopt compression (gltf-transform meshopt --level high afterwards):
//   node whale-weights.mjs in.glb out.glb
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';

const [src, out, R0 = '0.05', R1 = '0.08'] = process.argv.slice(2);
const IN = +R0, OUT = +R1;
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read(src);
const node = doc.getRoot().listNodes().find(n => n.getMesh());
const joints = node.getSkin().listJoints(), names = joints.map(j => j.getName());
const at = Object.fromEntries(joints.map(j => { const m = j.getWorldMatrix(); return [j.getName(), [m[12], m[13], m[14]]]; }));
const prim = node.getMesh().listPrimitives()[0];
const P = prim.getAttribute('POSITION'), J = prim.getAttribute('JOINTS_0'), W = prim.getAttribute('WEIGHTS_0'), UV = prim.getAttribute('TEXCOORD_0');
const M = node.getWorldMatrix();
const { data: px, info } = await sharp(Buffer.from(prim.getMaterial().getBaseColorTexture().getImage())).raw().toBuffer({ resolveWithObject: true });

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const segD = (p, a, b) => {
  const ab = sub(b, a), ap = sub(p, a), t = Math.max(0, Math.min(1, (ap[0] * ab[0] + ap[1] * ab[1] + ap[2] * ab[2]) / (ab[0] ** 2 + ab[1] ** 2 + ab[2] ** 2)));
  return Math.hypot(ap[0] - ab[0] * t, ap[1] - ab[1] * t, ap[2] - ab[2] * t);
};
// each arm as three segments: upper arm, forearm, and the hand out to its fingertips
const arm = {};
for (const s of ['L', 'R']) {
  const sh = at[s + '_Upperarm'], el = at[s + '_Forearm'], wr = at[s + '_Hand'], d = sub(wr, el), tip = [wr[0] + d[0] * 0.7, wr[1] + d[1] * 0.7, wr[2] + d[2] * 0.7];
  arm[s] = p => Math.min(segD(p, sh, el), segD(p, el, wr), segD(p, wr, tip));
}
const moving = names.map(s => /^(L|R)_(Upperarm|Forearm|Hand)/.test(s) ? s[0] : '');
const clav = { L: names.indexOf('L_Clavicle'), R: names.indexOf('R_Clavicle') };
const hairBlue = (r, g, b) => {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (d < 1e-5 || mx !== b) return false;
  const h = ((r - g) / d + 4) * 60;
  return h > 200 && h < 245 && d / mx > 0.4 && mx > 0.45;
};
const e = [0, 0, 0], jj = [0, 0, 0, 0], ww = [0, 0, 0, 0], uv = [0, 0];
let changed = 0, moved = 0;
for (let i = 0, n = P.getCount(); i < n; i++) {
  J.getElement(i, jj); W.getElement(i, ww);
  if (!jj.some((j, k) => moving[j] && ww[k] > 0)) continue;
  P.getElement(i, e);
  const p = [M[0] * e[0] + M[4] * e[1] + M[8] * e[2] + M[12], M[1] * e[0] + M[5] * e[1] + M[9] * e[2] + M[13], M[2] * e[0] + M[6] * e[1] + M[10] * e[2] + M[14]];
  UV.getElement(i, uv);
  const x = Math.min(info.width - 1, Math.max(0, Math.floor(uv[0] * info.width))), y = Math.min(info.height - 1, Math.max(0, Math.floor(uv[1] * info.height)));
  const o = (y * info.width + x) * info.channels, hair = hairBlue(px[o] / 255, px[o + 1] / 255, px[o + 2] / 255);
  const out = {};
  let take = 0;
  for (let k = 0; k < 4; k++) {
    if (ww[k] <= 0) continue;
    const s = moving[jj[k]];
    let keep = 1;
    if (s) {
      const d = arm[s](p), r1 = hair ? IN * 0.6 : OUT, r0 = hair ? IN * 0.4 : IN;
      keep = d <= r0 ? 1 : d >= r1 ? 0 : (r1 - d) / (r1 - r0);
      take += ww[k] * (1 - keep);
      if (keep < 1) { const c = clav[s]; out[c] = (out[c] || 0) + ww[k] * (1 - keep); }
    }
    if (keep > 0) out[jj[k]] = (out[jj[k]] || 0) + ww[k] * keep;
  }
  if (take < 1e-4) continue;
  changed++; if (take > 0.5) moved++;
  const list = Object.entries(out).map(([j, w]) => [+j, w]).sort((a, b) => b[1] - a[1]).slice(0, 4);
  const sum = list.reduce((s, v) => s + v[1], 0);
  for (let k = 0; k < 4; k++) { jj[k] = list[k] ? list[k][0] : 0; ww[k] = list[k] ? list[k][1] / sum : 0; }
  J.setElement(i, jj); W.setElement(i, ww);
}
console.log(`arm weights trimmed on ${changed} vertices, ${moved} of them mostly handed to the collarbones`);

// 2. hair and tail. Copies of a vertex along texture seams are one vertex here, so both sides get the same weight
const n = P.getCount(), pos = new Float32Array(n * 3), blue = new Uint8Array(n), bright = new Uint8Array(n);
for (let i = 0; i < n; i++) {
  P.getElement(i, e);
  for (let k = 0; k < 3; k++) pos[i * 3 + k] = M[k] * e[0] + M[4 + k] * e[1] + M[8 + k] * e[2] + M[12 + k];
  UV.getElement(i, uv);
  const x = Math.min(info.width - 1, Math.max(0, Math.floor(uv[0] * info.width))), y = Math.min(info.height - 1, Math.max(0, Math.floor(uv[1] * info.height)));
  const o = (y * info.width + x) * info.channels, r = px[o] / 255, g = px[o + 1] / 255, b = px[o + 2] / 255;
  const mx = Math.max(r, g, b), d = mx - Math.min(r, g, b);
  blue[i] = d > 1e-5 && mx === b && ((r - g) / d + 4) * 60 > 200 && ((r - g) / d + 4) * 60 < 250 && d / mx > 0.3 && mx > 0.22 ? 1 : 0;
  bright[i] = mx > 0.42 ? 1 : 0;
}
const raw = P.getArray(), first = new Map(), rep = new Int32Array(n);
for (let i = 0; i < n; i++) { const k = raw[i * 3] + ',' + raw[i * 3 + 1] + ',' + raw[i * 3 + 2]; if (!first.has(k)) first.set(k, i); rep[i] = first.get(k); }
for (let i = 0; i < n; i++) { blue[rep[i]] = Math.max(blue[rep[i]], blue[i]); bright[rep[i]] = Math.max(bright[rep[i]], bright[i]); }
const idx = prim.getIndices().getArray(), nb = Array.from({ length: n }, () => []);
for (let t = 0; t < idx.length; t += 3) for (let k = 0; k < 3; k++) { const a = rep[idx[t + k]], b = rep[idx[t + (k + 1) % 3]]; if (a !== b) { nb[a].push(b); nb[b].push(a); } }
const X = i => pos[i * 3], Y = i => pos[i * 3 + 1], Z = i => pos[i * 3 + 2];
const hx = at.Hip[0];
// the hair: from the crown down through blue vertices, leaving out the front of the dress and the tail. It runs from
// navy at the crown to sky blue at the tips, so below the shoulders it has to be bright: the navy there is her dress
const hairOK = i => blue[i] && (Y(i) > 0.6 || bright[i]) && !(Y(i) < 0.62 && X(i) > hx + 0.03 && Math.abs(Z(i)) < 0.11) && !(Y(i) < 0.3 && X(i) < hx - 0.05);
const hairV = new Uint8Array(n), queue = [];
for (let i = 0; i < n; i++) if (rep[i] === i && hairOK(i) && Y(i) > 0.8) { hairV[i] = 1; queue.push(i); }
for (let q = 0; q < queue.length; q++) for (const j of nb[queue[q]]) if (!hairV[j] && hairOK(j)) { hairV[j] = 1; queue.push(j); }
// the tail: bright blue, behind her and below the hem (her navy shoes are not)
const tailV = new Uint8Array(n);
const nearFoot = i => ['L', 'R'].some(s => segD([X(i), Y(i), Z(i)], at[s + '_Calf'], at[s + '_ToeBase']) < 0.085);
for (let i = 0; i < n; i++) if (rep[i] === i && blue[i] && bright[i] && X(i) < hx - 0.06 && Y(i) < 0.34 && !hairV[i] && !nearFoot(i)) tailV[i] = 1;
// and only the biggest piece of it: specks on the bows at her ankles are not the tail
{
  const comp = new Int32Array(n).fill(-1), sizes = [];
  for (let i = 0; i < n; i++) {
    if (!tailV[i] || comp[i] >= 0) continue;
    const c = sizes.length, q = [i];
    comp[i] = c;
    for (let k = 0; k < q.length; k++) for (const j of nb[q[k]]) if (tailV[j] && comp[j] < 0) { comp[j] = c; q.push(j); }
    sizes.push(q.length);
  }
  const big = sizes.indexOf(Math.max(...sizes));
  for (let i = 0; i < n; i++) if (tailV[i] && comp[i] !== big) tailV[i] = 0;
}
const ss = (a, b, v) => { const t = Math.max(0, Math.min(1, (v - a) / (b - a))); return t * t * (3 - 2 * t); };
const sway = new Uint8Array(n * 2);
let nh = 0, nt = 0;
for (let i = 0; i < n; i++) {
  const r = rep[i];
  if (hairV[r]) { sway[i * 2] = Math.round(255 * ss(0.74, 0.3, Y(r))); nh++; }
  if (tailV[r]) { sway[i * 2 + 1] = Math.round(255 * ss(0.32, 0.12, Y(r))); nt++; }
}
prim.setAttribute('_SWAY', doc.createAccessor().setType('VEC2').setArray(sway).setNormalized(true).setBuffer(P.getBuffer()));
console.log(`sway: ${nh} hair vertices, ${nt} tail vertices`);
await io.write(out, doc);
