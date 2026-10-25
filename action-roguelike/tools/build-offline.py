#!/usr/bin/env python3
"""Packs the game into 风控之夜.html, one self-contained file that plays when opened straight from disk
(double-clicked, or downloaded onto a phone) with no server and no network: the illustrations, the 3D
model and three.js all ride inside it. Run it again after changing index.html:

    python3 action-roguelike/tools/build-offline.py
"""
import base64, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / '风控之夜.html'
html = (ROOT / 'index.html').read_text(encoding='utf-8')


def swap(old, new, count=1):
    global html
    assert html.count(old) == count, f'expected {count} of {old!r}, found {html.count(old)}'
    html = html.replace(old, new)


# every file under art/ that the page loads, as a data: URL; the model and her voice go through fetch(), which takes data: URLs too.
# Opened from disk, images by path would taint the canvases the face and the 3D textures are painted on.
MIME = {'.webp': 'image/webp', '.glb': 'model/gltf-binary', '.mp3': 'audio/mpeg'}
art = {f'art/{p.name}': f'data:{MIME[p.suffix]};base64,' + base64.b64encode(p.read_bytes()).decode()
       for p in sorted((ROOT / 'art').iterdir()) if p.suffix in MIME}
for path in art:
    uses = len(re.findall(f'"{re.escape(path)}"', html))
    if uses:  # <img src="art/…"> waits for the table below, then picks its picture up from it
        swap(f'src="{path}"', f'data-art="{path}"', uses)
    swap(f"'{path}'", f"ART['{path}']")

# three.js, GLTFLoader and the meshopt decoder sit in the page as inert text and are handed to load3D as blob: URLs,
# so they still load in the background after the title shows
LIBS = ['three-r128.min.js', 'GLTFLoader-r128.js', 'meshopt-decoder.js']
libs = ''.join(f'<script type="text/plain" id="lib-{i}">{(ROOT / "vendor" / name).read_text(encoding="utf-8")}</script>\n'
               for i, name in enumerate(LIBS))
assert '</script' not in libs.replace('</script>\n', ''), 'a library contains </script'
swap("const M3_LIBS = ['vendor/three-r128.min.js', 'vendor/GLTFLoader-r128.js', 'vendor/meshopt-decoder.js'];",
     f"const M3_LIBS = {json.dumps([f'lib-{i}' for i in range(len(LIBS))])}"
     ".map(id => URL.createObjectURL(new Blob([$(id).textContent], { type: 'text/javascript' })));")

swap('</head>', f'<script>const ART = {json.dumps(art)};</script>\n</head>')
swap('\n<script>\n', '\n' + libs +
     "<script>document.querySelectorAll('[data-art]').forEach(img => { img.src = ART[img.dataset.art]; });</script>\n<script>\n")

OUT.write_text(html, encoding='utf-8')
print(f'{OUT.name}: {OUT.stat().st_size / 1e6:.2f} MB')
