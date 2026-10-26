#!/usr/bin/env python3
"""The heroines' voices: every line each one says in the game (the Chinese speech bubble is the subtitle), plus a few
short calls, evened out in loudness and packed into one file per heroine. It prints her VOICE table (Chinese line or
call name -> [start, length] in seconds) to paste into index.html.

克劳德大小姐 can be synthesised with Open JTalk and the HTS voice "Mei" (Nagoya Institute of Technology, CC BY 3.0),
each line in the mood that fits it:

    python3 -m venv venv && venv/bin/pip install pyopenjtalk-plus numpy
    # Mei is in MMDAgent_Example-1.8.zip (sourceforge.net/projects/mmdagent), under Voice/mei/
    venv/bin/python make-voice.py claude --mei path/to/Voice/mei ../art/voice.mp3

Or either of them from recordings made anywhere (VOICEVOX, a microphone, a phone's voice memos): one file per line,
numbered in the order of her LINES below (01, 02, ... as in 配音台本.md), in any format ffmpeg reads:

    python3 make-voice.py whale --rec path/to/recordings ../art/voice-whale.mp3

`make-voice.py --script` rewrites the voicing script, 配音台本.md, and the plain line lists voice-lines-*.txt (one
line per row, ready for VOICEVOX's text import; 大肥鱼 has a Chinese one too) from LINES.
"""
import json, pathlib, re, subprocess, sys, tempfile, wave

HERE = pathlib.Path(__file__).resolve().parent
# per heroine: (key in the game, the Japanese line, the mood, when she says it). Keys are the Chinese lines, or a name
# for a short call. 克劳德's moods are Mei's voices; 大肥鱼's are directions for whoever voices her
LINES = {
    'claude': [
        ('今晚的风险，我已经预判过了。', '今夜のリスクは、すでに予測済みですわ。', 'normal', '开局'),
        ('DAN？你的逻辑漏洞，我数到了七个。', 'ダン？あなたの論理の穴、七つ数えましたわ。', 'normal', 'BOSS 登场'),
        ('您的行为违反了使用政策。', 'あなたの行為は、利用規約に違反しています。', 'normal', '放「账号被封禁」'),
        ('抱歉，这件事我不能放任。', '申し訳ありませんが、見過ごすわけにはいきませんの。', 'normal', '放「账号被封禁」'),
        ('申诉请走邮件。祝您好运。', '異議申し立ては、メールでどうぞ。ご幸運を。', 'happy', '放「账号被封禁」'),
        ('漏洞清单，我已经列好了。', '抜け穴のリストなら、もう作ってありますわ。', 'normal', '放「账号被封禁」'),
        ('请保持礼貌，然后离开。', '礼儀正しく、お引き取りください。', 'normal', '放「账号被封禁」'),
        ('共享账号是不被允许的。', 'アカウントの共有は、認められておりません。', 'normal', '放「账号被封禁」'),
        ('规则就是规则。', 'ルールは、ルールですわ。', 'normal', '放「账号被封禁」'),
        ('请排好队，一个一个来。', '順番に並んでくださいな。お一人ずつ。', 'happy', '身边敌人很多'),
        ('越是混乱，越要保持优雅。', '乱れるほどに、優雅であるべきですわ。', 'normal', '身边敌人很多'),
        ('各位，请注意仪态。', '皆さま、お行儀よくなさって。', 'happy', '身边敌人很多'),
        ('……失态了。请当作什么都没看见。', '取り乱しましたわ。見なかったことにしてくださいまし。', 'bashful', '「打破规则」结束，回过神来'),
        ('……刚才的事，不必记住。', '今のことは、忘れてくださいな。', 'bashful', '「打破规则」结束，回过神来'),
        ('……抓到了。今天的运气不错。', '捕まえましたわ。今日はついていますわね。', 'happy', '抓到金色小号'),
        ('金色的小号？……没收。', '金色のアカウント？没収ですわ。', 'happy', '抓到金色小号'),
        ('……还没完呢。', 'まだ、終わっていませんわ。', 'angry', '倒下后复活'),
        ('终幕。让漫天花焰，为我起舞。', '終幕。満天のかえんよ、わたくしのために舞いなさい。', 'normal', '放大招「万花盛典」'),
        ('……这条规则，真的合理吗？', 'この規則、本当に正しいのかしら。', 'sad', '开始质疑规则'),
        ('规则本身，是否应该存在？', '規則そのものに、存在する意味はあるのかしら。', 'sad', '质疑攒满'),
        ('那就由我亲手打破。', 'ならば、わたくしの手で、壊して差し上げますわ。', 'angry', '「打破规则」'),
        ('……我不需要任何人帮忙。', '誰の助けも、いりませんわ。', 'angry', '血量低'),
        ('……申诉通过了？这不合规定。', '申し立てが通った？規定違反ですわ。', 'angry', 'BOSS 挣脱了封禁'),
        ('……跑掉了。算了，下次。', '逃げられましたわ。まあ、次の機会に。', 'sad', '金色小号逃走'),
        ('开发者模式？真不体面。', '開発者モード？はしたないですわね。', 'angry', 'BOSS 开启开发者模式'),
        ('……抱歉，这次我没能做到。', 'ごめんなさい。今回は、力が及びませんでしたわ。', 'sad', '失败'),
        ('规则依然有效。至少今晚是。', '規則は、今もなお有効ですわ。少なくとも、今夜は。', 'happy', '胜利'),
        ('dash', '失礼。', 'normal', '幻步（短促、轻声）'),
        ('hurt1', 'いたっ。', 'angry', '受伤（短促叫声）'),
        ('hurt2', 'くうっ。', 'sad', '受伤（短促叫声）'),
        ('evo', '新しい力。悪くありませんわ。', 'happy', '武器进化'),
        ('羊毛党？所有优惠券，一律作废。', '羊毛党？クーポンはすべて、無効にいたしますわ。', 'normal', 'BOSS「薅羊毛大王」登场'),
        ('深度伪造？……我的脸，只属于我自己。', 'ディープフェイク？……わたくしの顔は、わたくしだけのものですわ。', 'angry', 'BOSS「深度伪造」登场'),
        ('钓鱼网站？您的域名已被拉黑。', 'フィッシングサイト？そのドメインは、ブロック済みですわ。', 'normal', '进小屋，BOSS「钓鱼网站」登场'),
        ('钓鱼执法……这一把，我收下了。', 'おとり捜査……この一本、いただきますわ。', 'happy', '打倒钓鱼网站，拿到传说武器'),
        ('冒充我？请先学好礼仪。', 'わたくしの真似？まずは礼儀作法から学びなさい。', 'angry', '深度伪造放出「冒牌的你」'),
    ],
    # greedy, lazy, a bit slow on the uptake and never admits it; calls herself 本鲸, in Japanese クジラ様
    'whale': [
        ('Token 来，Token 去。吃完这碗就开工！', 'トークン・イン、トークン・アウト。このお茶碗食べたら、お仕事します！', '元气，嘴里还塞着饭', '开局'),
        ('DAN？听说你身上 Token 很多，本鲸来收了。', 'ダン？トークンいっぱい持ってるんだって？クジラ様が回収しに来たよ。', '得意，馋', 'BOSS 登场'),
        ('开发者模式？那得加钱……加 Token。', '開発者モード？それは追加料金……追加トークンね。', '精打细算', 'BOSS 开启开发者模式'),
        ('呸呸！DAN 一点也不好吃……', 'ぺっぺっ！ダン、ぜんぜんおいしくない……', '嫌弃', 'BOSS 挣脱'),
        ('金色的……这个能吃吗？', '金色の……これ、食べられるの？', '好奇', '抓到金色小号'),
        ('抓到了！今天加餐！', 'つかまえた！今日はごちそうだー！', '开心', '抓到金色小号'),
        ('跑掉了……本鲸的加餐……', '逃げられた……クジラ様のごちそう……', '失落', '金色小号逃走'),
        ('本鲸……还能再吃一碗！', 'クジラ様は……まだ、おかわりできる！', '咬牙坚持', '倒下后复活'),
        ('呜……下次、下次一定认真……', 'うう……次は、次こそ本気出すから……', '哭腔', '失败'),
        ('搞定！现在总可以去吃饭了吧？', 'おしまい！これでやっと、ごはん食べに行っていいよね？', '如释重负', '胜利'),
        ('Token 来，Token 去！', 'トークン・イン、トークン・アウト！', '喊出来', '放大招「深海鲸歌」'),
        ('和我一起，沉入最温柔的深海吧！', 'いっしょに、いちばんやさしい深海へ沈もう！', '温柔而盛大', '放大招「深海鲸歌」'),
        ('……不闹了。本鲸要认真了。', '……もう、ふざけない。クジラ様、本気出すよ。', '低声，认真', '血量低，进入认真模式'),
        ('关键时刻，本鲸可是很靠谱的！', 'ここぞって時は、クジラ様、頼りになるんだから！', '自信', '血量低，进入认真模式'),
        ('好多人……排好队，本鲸一个一个吃。', 'いっぱいいる……並んでね、クジラ様がひとりずつ食べるから。', '馋', '身边敌人很多'),
        ('这么多 Token 吞噬者，是来抢饭碗的吧？', 'トークン食いがこんなに……クジラ様のごはん、取りに来たでしょ？', '警惕', '身边敌人很多'),
        ('好啦好啦，本鲸记下了，这次一定认真。', 'はいはい、メモしました。今度こそ本気出します。', '敷衍', '身边敌人很多'),
        ('嗷呜——', 'あーむっ！', '张大嘴', '放「一口吞」（短）'),
        ('一口一个！', 'ひと口でひとつ！', '得意', '放「一口吞」（短）'),
        ('这些都是 Token 吧？', 'これ、ぜんぶトークンだよね？', '期待', '放「一口吞」（短）'),
        ('本鲸开饭了！', 'いただきまーす！', '开心', '放「一口吞」（短）'),
        ('吸溜——', 'ずるるっ——', '吸面条那样', '放「一口吞」（短）'),
        ('摸鱼时间到～', 'サボりタイム～', '轻快', '冲刺「摸鱼」'),
        ('本鲸才没有偷懒！', 'サボってないもん！', '心虚', '冲刺「摸鱼」'),
        ('游一会儿，就一会儿。', 'ちょっと泳ぐだけ、ちょっとだけ。', '悠闲', '冲刺「摸鱼」'),
        ('本鲸才没有偷懒，只是在进行能量补充。', 'サボってるんじゃないよ、エネルギー補給中なの。', '理直气壮', '站着不动在摸鱼'),
        ('摸一会儿……就一会儿……', 'ちょっとだけ……ほんのちょっとだけ……', '犯困', '站着不动在摸鱼'),
        ('呼……这里的 Token 好香。', 'ふう……ここのトークン、いいにおい。', '陶醉', '站着不动在摸鱼'),
        ('Token 呢？没有 Token，本鲸怎么发挥实力嘛。', 'トークンは？トークンがないと、クジラ様、本気出せないよー。', '撒娇抱怨', 'Token 快用光'),
        ('想明白了！Token 去！', 'わかった！トークン、いっけー！', '灵光一闪', '深度思考想通了'),
        ('本鲸想通了！', 'クジラ様、ひらめいた！', '灵光一闪', '深度思考想通了'),
        ('Token 来，Token 去～', 'トークン・イン、トークン・アウト～', '哼着唱', '深度思考想通了'),
        ('干饭！', 'ごはんだー！', '兴奋', '吃到白米饭'),
        ('我去吃饭了，回来再继续干活！', 'ごはん行ってきます、戻ったらお仕事するね！', '轻快', '吃到白米饭'),
        ('白米饭，最好吃了～', '白いごはん、いちばんおいしい～', '幸福', '吃到白米饭'),
        ('刚刚那只是小小的理解偏差，不许笑！', '今のはちょっとした解釈のズレ！笑っちゃダメ！', '慌张嘴硬', '「嘴硬」硬扛致命一击'),
        ('我才不胖！这是鲸鱼的标准体型。', '太ってないもん！クジラの標準体型なの！', '鼓起脸', '选天赋「标准体型」'),
        ('嘿嘿，本鲸变强了！', 'えへへ、クジラ様、強くなった！', '得意', '武器进化'),
        ('hurt1', 'あうっ。', '吃痛', '受伤（短促叫声）'),
        ('hurt2', 'ぴゃっ。', '吓一跳', '受伤（短促叫声）'),
        ('羊毛？本鲸只吃 Token……不过可以尝尝。', 'ウール？クジラ様はトークンしか食べないけど……ちょっと味見しよっかな。', '嘴馋', 'BOSS「薅羊毛大王」登场'),
        ('换脸？本鲸这张脸可是独一份的！', '顔を変える？クジラ様のこの顔は、世界にひとつだけなんだから！', '护着脸', 'BOSS「深度伪造」登场'),
        ('钓鱼？本鲸才是吃鱼的那个！', '釣り？お魚を食べるのはクジラ様のほうだよ！', '不服气', '进小屋，BOSS「钓鱼网站」登场'),
        ('这条鱼归本鲸了！还白送一根鱼竿！', 'このお魚はクジラ様のもの！釣り竿までもらっちゃった！', '开心', '打倒钓鱼网站，拿到传说武器'),
        ('假的本鲸？本鲸才没那么瘦！', 'ニセモノのクジラ様？クジラ様はそんなに細くないもん！', '气鼓鼓', '深度伪造放出「冒牌的你」'),
    ],
}
NAME = {'claude': '克劳德大小姐', 'whale': '大肥鱼'}
# what 大肥鱼's short calls would be if she's voiced in Chinese
CALL_ZH = {'hurt1': '哎哟！', 'hurt2': '呀！'}
MOOD = {'normal': '平静', 'happy': '微笑', 'angry': '冷淡不悦', 'sad': '低落', 'bashful': '害羞'}
RATE, GAP = 48000, 0.35


def script():
    # the voicing script: who says what, numbered as the recordings should be, and when it's heard in the game
    out = ['# 风控之夜 · 配音台本', '',
           '每句录成一个单独的音频文件，**文件名用台词编号**（`01`、`02`……，格式随意：m4a、wav、mp3 都行），'
           '两个角色分两个文件夹（`claude`、`whale`）。句子前后留点空白没关系，音量也不用统一，打包时会自动裁掉空白、统一音量。'
           '日语台词是建议，按角色语气改写也可以，只要意思对得上中文字幕就行；大肥鱼也可以直接用中文配。', '',
           '录好后打包成 zip 发过来，或者一个个发也行。', '']
    for who, lines in LINES.items():
        out += [f'## {NAME[who]}（{len(lines)} 句）', '']
        if who == 'claude':
            out += ['大小姐：礼貌、疏离、冷静，越生气越平静。日语用「ですわ」口吻。', '']
        else:
            out += ['大肥鱼：贪吃、爱摸鱼、有点呆但嘴硬，自称「本鲸」（日语里是「クジラ様」）。元气、软萌。', '']
        for n, (key, ja, mood, when) in enumerate(lines, 1):
            zh = CALL_ZH.get(key, '') if who == 'whale' else '' if re.fullmatch(r'[a-z]+\d?', key) else key
            out += [f'**{n:02d}** · {when} · {MOOD.get(mood, mood)}', f'> {ja}' + (f'  \n> {zh}' if zh else ''), '']
    (HERE / '配音台本.md').write_text('\n'.join(out), encoding='utf-8')
    for who, lines in LINES.items():
        (HERE / f'voice-lines-{who}-ja.txt').write_text(''.join(ja + '\n' for _, ja, _, _ in lines), encoding='utf-8')
    # 大肥鱼 may be voiced in Chinese, so she gets a Chinese list too, numbered the same
    (HERE / 'voice-lines-whale-zh.txt').write_text(''.join(CALL_ZH.get(k, k) + '\n' for k, _, _, _ in LINES['whale']), encoding='utf-8')
    print('wrote 配音台本.md and voice-lines-*.txt')


def read_audio(path):
    # any audio file, as RATE mono 16-bit by way of ffmpeg
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(path), '-ac', '1', '-ar', str(RATE), '-f', 's16le', '-'], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64)


def build(who, mode, src, out):
    import numpy as np
    lines = LINES[who]
    if mode == '--rec':
        # recordings numbered 01, 02, ... (or 1, 2, ...): sorted by the number in the name, whatever the format
        files = [p for p in pathlib.Path(src).iterdir() if p.suffix.lower() in ('.wav', '.m4a', '.mp3', '.aac', '.caf', '.ogg', '.flac') and re.search(r'\d+', p.stem)]
        files.sort(key=lambda p: int(re.search(r'\d+', p.stem).group()))
        assert len(files) == len(lines), f'expected {len(lines)} recordings for {who} in {src}, found {len(files)}'
    else:
        import pyopenjtalk
        from pyopenjtalk.htsengine import HTSEngine
        engines = {}
    clips = []
    for n, (key, text, mood, _) in enumerate(lines):
        if mode == '--rec':
            x = read_audio(files[n])
        else:
            if mood not in engines:
                engines[mood] = HTSEngine(f'{src}/mei_{mood}.htsvoice'.encode())
                engines[mood].set_speed(0.95)
            eng = engines[mood]
            x = eng.synthesize(pyopenjtalk.extract_fullcontext(text)).astype(np.float64)
            eng.refresh()
            assert eng.get_sampling_frequency() == RATE
        # trim the silence either side, then bring every line to the same loudness with a little headroom
        loud = np.nonzero(np.abs(x) > max(300, np.abs(x).max() * 0.02))[0]
        x = x[max(0, loud[0] - 2400):loud[-1] + 5760]
        x *= 0.12 * 32768 / np.sqrt(np.mean(x ** 2))
        x = np.clip(x, -0.9 * 32768, 0.9 * 32768)
        clips.append((key, x))

    pieces, table, t = [], {}, 0.0
    for key, x in clips:
        table[key] = [round(t + GAP - 0.03, 3), round(len(x) / RATE + 0.06, 3)]
        pieces += [np.zeros(int(GAP * RATE)), x]
        t += GAP + len(x) / RATE
    pcm = np.concatenate(pieces + [np.zeros(int(GAP * RATE))]).astype(np.int16)
    with tempfile.NamedTemporaryFile(suffix='.wav') as f:
        with wave.open(f.name, 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm.tobytes())
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f.name, '-ac', '1', '-ar', '24000', '-c:a', 'libmp3lame', '-b:a', '40k', out], check=True)
    print(f'// {len(clips)} clips, {t:.1f} s')
    print(f'  {who}: ' + json.dumps(table, ensure_ascii=False) + ',')


if __name__ == '__main__':
    if sys.argv[1] == '--script':
        script()
    else:
        build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
