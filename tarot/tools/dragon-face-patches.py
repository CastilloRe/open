#!/usr/bin/env python3
"""重画首页龙娘眨眼、说话用的闭眼和闭嘴补丁。

用法：python3 tarot/tools/dragon-face-patches.py 输出目录
输出目录里要先放好去掉黑底的立绘 dragon-cut.png（730×1255）。

做法：把眼睛（连同上睫毛）和嘴圈成一个多边形洞，用离眼眶稍远、较亮的皮肤往洞里做调和扩散，
填出一片和四周接得上的渐变皮肤；再按原画睫毛的颜色画一道中间粗、两头细的闭眼线（外眼角带两根睫毛尖），
嘴画一笔有粗细的小弧线。生成的三张 png 拷到 tarot/art/，再重新生成 art/dragon-live.js（见 tarot/README.md）。
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sp=sys.argv[1]
cut=Image.open(f'{sp}/dragon-cut.png').convert('RGBA')
A=np.asarray(cut).astype(np.float32)
H0,W0=A.shape[:2]

def poly_mask(pts):
    m=Image.new('L',(W0,H0),0); ImageDraw.Draw(m).polygon(pts,fill=255); return np.asarray(m)>0

def harmonic_fill(img, hole, region_pad=6, iters=900):
    """用洞外一圈的「皮肤色」往洞里扩散，得到平滑的渐变（洞外不是皮肤的像素，比如头发，不参与）。"""
    ys,xs=np.where(hole)
    y0,y1,x0,x1=ys.min()-region_pad,ys.max()+region_pad+1,xs.min()-region_pad,xs.max()+region_pad+1
    sub=img[y0:y1,x0:x1,:3].copy(); h=hole[y0:y1,x0:x1]
    r,g,b=sub[...,0],sub[...,1],sub[...,2]
    ring=np.asarray(Image.fromarray((h*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)))>0
    skin=(r>236)&(r>b+18)&(r>=g)&~ring
    known=skin
    out=sub.copy()
    mean=sub[skin].mean(axis=0)
    out[~known]=mean
    for _ in range(iters):
        p=np.pad(out,((1,1),(1,1),(0,0)),mode='edge')
        avg=(p[:-2,1:-1]+p[2:,1:-1]+p[1:-1,:-2]+p[1:-1,2:])/4
        out=np.where(known[...,None],sub,avg)
    res=img.copy(); res[y0:y1,x0:x1,:3]=np.where(h[...,None],out,img[y0:y1,x0:x1,:3])
    return res

def lash_color(hole):
    px=A[hole][:,:3]; lum=px.mean(axis=1)
    dark=px[lum<=np.percentile(lum,12)]
    return tuple(int(v) for v in dark.mean(axis=0))

S=6
def bez(p0,p1,p2,n=40):
    t=np.linspace(0,1,n)[:,None]; return (1-t)**2*np.array(p0)+2*(1-t)*t*np.array(p1)+t**2*np.array(p2)

def taper_polygon(pts, w_fn):
    pts=np.array(pts,dtype=float); left=[]; right=[]
    for i in range(len(pts)):
        a=pts[max(0,i-1)]; b=pts[min(len(pts)-1,i+1)]; d=b-a; n=np.array([-d[1],d[0]]); n/=np.linalg.norm(n)+1e-9
        w=w_fn(i/(len(pts)-1))/2
        left.append(pts[i]+n*w); right.append(pts[i]-n*w)
    return [tuple(p) for p in left+right[::-1]]

def make(hole_pts, box, draw_fn):
    hole=poly_mask(hole_pts)
    col=lash_color(hole)
    filled=harmonic_fill(A,hole)
    x0,y0,x1,y1=box
    patch=Image.fromarray(np.clip(filled[y0:y1,x0:x1],0,255).astype(np.uint8),'RGBA')
    big=patch.resize(((x1-x0)*S,(y1-y0)*S),Image.LANCZOS)
    layer=Image.new('RGBA',big.size,(0,0,0,0)); d=ImageDraw.Draw(layer)
    draw_fn(d,col,lambda x,y:((x-x0)*S,(y-y0)*S))
    big.alpha_composite(layer.filter(ImageFilter.GaussianBlur(S*0.25)))
    patch=big.resize(patch.size,Image.LANCZOS)
    # 补丁只在洞和画线的地方不透明，边缘羽化一像素
    m=Image.fromarray((hole[y0:y1,x0:x1]*255).astype(np.uint8),'L').filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    patch.putalpha(m)
    return patch,col

def eye_draw(p_outer,p_mid,p_inner,crease_shift,flick_dir):
    def f(d,col,T):
        line=[T(x,y) for x,y in bez(p_outer,p_mid,p_inner)]
        # 上眼皮的褶：很淡的一道
        cr=[T(x,y-crease_shift) for x,y in bez(p_outer,(p_mid[0],p_mid[1]-1.5),p_inner)][4:-6]
        d.line(cr,fill=col+(28,),width=int(S*0.7),joint='curve')
        # 闭眼线：外眼角那头粗，往内眼角收细
        d.polygon(taper_polygon(line,lambda t:S*(2.9*(1-t)**0.6+0.6)),fill=col+(255,))
        # 外眼角的两根睫毛
        ox,oy=T(*p_outer)
        for k,(dx,dy) in enumerate(flick_dir):
            d.line([(ox,oy),(ox+dx*S,oy+dy*S)],fill=col+(235,),width=int(S*(1.3-0.3*k)))
    return f

def mouth_draw(d,col,T):
    c=(150,72,90)
    pts=[T(x,y) for x,y in bez((373.5,186.5),(380.5,191.5),(388,186))]
    d.polygon(taper_polygon(pts,lambda t:S*(0.9+0.9*np.sin(np.pi*t))),fill=c+(235,))

eyeL_hole=[(323,156),(330,153),(340,152),(350,153),(357,157),(359,165),(357,174),(350,181),(340,184),(331,183),(324,181),(320,175),(321,164)]
eyeR_hole=[(383,140),(387,134),(394,131),(404,131),(411,132),(416,136),(416,143),(412,150),(405,156),(396,158),(388,156),(383,150)]
mouth_hole=[(370,184),(374,181),(381,180),(388,181),(392,184),(391,190),(386,194),(379,195),(373,193),(370,189)]
boxL=(314,146,364,190); boxR=(378,124,422,164); boxM=(364,176,398,200)
eL,cl=make(eyeL_hole,boxL,eye_draw((321,171),(339,180),(357,168),5,[(-3.2,1.2),(-2.6,2.8)]))
eR,cr=make(eyeR_hole,boxR,eye_draw((415,141),(399,155),(383,149),5,[(3.2,0.6),(2.8,2.6)]))
mo,cm=make(mouth_hole,boxM,mouth_draw)
print('lash colours',cl,cr)
for n,p,b in (('dragon-eye-l',eL,boxL),('dragon-eye-r',eR,boxR),('dragon-mouth',mo,boxM)):
    p.save(f'{sp}/{n}.png'); print(n,b[:2],p.size)
face=(300,100,440,215)
mod=cut.copy()
for p,b in ((eL,boxL),(eR,boxR),(mo,boxM)): mod.alpha_composite(p,b[:2])
o=cut.crop(face); m=mod.crop(face)
pv=Image.new('RGBA',(o.width*2+6,o.height),(255,255,255,255)); pv.alpha_composite(o,(0,0)); pv.alpha_composite(m,(o.width+6,0))
pv.resize((pv.width*4,pv.height*4),Image.LANCZOS).save(f'{sp}/patch-preview2.png')
