# 牌面插画

有插画的牌会直接显示插画，没有插画的牌用代码画的黑金牌面（版式照着插画做，混在一起也不突兀）。目前有插画的是：

- 17 星星（The Star）

## 加一张插画

```sh
python3 tarot/tools/add-art.py 图片路径 牌名
# 例如
python3 tarot/tools/add-art.py ~/Downloads/fool.png 愚者
python3 tarot/tools/add-art.py ~/Downloads/x.png "Three of Cups"
```

脚本会把图从中间裁成 2:3、缩到 1024×1536、存成 `art/<编号>.webp`，并更新 `art/manifest.js`。牌名可以写中文名、英文名或编号。需要 Pillow（`pip install pillow`）。

## 用 AI 生成同样画风的插画

「星星」那张的画风是：日系厚涂的帅气青年，深蓝与半透明白色长袍，金色首饰和星形挂饰，星空与星云，满屏闪光粒子；外面是金色新艺术风格的细框，四角是带四芒星的圆章，顶上一块写罗马数字的小铭牌，底下一块深色名牌写英文牌名，名牌下面一行三个英文关键词。

每张牌用「通用风格」加上「这张牌的画面」拼成一条提示词，比例设为 2:3（竖版）。想让整副牌像同一个人，可以固定种子，或者把「星星」那张当参考图（图生图、风格参考、角色参考）。

### 通用风格

```
ornate tarot card illustration, vertical 2:3, anime-style semi-realistic painting, a handsome young man with tousled dark hair and luminous blue eyes, elegant androgynous features, flowing midnight-blue and translucent white layered robes, delicate gold jewelry and hanging star ornaments, deep starry night sky with violet and blue nebula, glowing eight-pointed stars, sparkling light particles, luminous, highly detailed, intricate gold art nouveau filigree border with circular star medallions in the four corners, small cartouche at the top center with the roman numeral {编号}, dark rounded name plate at the bottom with the title "{英文名}" in elegant serif capitals, a line of three keywords "{关键词}" beneath it
```

把 `{编号}`、`{英文名}`、`{关键词}` 换成下表里的内容。小阿卡纳顶上写的是数字或 PAGE / KNIGHT / QUEEN / KING。

### 大阿卡纳

| # | 牌 | 英文名 | 关键词 | 这张牌的画面 |
| --- | --- | --- | --- | --- |
| 0 | 愚者 | THE FOOL | BEGINNINGS • FREEDOM • LEAP OF FAITH | a carefree young traveler stepping toward a cliff edge under the stars, a small bundle tied to a staff over his shoulder, a white rose in his hand, a small white dog leaping at his feet, wind in his hair and robes |
| I | 魔术师 | THE MAGICIAN | WILL • SKILL • MANIFESTATION | a confident young sorcerer raising a glowing wand to the sky with one hand and pointing to the ground with the other, a glowing infinity sign above his head, a stone altar before him holding a cup, a sword, a pentacle and a wand, roses and lilies |
| II | 女祭司 | THE HIGH PRIESTESS | INTUITION • MYSTERY • STILLNESS | a serene, mysterious young priest seated between a black pillar marked B and a white pillar marked J, a crescent moon at his feet, a half-hidden scroll in his robes, a veil embroidered with pomegranates behind him, cold moonlight |
| III | 皇后 | THE EMPRESS | ABUNDANCE • NURTURE • BEAUTY | a gentle, regal young man crowned with twelve stars reclining on velvet cushions in a golden wheat field beside a waterfall, a heart-shaped shield with the symbol of Venus, a lush forest |
| IV | 皇帝 | THE EMPEROR | AUTHORITY • ORDER • STRUCTURE | a stern young king on a stone throne carved with ram heads, holding an ankh scepter and a golden orb, armor beneath a deep red and gold robe, barren mountains behind |
| V | 教皇 | THE HIEROPHANT | TRADITION • FAITH • GUIDANCE | a solemn young high priest in ornate robes and a triple crown raising one hand in blessing, two acolytes kneeling before him, crossed golden keys at his feet, cathedral pillars |
| VI | 恋人 | THE LOVERS | LOVE • UNION • CHOICE | a young man and his beloved standing face to face beneath a radiant winged angel in the clouds, a tree of flames and a tree with a coiled serpent behind them, a distant mountain |
| VII | 战车 | THE CHARIOT | WILL • VICTORY • MOMENTUM | a young armored prince standing in a chariot under a star-spangled canopy, crescent moons on his shoulders, a black sphinx and a white sphinx before the chariot, a walled city behind |
| VIII | 力量 | STRENGTH | COURAGE • GENTLENESS • RESOLVE | a gentle young man in white robes and a flower garland calmly closing the jaws of a great golden lion, a glowing infinity sign above his head |
| IX | 隐士 | THE HERMIT | INTROSPECTION • SOLITUDE • INNER LIGHT | a lone young hermit in a grey hooded cloak on a snowy mountain peak, holding up a lantern with a glowing six-pointed star inside and leaning on a staff |
| X | 命运之轮 | WHEEL OF FORTUNE | CYCLES • FATE • TURNING POINT | a great golden wheel engraved with alchemical symbols turning in the night sky, a sphinx on top, a serpent descending and a jackal-headed figure rising, a young man reaching out to touch the wheel, four winged creatures reading books in the clouds |
| XI | 正义 | JUSTICE | TRUTH • BALANCE • CONSEQUENCE | a composed young judge on a throne between two pillars, an upright sword in his right hand and balanced golden scales in his left, a crown, a violet curtain behind |
| XII | 倒吊人 | THE HANGED MAN | SURRENDER • PAUSE • NEW PERSPECTIVE | a serene young man hanging upside down by one ankle from a living T-shaped tree, the other leg crossed behind, hands behind his back, a golden halo around his head, a calm face |
| XIII | 死神 | DEATH | ENDINGS • TRANSFORMATION • REBIRTH | an elegant dark young knight in black armor riding a pale white horse, carrying a black banner with a white rose, the sun rising between two distant towers, solemn rather than gory |
| XIV | 节制 | TEMPERANCE | BALANCE • HARMONY • PATIENCE | a winged young angel with a sun disc on his brow, one foot in a pool and one on land, pouring a stream of light between two golden cups, irises by the water, a path leading to mountains crowned with light |
| XV | 恶魔 | THE DEVIL | BONDAGE • DESIRE • SHADOW | a seductive dark young demon lord with ram horns and bat wings on a black pedestal, an inverted pentagram glowing above him, two figures below in loose chains they could slip off |
| XVI | 塔 | THE TOWER | UPHEAVAL • REVELATION • SUDDEN CHANGE | a tall tower on a crag struck by lightning, its crown blown off, flames bursting from the windows, a young man falling through the air with his robes flying, golden sparks raining down |
| XVII | 星星 | THE STAR | HOPE • HEALING • RENEWAL | 已经有了 |
| XVIII | 月亮 | THE MOON | ILLUSION • INTUITION • THE UNKNOWN | a young man standing by a still pool at night beneath an enormous full moon, a dog and a wolf howling at the moon, a crayfish crawling from the water, a winding path between two towers |
| XIX | 太阳 | THE SUN | JOY • SUCCESS • VITALITY | a joyful young man riding a white horse with a red banner, sunflowers over a stone wall, a huge radiant sun filling the sky |
| XX | 审判 | JUDGEMENT | AWAKENING • CALLING • RENEWAL | a handsome winged angel blowing a golden trumpet with a banner from the clouds, people rising from open coffins floating on water, snowy mountains |
| XXI | 世界 | THE WORLD | COMPLETION • WHOLENESS • JOURNEY'S END | a young dancer floating inside a great laurel wreath tied with ribbons, holding a wand in each hand, a violet sash, an angel, an eagle, a lion and a bull in the clouds around him |

### 小阿卡纳

四组花色各加一句色调，让同一组的牌看起来是一家：

- 权杖（WANDS）：`warm ember and flame accents, sparks, desert and sunset tones`
- 圣杯（CUPS）：`cool water and moonlight accents, waves, lilies, silver-blue tones`
- 宝剑（SWORDS）：`silver steel and wind accents, clouds, feathers, pale lavender tones`
- 星币（PENTACLES）：`golden coin and earth accents, gardens, vines, emerald-green tones`

关键词用网页里正位的三个关键词翻成英文即可。

| 牌 | 画面 |
| --- | --- |
| 权杖王牌 | a glowing hand emerging from a cloud holding a sprouting wand, leaves drifting down, a castle on a distant hill |
| 权杖二 | a young lord on castle battlements holding a small globe, one wand in hand and one fixed to the wall, gazing over the sea |
| 权杖三 | a young merchant on a cliff watching ships sail toward the horizon, three wands planted around him |
| 权杖四 | four wands holding a garland canopy, two figures celebrating with bouquets, a castle behind |
| 权杖五 | five young men sparring playfully with long wands |
| 权杖六 | a young hero wearing a laurel wreath riding a white horse through a cheering crowd, a wand tied with a wreath |
| 权杖七 | a young man on a hilltop holding his ground with one wand against six wands rising from below |
| 权杖八 | eight wands flying in formation through a clear sky over a river and hills |
| 权杖九 | a wounded young guard with a bandaged head leaning on a wand, eight wands standing behind him like a fence |
| 权杖十 | a young man straining to carry a heavy bundle of ten wands toward a distant town |
| 权杖侍从 | a curious young page in a desert holding a tall wand and gazing at its new sprout, a tunic patterned with salamanders |
| 权杖骑士 | a dashing young knight on a rearing horse holding a wand, flame-like plume and salamander tunic |
| 权杖王后 | a radiant queen on a throne carved with lions, holding a wand and a sunflower, a black cat at her feet |
| 权杖国王 | a commanding young king on a throne decorated with lions and salamanders, holding a flowering wand |
| 圣杯王牌 | a glowing hand from a cloud offering an overflowing golden cup, five streams of water falling into a lotus pond, a dove above |
| 圣杯二 | a young man and his beloved exchanging cups, a winged lion's head above a caduceus between them |
| 圣杯三 | three friends raising cups in a joyful toast among fruit and flowers |
| 圣杯四 | a young man sitting under a tree with folded arms, three cups before him, a fourth cup offered by a hand from a cloud |
| 圣杯五 | a young man in a black cloak mourning over three spilled cups, two full cups standing behind him, a bridge across a river |
| 圣杯六 | a young man handing a cup filled with flowers to a child in a sunny old courtyard, six cups of white flowers |
| 圣杯七 | a young man in silhouette before seven cups floating in clouds, each holding a different vision: a castle, jewels, a wreath, a dragon, a serpent, a veiled figure, a head |
| 圣杯八 | a young man in a red cloak walking away from eight stacked cups toward mountains under an eclipsed moon |
| 圣杯九 | a contented young man seated with arms crossed, nine cups arranged on a curved table behind him |
| 圣杯十 | a family with arms raised beneath a rainbow of ten cups, two children dancing, a cottage by a river |
| 圣杯侍从 | a dreamy young page in a floral tunic holding a cup from which a small fish peeks out, waves behind him |
| 圣杯骑士 | a graceful young knight on a white horse riding slowly, holding a cup forward, winged helmet |
| 圣杯王后 | a serene queen on a throne at the water's edge gazing into an ornate covered cup, cherubs carved on the throne |
| 圣杯国王 | a calm young king on a throne floating on a rough sea, holding a cup and a scepter, a fish pendant, a ship and a leaping fish behind |
| 宝剑王牌 | a glowing hand from a cloud gripping an upright sword topped with a crown, olive and palm branches, mountains |
| 宝剑二 | a blindfolded young man seated by the sea with two swords crossed over his chest, a crescent moon |
| 宝剑三 | a red heart pierced by three swords under a stormy rain-filled sky, a young man's silhouette in sorrow |
| 宝剑四 | a young knight lying in repose on a stone tomb in a chapel, hands in prayer, three swords on the wall and one beneath him, a stained-glass window |
| 宝剑五 | a smirking young man gathering swords while two defeated figures walk away, a jagged windswept sky |
| 宝剑六 | a ferryman poling a boat carrying a cloaked figure and a child across calm water, six swords standing in the boat |
| 宝剑七 | a young man sneaking away from a camp carrying five swords, two left behind, glancing over his shoulder |
| 宝剑八 | a blindfolded, loosely bound young man standing among eight swords planted in the ground, a castle on a cliff behind |
| 宝剑九 | a young man sitting up in bed with his face in his hands, nine swords on the dark wall behind him |
| 宝剑十 | a young man lying face down under a dark sky with ten swords in his back, a golden dawn breaking on the horizon, solemn not gory |
| 宝剑侍从 | an alert young page on a windy hill holding a sword upright, clouds and birds swirling |
| 宝剑骑士 | a fierce young knight charging on a galloping horse with sword raised, storm clouds and bending trees |
| 宝剑王后 | a stern, clear-eyed queen on a throne in the clouds, holding an upright sword, one hand raised, butterflies carved on the throne |
| 宝剑国王 | a stern young king on a throne in the clouds holding an upright sword, butterflies and crescent moons carved on the throne |
| 星币王牌 | a glowing hand from a cloud holding a golden pentacle above a garden, an archway of roses leading to mountains |
| 星币二 | a young man dancing while juggling two pentacles linked by an infinity loop, ships riding high waves behind |
| 星币三 | a young stonemason at work in a cathedral while a monk and an architect hold plans, three pentacles carved in the arch |
| 星币四 | a young man on a stool clutching a pentacle to his chest, one on his crown and two under his feet, a city behind |
| 星币五 | two figures in rags trudging through snow past a lit stained-glass church window with five pentacles |
| 星币六 | a young merchant in fine robes holding balanced scales and giving coins to two kneeling figures |
| 星币七 | a young farmer leaning on a hoe and studying seven pentacles growing on a green vine |
| 星币八 | a young craftsman at a workbench carving pentacles, six finished pentacles displayed on a post |
| 星币九 | an elegant young figure in a robe embroidered with flowers standing in a vineyard, a hooded falcon on his gloved hand, nine pentacles among the vines |
| 星币十 | an old man with two white dogs beneath an archway, a young couple and a child, ten pentacles arranged like the Tree of Life |
| 星币侍从 | a studious young page in a green field holding up a pentacle and gazing at it intently |
| 星币骑士 | a steady young knight sitting still on a heavy black horse holding a pentacle, freshly plowed fields |
| 星币王后 | a nurturing queen on a throne in a blooming garden holding a pentacle in her lap, a rabbit at her feet |
| 星币国王 | a prosperous young king on a throne decorated with bulls, grapevines covering his robe, holding a pentacle and a scepter, a castle behind |
