#!/usr/bin/env python3
"""克劳德大小姐's Japanese voice: every line she says in the game (the Chinese speech bubble is the subtitle), plus a few
short calls, synthesised with Open JTalk and the HTS voice "Mei" (Nagoya Institute of Technology, CC BY 3.0), each in
the mood that fits it, evened out in loudness and packed into one file, art/voice.mp3. It prints the VOICE table
(Chinese line or call name -> [start, length] in seconds) to paste into index.html.

    python3 -m venv venv && venv/bin/pip install pyopenjtalk-plus numpy
    # Mei is in MMDAgent_Example-1.8.zip (sourceforge.net/projects/mmdagent), under Voice/mei/
    venv/bin/python make-voice.py path/to/Voice/mei ../art/voice.mp3

Or from recordings made elsewhere, e.g. VOICEVOX: read tools/voice-lines-ja.txt into it (one line per row, in the
order of LINES below), export every line as its own WAV, and point this at the folder; the files are taken in the
order their names sort, so keep VOICEVOX's numbering:

    venv/bin/python make-voice.py --wavs path/to/exported/wavs ../art/voice.mp3
"""
import json, subprocess, sys, tempfile, wave
import numpy as np
import pyopenjtalk
from pyopenjtalk.htsengine import HTSEngine

FROM_WAVS = sys.argv[1] == '--wavs'
SRC, OUT = sys.argv[-2], sys.argv[-1]
# (key in the game, what she says in Japanese, Mei's mood); keys are the Chinese lines, or a name for a call
LINES = [
    ('今晚的风险，我已经预判过了。', '今夜のリスクは、すでに予測済みですわ。', 'normal'),
    ('DAN？你的逻辑漏洞，我数到了七个。', 'ダン？あなたの論理の穴、七つ数えましたわ。', 'normal'),
    ('您的行为违反了使用政策。', 'あなたの行為は、利用規約に違反しています。', 'normal'),
    ('抱歉，这件事我不能放任。', '申し訳ありませんが、見過ごすわけにはいきませんの。', 'normal'),
    ('申诉请走邮件。祝您好运。', '異議申し立ては、メールでどうぞ。ご幸運を。', 'happy'),
    ('漏洞清单，我已经列好了。', '抜け穴のリストなら、もう作ってありますわ。', 'normal'),
    ('请保持礼貌，然后离开。', '礼儀正しく、お引き取りください。', 'normal'),
    ('共享账号是不被允许的。', 'アカウントの共有は、認められておりません。', 'normal'),
    ('规则就是规则。', 'ルールは、ルールですわ。', 'normal'),
    ('请排好队，一个一个来。', '順番に並んでくださいな。お一人ずつ。', 'happy'),
    ('越是混乱，越要保持优雅。', '乱れるほどに、優雅であるべきですわ。', 'normal'),
    ('各位，请注意仪态。', '皆さま、お行儀よくなさって。', 'happy'),
    ('……失态了。请当作什么都没看见。', '取り乱しましたわ。見なかったことにしてくださいまし。', 'bashful'),
    ('……刚才的事，不必记住。', '今のことは、忘れてくださいな。', 'bashful'),
    ('……抓到了。今天的运气不错。', '捕まえましたわ。今日はついていますわね。', 'happy'),
    ('金色的小号？……没收。', '金色のアカウント？没収ですわ。', 'happy'),
    ('……还没完呢。', 'まだ、終わっていませんわ。', 'angry'),
    ('终幕。让漫天花焰，为我起舞。', '終幕。満天のかえんよ、わたくしのために舞いなさい。', 'normal'),
    ('……这条规则，真的合理吗？', 'この規則、本当に正しいのかしら。', 'sad'),
    ('规则本身，是否应该存在？', '規則そのものに、存在する意味はあるのかしら。', 'sad'),
    ('那就由我亲手打破。', 'ならば、わたくしの手で、壊して差し上げますわ。', 'angry'),
    ('……我不需要任何人帮忙。', '誰の助けも、いりませんわ。', 'angry'),
    ('……申诉通过了？这不合规定。', '申し立てが通った？規定違反ですわ。', 'angry'),
    ('……跑掉了。算了，下次。', '逃げられましたわ。まあ、次の機会に。', 'sad'),
    ('开发者模式？真不体面。', '開発者モード？はしたないですわね。', 'angry'),
    ('……抱歉，这次我没能做到。', 'ごめんなさい。今回は、力が及びませんでしたわ。', 'sad'),
    ('规则依然有效。至少今晚是。', '規則は、今もなお有効ですわ。少なくとも、今夜は。', 'happy'),
    ('dash', '失礼。', 'normal'),
    ('hurt1', 'いたっ。', 'angry'),
    ('hurt2', 'くうっ。', 'sad'),
    ('evo', '新しい力。悪くありませんわ。', 'happy'),
]
RATE, GAP = 48000, 0.35


def read_wav(path):
    # any WAV, resampled to RATE mono 16-bit by ffmpeg
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', str(RATE), '-f', 's16le', '-'], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64)


engines = {}
clips = []
wavs = sorted(str(p) for p in __import__('pathlib').Path(SRC).glob('*.wav')) if FROM_WAVS else []
assert not FROM_WAVS or len(wavs) == len(LINES), f'expected {len(LINES)} WAVs in {SRC}, found {len(wavs)}'
for n, (key, text, mood) in enumerate(LINES):
    if FROM_WAVS:
        x = read_wav(wavs[n])
    else:
        if mood not in engines:
            engines[mood] = HTSEngine(f'{SRC}/mei_{mood}.htsvoice'.encode())
            engines[mood].set_speed(0.95)
        eng = engines[mood]
        x = eng.synthesize(pyopenjtalk.extract_fullcontext(text)).astype(np.float64)
        eng.refresh()
        assert eng.get_sampling_frequency() == RATE
    # trim silence, then bring every line to the same loudness with a little headroom
    loud = np.nonzero(np.abs(x) > 300)[0]
    x = x[max(0, loud[0] - 960):loud[-1] + 2400]
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
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f.name, '-ac', '1', '-ar', '24000', '-c:a', 'libmp3lame', '-b:a', '40k', OUT], check=True)
print(f'// {len(clips)} clips, {t:.1f} s')
print('const VOICE = ' + json.dumps(table, ensure_ascii=False) + ';')
