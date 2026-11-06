"""Original eight-second cinematic hook. Requires authorized 1999–2001 daily OHLC.
Only initialize() or the CLI reads caller-specified market observations.
"""
from render import *
from effects import overlay_glow
from PIL import ImageEnhance
import time
DAILY=None
P=T=START=0
DUR=8;FPS=30

def initialize(data):
 global DAILY,P,T,START
 if data.empty or not data.ohlc_verified.all():
  raise ValueError('The cinematic hook requires verified daily OHLC on every row. Use render.py for close-only data.')
 DAILY=data.copy().reset_index(drop=True)
 if DAILY.iloc[0].date != pd.Timestamp('1999-01-05') or DAILY.iloc[-1].date<pd.Timestamp('2001-09-28'):
  raise ValueError('The fixed historical hook requires daily TAIEX observations starting 1999-01-05 and reaching at least 2001-09-28.')
 peak=DAILY[(DAILY.date>='2000-01-01')&(DAILY.date<='2000-12-31')]
 if peak.empty:raise ValueError('Missing 2000 observations for the historical hook')
 P=int(peak.close.idxmax())
 trough=DAILY[(DAILY.index>P)&(DAILY.date<='2001-09-28')]
 if trough.empty:raise ValueError('Missing observations after the 2000 peak')
 T=int(trough.close.idxmin());START=max(0,P-25)
 if T<=P:raise ValueError('Hook requires the trough to follow the observed peak')

Y,X=np.mgrid[0:H,0:W];RAD=np.exp(-(((X-370)/470)**2+((Y-740)/600)**2))
F22=font(22);F20=font(20);F18=font(18);F14=font(14)

def glowing_text(im,xy,text,ft,color,blur=7,condense=1,opacity=1):
 box=ft.getbbox(text);tw=max(1,box[2]-box[0]);th=max(1,box[3]-box[1]);layer=Image.new('RGBA',(tw+40,th+40));dr=ImageDraw.Draw(layer);dr.text((20-box[0],20-box[1]),text,font=ft,fill=(*color,int(255*opacity)))
 if condense!=1:layer=layer.resize((int(layer.width*condense),layer.height),Image.Resampling.LANCZOS)
 glow=layer.filter(ImageFilter.GaussianBlur(blur));xy=(int(xy[0]-20*condense),int(xy[1]-20));im.paste(glow,xy,glow);im.paste(layer,xy,layer)

def idx_at(t):
 if t<2.1:return int(START+(P-START)*t/2.1)
 if t<4.733:return int(P+(T-P)*(t-2.1)/2.633)
 if t<6.967:return T
 return int(min(50,(t-6.967)/1.033*50))

def lightning(im,t,end,flash=True):
 age=t-4.567
 if not 0<=age<.8:return im
 strength=1 if age<.2 else max(0,1-(age-.2)/.6)
 ex,ey=end;pts=[]
 for k in range(12):
  u=k/11;x=ex+(1-u)*90+math.sin(k*4.7+int(age*30)*.5)*34*(1-u);y=u*ey;pts.append((x,y))
 # RGB additive light avoids squaring RGBA alpha during glow compositing.
 glow=Image.new('RGB',(W,H));gd=ImageDraw.Draw(glow)
 gd.line(pts,fill=tuple(int(v*strength) for v in (70,200,220)),width=12)
 for k in [4,6,8]:
  x,y=pts[k];gd.line([(x,y),(x-36,y+45),(x-18,y+82),(x-44,y+120)],fill=tuple(int(v*strength) for v in (60,140,160)),width=3)
 glow=glow.filter(ImageFilter.GaussianBlur(10))
 pool=Image.new('RGB',(W,H));pg=ImageDraw.Draw(pool);pg.ellipse((ex-145,ey-65,ex+145,ey+65),fill=tuple(int(v*strength) for v in (20,85,65)));pool=pool.filter(ImageFilter.GaussianBlur(17))
 im=Image.fromarray(np.clip(np.asarray(im).astype(np.uint16)+np.asarray(glow).astype(np.uint16)+np.asarray(pool).astype(np.uint16),0,255).astype(np.uint8));dr=ImageDraw.Draw(im)
 dr.line(pts,fill=tuple(int(v*strength) for v in (245,255,255)),width=4)
 for k in [4,6,8]:
  x,y=pts[k];dr.line([(x,y),(x-36,y+45),(x-18,y+82),(x-44,y+120)],fill=tuple(int(v*strength) for v in (140,210,220)),width=1)
 rng=np.random.default_rng(9417)
 angles=rng.uniform(0,math.tau,150);radii=np.sqrt(rng.uniform(0,1,150))*170;lifetimes=rng.uniform(.35,.85,150)
 for angle,radius,life in zip(angles,radii,lifetimes):
  if age>=life:continue
  dist=radius*min(1,age/.22);px=ex+math.cos(angle)*dist;py=ey+math.sin(angle)*dist*.58+age*15
  power=(1-age/life)**1.2;col=tuple(int(v*power) for v in (180,255,231));dr.ellipse((px-1,py-1,px+1,py+1),fill=col)
 if flash and age<.133:im=Image.blend(im,Image.new('RGB',(W,H),(220,239,241)),.35*(1-age/.133))
 return im

def frame(t):
 idx=idx_at(t);row=DAILY.iloc[idx];val=row.close;after=t>=2.1 and t<6.967;reference=DAILY.iloc[P].close if after else DAILY.iloc[0].close
 perf=(val/reference-1)*100;headercolor=GREEN if perf<0 else RED
 tint=np.array(headercolor)*.045
 arr=np.zeros((H,W,3),dtype=np.uint8);arr[:]=[4,6,7];arr=np.clip(arr.astype(float)+RAD[:,:,None]*tint,0,255).astype(np.uint8);im=Image.fromarray(arr);dr=ImageDraw.Draw(im)
 # True weekly aggregation only from sessions already reached, preserving actual partial-week close.
 hist=DAILY.iloc[:idx+1].set_index('date');weekly=hist.resample('W-FRI').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna();n=len(weekly)
 lo,hi=float(DAILY.iloc[:T+1].low.min())*.28,float(DAILY.iloc[:T+1].high.max())*1.07
 if t<2.1:lo=float(hist.low.min())*.93;hi=float(hist.high.max())*1.03
 if t>=6.967:lo,hi=float(DAILY.iloc[:51].low.min())*.9,float(DAILY.iloc[:51].high.max())*1.07
 def xp(j):return 560-(n-1-j)*595/max(55,n-1)
 def yp(v):return 1215-(v-lo)/(hi-lo)*745
 for tick in [2000,4000,6000,8000,10000]:
  yy=yp(tick)
  if not 480<yy<1215:continue
  dr.text((644,yy),f'{tick:,}',font=font(13,True),fill=(55,61,63))
 tails=np.asarray(im).copy()
 for j,r in enumerate(weekly.itertuples()):
  x=int(xp(j));c=np.array(RED if r.close>=r.open else GREEN);ystart=max(0,int(yp(r.close)));ystop=min(H,1270)
  if x<0 or x>=W or ystart>=ystop:continue
  ys=np.arange(ystart,ystop);alpha=.10*(1-(ys-ystart)/max(1,ystop-ystart))**2.0
  shade=np.clip(np.array([4,6,7])[None,:]+alpha[:,None]*c[None,:],0,255).astype(np.uint8)
  for xx in range(max(0,x-1),min(W,x+2)):tails[ys,xx]=np.maximum(tails[ys,xx],shade)
 im=Image.fromarray(tails);dr=ImageDraw.Draw(im)
 for tick in [2000,4000,6000,8000,10000]:
  yy=yp(tick)
  if 480<yy<1215:dr.line((0,yy,635,yy),fill=(9,13,16),width=1)
 for k in range(27):
  sx=(k*137+23)%W;sy=480+(k*181)%750;dr.point((sx,sy),fill=(22,30,33))
 for j,r in enumerate(weekly.itertuples()):
  x=xp(j);c=RED if r.close>=r.open else GREEN;y=yp(r.close);ww=min(6,max(2,595/max(55,n-1)*.57))
  if x<-5:continue
  dr.line((x,yp(r.high),x,yp(r.low)),fill=c,width=1)
  a,b=sorted([yp(r.open),yp(r.close)]);dr.rectangle((x-ww/2,a,x+ww/2,max(a+1,b)),fill=c)
 end=(xp(n-1),yp(val));flow=RED if val>=DAILY.iloc[max(0,idx-1)].close else GREEN
 im=overlay_glow(im,end,flow,t);dr=ImageDraw.Draw(im)
 # Matching information hierarchy, without copied logos/watermark.
 dr.text((44,126),'加權指數',font=F20,fill=WHITE);dr.text((134,132),'TAIEX',font=font(12,True),fill=(184,188,190))
 glowing_text(im,(42,155),f'{val:.2f}',NF[72],headercolor,blur=6,condense=.80)
 glowing_text(im,(44,224),row.date.strftime('%Y.%m.%d'),font(30,True),WHITE,blur=0,condense=.85);dr=ImageDraw.Draw(im)
 label=('較'+DAILY.iloc[P].date.strftime('%Y.%m.%d')+'高點') if after else ('較'+DAILY.iloc[0].date.strftime('%Y.%m.%d')+'收盤')
 dr.text((318,151),label,font=font(12),fill=WHITE);dr.rectangle((316,172,449,198),fill=tuple(int(x*.18) for x in headercolor));dr.text((322,173),f'{perf:+.2f}%',font=font(18,True),fill=headercolor)
 if .333<t<2.1:
  opacity=min(1,(t-.333)/.1,(2.1-t)/.1);glowing_text(im,(178,575),'萬點行情',F[52],(255,236,47),blur=7,opacity=opacity)
 if 2.333<t<6.967:
  dd=(val/DAILY.iloc[P].close-1)*100
  glowing_text(im,(220,565),f'{dd:.2f}%',NF[90],GREEN,blur=8,condense=.85,opacity=min(1,max(0,(6.967-t)/.134)))
 if 4.733<t<6.967:
  fade=min(1,max(0,(6.967-t)/.134));glowing_text(im,(170,694),f'{(DAILY.iloc[T].date-DAILY.iloc[P].date).days}天，收盤{(DAILY.iloc[T].close/DAILY.iloc[P].close-1)*100:.1f}%' ,F[32],WHITE,blur=0,opacity=fade);glowing_text(im,(174,740),f'觀測收盤：{DAILY.iloc[P].close:.2f} → {DAILY.iloc[T].close:.2f}',F20,WHITE,blur=0,opacity=fade)
 if t>=7.133:
  glowing_text(im,(188,585),'回到 1999',F[52],WHITE,blur=5,opacity=min(1,(t-7.133)/.067))
 dr=ImageDraw.Draw(im);dr.text((42,1248),'週K·使用者提供資料 · 1999–2001歷史片段',font=F14,fill=(121,132,136))
 im=lightning(im,t,end)
 if 2.1<=t<2.3:
  alpha=.35*(1-(t-2.1)/.2);im=Image.blend(im,Image.new('RGB',(W,H),(200,215,218)),alpha)
  if t<2.2:
   for k,yy in enumerate([480,533,609,718,805,923,1028,1135]):
    strip=im.crop((0,yy,W,yy+8+(k%3)*5));im.paste(strip,(18 if k%2 else -24,yy))
 return im

def main():
 p=argparse.ArgumentParser(description='Original cinematic hook; external authorized daily OHLC required.')
 p.add_argument('--data');p.add_argument('--output',default='output/cinematic_hook.mp4');p.add_argument('--fps',type=int,default=FPS);p.add_argument('--still',type=float)
 a=p.parse_args()
 try:
  initialize(load(input_path(a.data)));out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
  if a.still is not None:
   if not 0<=a.still<DUR:raise ValueError('Still timestamp must be within [0,8) seconds')
   frame(a.still).save(out.with_suffix('.png'));return
  silent=out.with_name(out.stem+'_silent.mp4');duration=encode_frames(frame,silent,DUR,a.fps,size=(W,H))
  from score_long import write_score
  wav=out.with_suffix('.wav');write_score(wav,duration,[],set(),set());mux_audio(silent,wav,out);print(out)
 except (ValueError,RuntimeError,OSError) as error:p.error(str(error))
if __name__=='__main__':main()
