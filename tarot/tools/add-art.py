#!/usr/bin/env python3
"""把一张插画放进星夜塔罗，替换那张牌画出来的牌面。

用法：
    python3 tarot/tools/add-art.py 图片路径 牌
    python3 tarot/tools/add-art.py --rebuild

「牌」可以是编号（0–21 大阿卡纳，22 起依次是权杖、圣杯、宝剑、星币，每组王牌到国王 14 张），
也可以是中文名（星星、圣杯三、宝剑国王）或英文名（The Star、Three of Cups）。

图片会从中间裁成 2:3，宽超过 1024 时缩到 1024×1536，存成 tarot/art/<编号>.webp，
然后重新生成 tarot/art/manifest.js，网页就会用这张插画。--rebuild 只重新生成清单。
需要 Pillow（pip install pillow）。
"""
import re
import sys
from pathlib import Path

ART = Path(__file__).resolve().parent.parent / 'art'

MAJORS = [
    ('愚者', 'The Fool'), ('魔术师', 'The Magician'), ('女祭司', 'The High Priestess'), ('皇后', 'The Empress'),
    ('皇帝', 'The Emperor'), ('教皇', 'The Hierophant'), ('恋人', 'The Lovers'), ('战车', 'The Chariot'),
    ('力量', 'Strength'), ('隐士', 'The Hermit'), ('命运之轮', 'Wheel of Fortune'), ('正义', 'Justice'),
    ('倒吊人', 'The Hanged Man'), ('死神', 'Death'), ('节制', 'Temperance'), ('恶魔', 'The Devil'),
    ('塔', 'The Tower'), ('星星', 'The Star'), ('月亮', 'The Moon'), ('太阳', 'The Sun'),
    ('审判', 'Judgement'), ('世界', 'The World'),
]
SUITS = [('权杖', 'Wands'), ('圣杯', 'Cups'), ('宝剑', 'Swords'), ('星币', 'Pentacles')]
RANKS = [('王牌', 'Ace'), ('二', 'Two'), ('三', 'Three'), ('四', 'Four'), ('五', 'Five'), ('六', 'Six'), ('七', 'Seven'),
         ('八', 'Eight'), ('九', 'Nine'), ('十', 'Ten'), ('侍从', 'Page'), ('骑士', 'Knight'), ('王后', 'Queen'), ('国王', 'King')]

CARDS = list(MAJORS) + [(s + r, f'{re_} of {se}') for s, se in SUITS for r, re_ in RANKS]


def card_id(name):
    name = name.strip()
    if name.isdigit() and 0 <= int(name) < len(CARDS):
        return int(name)
    for i, (zh, en) in enumerate(CARDS):
        if name == zh or name.lower() == en.lower():
            return i
    sys.exit(f'不认识这张牌：{name}')


def rebuild():
    files = {}
    for f in sorted(ART.iterdir()):
        m = re.fullmatch(r'(\d+)\.(webp|png|jpe?g)', f.name, re.I)
        if m and int(m.group(1)) < len(CARDS):
            files[int(m.group(1))] = f.name
    lines = ['// 由 tools/add-art.py 生成：有插画的牌的编号 → 文件名', 'window.TAROT_ART = {']
    lines += [f"  {i}: '{name}',  // {CARDS[i][0]}" for i, name in sorted(files.items())]
    lines.append('};')
    (ART / 'manifest.js').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'清单里有 {len(files)} 张插画：' + '、'.join(CARDS[i][0] for i in sorted(files)))


def add(path, card):
    from PIL import Image
    i = card_id(card)
    im = Image.open(path).convert('RGB')
    w, h = im.size
    if w * 3 > h * 2:  # 太宽，裁两边
        nw = h * 2 // 3
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w * 3 < h * 2:  # 太高，裁上下
        nh = w * 3 // 2
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    if im.width > 1024:
        im = im.resize((1024, 1536), Image.LANCZOS)
    for old in ART.glob(f'{i}.*'):
        if old.suffix.lower() in ('.webp', '.png', '.jpg', '.jpeg'):
            old.unlink()
    out = ART / f'{i}.webp'
    im.save(out, 'WEBP', quality=84, method=6)
    print(f'{CARDS[i][0]}（{CARDS[i][1]}）→ {out.relative_to(ART.parent.parent)}，{out.stat().st_size // 1024} KB')
    rebuild()


if __name__ == '__main__':
    if sys.argv[1:] == ['--rebuild']:
        rebuild()
    elif len(sys.argv) == 3:
        add(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
