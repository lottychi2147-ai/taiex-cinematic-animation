"""Original dynamic camera, particles, rings and stable HUD; no bundled full history."""
import camera_film as base
from camera_film import *
from PIL import ImageChops
from branding import stamp, validate_label
SOURCE_LABEL='User-supplied authorized data'
WATERMARK='紀順文X小狐AI'
ASOF=''
EVENT_CUES=[]

def initialize(data, *, source_label='User-supplied authorized data', watermark='紀順文X小狐AI', demo=False, duration=12):
 global SOURCE_LABEL,WATERMARK,ASOF,EVENT_CUES
 SOURCE_LABEL=validate_label(source_label);WATERMARK=validate_label(watermark)
 base.initialize(data,demo=demo,duration=duration)
 for name in ('DAILY','N','SEG','RAW_O','RAW_H','RAW_L','RAW_C','CUMCLOSE','DAY_RET','ANNUAL','CAM'):
  globals()[name]=getattr(base,name)
 ASOF=DAILY.date.iloc[-1].strftime('%Y.%m.%d');EVENT_CUES=[s for s in SEG if s['event']]

CYAN=(78,221,255); GOLD3=(255,214,91)
FX_SEED=np.random.default_rng(86026)
PARTICLES=[tuple(x) for x in np.column_stack([FX_SEED.uniform(0,math.tau,95),FX_SEED.uniform(60,320,95),FX_SEED.uniform(.6,1.45,95),FX_SEED.uniform(1,3,95)])]
STARS=[tuple(x) for x in np.column_stack([FX_SEED.uniform(0,720,42),FX_SEED.uniform(500,1190,42),FX_SEED.uniform(.5,1.5,42)])]

def centered(dr,text,y,ft,color,x=360):
 b=dr.textbbox((0,0),text,font=ft);dr.text((x-(b[2]-b[0])/2,y),text,font=ft,fill=color)

def small_glow(im,layer,radius=10,strength=.85):
 # Light is rendered at one-third resolution, keeping full-resolution text crisp.
 glow=layer.resize((240,427),Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(radius/3)).resize((W,H),Image.Resampling.BILINEAR)
 if strength!=1:glow=glow.point(lambda v:round(v*strength))
 return ImageChops.add(im,glow)

def cue_age(t):
 if 2.1<=t<3.6:return t-2.1,'crash'
 if 4.567<=t<6.2:return t-4.567,'crash'
 for s in EVENT_CUES:
  age=t-s['start']
  if 0<=age<1.5:return age,('gold' if s['event']['date'] in GOLD else 'crash' if s['event']['date'] in CRASH else 'event')
 if 209<=t<210.5:return t-209,'gold'
 return None,None

def fx(im,t,idx,end,color):
 layer=Image.new('RGB',(W,H));ld=ImageDraw.Draw(layer)
 age,kind=cue_age(t);pulse=math.exp(-((t*124/60)%1)*7)
 strength=.4+.5*pulse
 # A deliberately restrained beat light at the chart margins, not a flash.
 col=tuple(int(v*.19*strength) for v in color)
 for side in [7,712]:ld.line((side,515,side,1185),fill=col,width=3)
 # Orbital reticle and actual endpoint are locked to the observed candle.
 ex,ey=end
 if 5<ex<638 and 505<ey<1180:
  r=17+4*pulse
  ld.arc((ex-r,ey-r,ex+r,ey+r),t*65,t*65+110,fill=color,width=2)
  ld.arc((ex-r-7,ey-r-7,ex+r+7,ey+r+7),-t*50,-t*50+65,fill=CYAN,width=1)
  ld.ellipse((ex-5,ey-5,ex+5,ey+5),fill=(220,255,255))
 if age is not None:
  c=GOLD3 if kind=='gold' else CYAN if kind=='crash' else color
  decay=max(0,1-age/1.5)
  # Expanding impact rings, angular streaks and particles occupy chart only.
  for lag in [0,.12,.25]:
   a=age-lag
   if a<0:continue
   rr=24+a*310;v=max(0,1-a/1.4)
   cc=tuple(int(z*v*.9) for z in c)
   ld.ellipse((ex-rr,ey-rr*.48,ex+rr,ey+rr*.48),outline=cc,width=max(1,int(4*v)))
  for ang,speed,life,size in PARTICLES:
   if age>=life:continue
   dist=(age*speed)*(1.5-.2*age);x=ex+math.cos(ang)*dist;y=ey+math.sin(ang)*dist*.65+age*age*45
   if 4<x<638 and 505<y<1187:
    v=(1-age/life)**1.2;cc=tuple(int(z*v) for z in c)
    ld.line((x-math.cos(ang)*(4+age*13),y-math.sin(ang)*(4+age*13),x,y),fill=cc,width=round(size))
  if kind=='crash' and age<.55:
   # Lightning is a decoration: bent paths do not pretend to be data.
   rng=np.random.default_rng(726+int(age*15))
   pts=[(ex+(1-u)*60+rng.uniform(-22,22)*(1-u),500+(ey-500)*u) for u in np.linspace(0,1,13)]
   ld.line(pts,fill=tuple(int(x*(1-age/.55)) for x in CYAN),width=3)
  # Side velocity streaks and a lens bloom, separated from numeric regions.
  for side in [0,1]:
   for k in range(11):
    yy=510+k*62+(age*360)%62;xx=(18+k%3*7) if side==0 else (704-k%3*7)
    ld.line((xx,yy,xx,yy+25+50*decay),fill=tuple(int(v*decay*.7) for v in c),width=1)
 # Clamp all effects below the information panel and above provenance.
 ld.rectangle((0,0,W,498),fill=(0,0,0));ld.rectangle((0,1190,W,H),fill=(0,0,0))
 original=im.copy()
 im=small_glow(im,layer,12,.95);im=ImageChops.add(im,layer)
 original.paste(im.crop((0,499,W,1190)),(0,499))
 return original

def header(im,t,idx,color,dd):
 dr=ImageDraw.Draw(im);row=DAILY.iloc[idx]
 # Opaque information planes make sure animated candles never cover facts.
 dr.rectangle((0,0,W,470),fill=(4,7,12))
 dr.text((42,33),'TAIEX  /  MARKET CHRONICLE',font=fnt(16,True),fill=(160,182,199))
 dr.text((560,35),'1999—2026',font=fnt(15,True),fill=(109,136,155))
 dr.line((42,71,678,71),fill=(31,51,65),width=1)
 # Animated equalizer is ornamental rather than a volume/data measurement.
 for k in range(18):
  hh=4+int(13*(.5+.5*math.sin(t*7-k*.65))**2)
  dr.rectangle((481+k*3,58-hh,482+k*3,58),fill=tuple(int(x*.65) for x in color))
 dr.rounded_rectangle((29,91,690,273),radius=16,fill=(10,16,24),outline=(28,45,57),width=1)
 dr.rounded_rectangle((29,113,33,250),radius=2,fill=color)
 dr.text((49,108),'加權指數',font=fnt(22),fill=WHITE)
 dr.text((466,111),row.date.strftime('%Y.%m.%d'),font=fnt(26,True),fill=WHITE)
 hook.glowing_text(im,(45,158),f'{row.close:,.2f}',fnt(70,True),color,blur=6,condense=.86)
 dr=ImageDraw.Draw(im)
 dr.text((487,163),'單日漲跌',font=fnt(14),fill=(155,173,189))
 if idx==0:
  # No previous-session close is supplied for the first observation.
  dr.text((487,185),'N/A',font=fnt(31,True),fill=DIM)
  dr.text((487,225),'未提供前收',font=fnt(16),fill=(186,204,215))
 else:
  change=row.close-RAW_C[idx-1]
  pct=change/RAW_C[idx-1]*100
  daycol=RED if change>=0 else GREEN
  dr.text((487,185),f'{pct:+.2f}%',font=fnt(31,True),fill=daycol)
  dr.text((487,225),f'{change:+,.2f} 點',font=fnt(16),fill=(186,204,215))
 dr.text((49,242),'距1999起樣本收盤前高',font=fnt(13),fill=(135,158,175))
 dr.text((236,238),f'{dd:+.2f}%',font=fnt(19,True),fill=GREEN if dd<0 else RED)
 p=max(0,min(1,(t-7)/202));dr.line((42,286,678,286),fill=(24,41,54),width=2)
 dr.line((42,286,42+p*636,286),fill=color,width=3)
 if t>=7:dr.ellipse((38+p*636,282,46+p*636,290),fill=WHITE)

def event_panel(im,t,idx,event,age,remaining,color):
 dr=ImageDraw.Draw(im)
 if t<7:
  after=t>=2.1
  dr.text((44,306),'高峰之後，市場突然變臉' if after else '從萬點高峰開始',font=fnt(29),fill=WHITE)
  perf=(RAW_C[idx]/RAW_C[hook.P]-1)*100
  text=f'{perf:.2f}%' if after else '萬點行情'
  hook.glowing_text(im,(44,362),text,fnt(62,True) if after else fnt(44),GREEN if after else GOLD3,blur=7)
  dr=ImageDraw.Draw(im)
  dr.text((341,374),'較'+DAILY.date.iloc[hook.P].strftime('%Y.%m.%d')+'收盤' if after else '真實歷史・真實OHLC',font=fnt(18),fill=(172,193,206))
  dr.text((341,406),f'相隔 {(DAILY.date.iloc[idx]-DAILY.date.iloc[hook.P]).days} 天' if t>=4.733 else '1999 → 2001',font=fnt(20),fill=WHITE)
 elif t>=209:
  gain=(RAW_C[-1]/RAW_C[0]-1)*100
  dr.text((42,307),'把波動，拉成一段歷史',font=fnt(34),fill=WHITE)
  dr.text((45,368),'1999 → '+ASOF,font=fnt(30,True),fill=(192,210,220))
  dr.text((45,414),f'價格指數 {gain:+.2f}%  ·  不含股息',font=fnt(24),fill=RED)
 elif event:
  # A quick slide of only the accent line, while every word stays stable.
  ecolor=GOLD3 if event['date'] in GOLD else color
  dr.rectangle((42,306,47,449),fill=ecolor)
  category=event['category']
  dr.text((62,306),category,font=fnt(16),fill=(144,172,191))
  title=event['title'];dr.text((61,337),title,font=fnt(29 if len(title)>11 else 32),fill=WHITE)
  detail=DETAILS[event['date']]
  # Split on the semantic divider before adding the compact crash ranking.
  lines=detail.split('・')
  for n,line in enumerate(lines):dr.text((62,391+n*25),line,font=fnt(18),fill=(207,222,231))
  if event['date'] in CRASH:
   dr.rectangle((456,300,693,452),fill=(9,18,23));dr.text((469,306),'樣本單日跌幅 TOP 5',font=fnt(13),fill=(143,168,179))
   picks=np.argsort(DAY_RET[:idx+1])[:5]
   for rank,j in enumerate(picks):
    yy=333+rank*22
    dr.text((470,yy),DAILY.iloc[int(j)].date.strftime('%y.%m.%d'),font=fnt(13,True),fill=(183,204,216))
    dr.text((586,yy-2),f'{DAY_RET[j]*100:.2f}%',font=fnt(16,True),fill=GREEN)
 else:
  year=DAILY.date.iloc[idx].year
  dr.text((43,309),str(year),font=fnt(72,True),fill=(32,65,84))
  dr.text((253,331),'市場一直向前，波動從未停止',font=fnt(21),fill=(185,210,223))
  phase='推近波動，追蹤每一次轉折' if CAM[round(t*FPS)]['span']<440 else '拉開視野，看見長期軌跡'
  dr.text((254,371),phase,font=fnt(18),fill=(111,146,167))
  if t<8.5:dr.text((253,410),'回到 1999，重新出發',font=fnt(22),fill=CYAN)

def footer(im,t,cam):
 dr=ImageDraw.Draw(im)
 dr.rectangle((0,1231,W,H),fill=(4,7,12))
 mode='日K' if cam['span']<440 else '週K・末週截至當日'
 if t>=209:mode='全期週K'
 dr.text((40,1240),mode+'  |  截至 '+ASOF,font=fnt(14),fill=(147,174,192))
 dr.text((40,1261),SOURCE_LABEL,font=fnt(12),fill=(109,136,153))

def scene_v3(t):
 frame=max(0,min(len(CAM)-1,round(t*FPS)));cam=CAM[frame]
 idx,event,age,remaining=observed(t);row=DAILY.iloc[idx];dd=(row.close/CUMCLOSE[idx]-1)*100
 color=GOLD3 if event and event['date'] in GOLD else GREEN if dd<-5 else RED
 im,end,xp,yp=chart_layer(t,idx,cam,color,event,age,remaining)
 # Extend true recent closes as a fine luminous trace; it does not invent bars.
 dr=ImageDraw.Draw(im)
 if t<209:
  points=[(xp(j),yp(RAW_C[j])) for j in range(max(0,idx-19),idx+1)]
  points=[(x,y) for x,y in points if 1<x<638 and 500<y<1185]
  if len(points)>1:dr.line(points,fill=tuple(int(v*.6) for v in color),width=2)
 im=fx(im,t,idx,end,color)
 dr=ImageDraw.Draw(im)
 if 7<=t<209 and row.date<=pd.Timestamp('2020-07-27'):
  yy=yp(12682.41)
  if 525<yy<1170:
   for xx in range(0,638,13):dr.line((xx,yy,xx+6,yy),fill=(82,125,144),width=1)
   # Dark label plate prevents the reference caption from fighting candle wicks.
   dr.rectangle((36,yy-28,322,yy-5),fill=(5,12,18))
   dr.text((43,yy-27),'1990盤中前高 12,682.41',font=fnt(16),fill=(161,193,207))
  else:
   dr.text((43,475),'↑ 1990盤中前高 12,682.41',font=fnt(15),fill=(126,165,185))
 header(im,t,idx,color,dd);event_panel(im,t,idx,event,age,remaining,color);footer(im,t,cam)
 # A camera reset is marked by a directional wipe only over the chart.
 if 6.75<=t<7.3:
  u=(t-6.75)/.55;x=int(-220+u*1140)
  wipe=Image.new('RGBA',(720,1280));wd=ImageDraw.Draw(wipe)
  wd.polygon([(x-170,470),(x-50,470),(x+170,1230),(x+50,1230)],fill=(50,190,238,int(45*math.sin(math.pi*u))))
  im.paste(wipe,(0,0),wipe)
 return im

def ranking_v3(t):
 im=Image.new('RGB',(W,H),(4,7,12));dr=ImageDraw.Draw(im)
 dr.text((42,37),'TAIEX  /  THE YEARBOOK',font=fnt(17,True),fill=(160,182,199))
 dr.text((42,113),'完整年度漲幅排行',font=fnt(43),fill=GOLD3)
 dr.text((44,184),'2000–2025・價格指數，不含股息',font=fnt(21),fill=WHITE)
 dr.line((42,238,678,238),fill=(83,73,40),width=2)
 # All 26 complete years are visible at once, unlike the older scrolling crop.
 for rank,(year,ret) in enumerate(ANNUAL,1):
  rr,cc=divmod(rank-1,2);x=42+cc*338;y=276+rr*66
  enter=smooth((t-216-rr*.035)/.45);dx=int(35*(1-enter))
  c=GOLD3 if ret>=0 else GREEN
  dr.rounded_rectangle((x+dx,y,x+306+dx,y+54),radius=7,fill=(12,19,27),outline=(23,37,47))
  dr.text((x+9+dx,y+15),f'{rank:02}',font=fnt(15,True),fill=(113,139,156))
  dr.text((x+41+dx,y+10),str(year),font=fnt(23,True),fill=WHITE)
  dr.text((x+176+dx,y+11),f'{ret*100:+.2f}%',font=fnt(23,True),fill=c)
  w=267*abs(ret)/max(abs(z[1]) for z in ANNUAL)
  dr.rectangle((x+10+dx,y+47,x+10+dx+w*enter,y+49),fill=tuple(int(v*.6) for v in c))
 dr.text((43,1166),'2026 尚未結束，不列入完整年度排名',font=fnt(20),fill=(175,196,210))
 dr.text((43,1246),SOURCE_LABEL,font=fnt(14),fill=(114,141,159))
 return im

def end_v3(t):
 im=Image.new('RGB',(W,H),(4,7,12));dr=ImageDraw.Draw(im)
 u=smooth((t-229)/.65)
 for r in [180,230,285]:
  dr.arc((360-r,475-r,360+r,475+r),t*18,t*18+230,fill=(12,47,62),width=2)
 centered(dr,'台股，未完待續',405,fnt(51),WHITE)
 centered(dr,'1999.01.05 → '+ASOF,498,fnt(29),WHITE)
 centered(dr,f'{RAW_C[0]:,.2f} → {RAW_C[-1]:,.2f}',559,fnt(39,True),CYAN)
 for text,y in [(SOURCE_LABEL,758),('資料與成片發布須取得相應授權',801),('K線1999起・1990前高為單點參考',855),('原創圖形、程式、合成音樂與音效',903),('歷史價格指數不含股息・非投資建議',951)]:centered(dr,text,y,fnt(19),GOLD3 if y==801 else (135,161,181))
 return Image.blend(Image.new('RGB',(W,H),(4,7,12)),im,u)

def render_frame(t):
 if DAILY is None:raise ValueError('Call initialize with explicitly supplied observations first')
 if not math.isfinite(t) or not 0<=t<(base.DEMO_DURATION if base.DEMO else DURATION):raise ValueError('Frame time is outside the initialized story')
 image=demo_frame(t) if base.DEMO else scene_v3(t) if t<216 else ranking_v3(t) if t<229 else end_v3(t)
 return stamp(image,WATERMARK)



def demo_frame(t):
 cam=CAM[min(len(CAM)-1,round(t*FPS))];idx,_,_,_=base.observed(t)
 color=RED if idx==0 or RAW_C[idx]>=RAW_C[idx-1] else GREEN
 im,end,_,_=chart_layer(t,idx,cam,color,None,0,0)
 im=fx(im,t,idx,end,color);dr=ImageDraw.Draw(im)
 dr.rectangle((0,0,W,470),fill=(4,7,12))
 dr.text((42,50),'TAIEX / CAMERA DEMO',font=fnt(25,True),fill=WHITE)
 dr.text((42,118),'官方短樣本・鏡頭特效展示',font=fnt(32),fill=WHITE)
 dr.text((42,198),DAILY.date.iloc[idx].strftime('%Y.%m.%d'),font=fnt(30,True),fill=WHITE)
 dr.text((42,252),f'{RAW_C[idx]:,.2f}',font=fnt(65,True),fill=color)
 dr.text((42,360),f'僅 {N} 筆觀測，不代表完整歷史',font=fnt(24),fill=DIM)
 dr.text((42,407),'光環、粒子與節拍燈為裝飾，非行情',font=fnt(20),fill=DIM)
 dr.rectangle((0,1231,W,H),fill=(4,7,12))
 dr.text((40,1245),SOURCE_LABEL,font=fnt(14),fill=DIM)
 return im

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--data');p.add_argument('--demo',action='store_true',help='Use only the bundled three-day official sample')
 p.add_argument('--start',type=float,default=0);p.add_argument('--seconds',type=float)
 p.add_argument('--fps',type=int,default=30);p.add_argument('--still',type=float)
 p.add_argument('--output',default='output/dynamic.mp4');p.add_argument('--silent-only',action='store_true')
 p.add_argument('--source-label');p.add_argument('--watermark',default='紀順文X小狐AI')
 a=p.parse_args()
 try:
  if a.demo and a.data:raise ValueError('--demo and --data are mutually exclusive')
  seconds=a.seconds if a.seconds is not None else (12 if a.demo else DURATION)
  duration=seconds if a.demo else DURATION
  if not all(math.isfinite(v) for v in (seconds,a.start)) or seconds<=0 or a.start<0 or a.start+seconds>duration or a.fps<=0:raise ValueError('Invalid render interval or FPS')
  data=load(ROOT/'data/official_20261102_04.csv' if a.demo else input_path(a.data))
  source=a.source_label or ('TWSE / Government Open Data License 1.0' if a.demo else 'User-supplied authorized data')
  initialize(data,source_label=source,watermark=a.watermark,demo=a.demo,duration=duration)
  out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
  if a.still is not None:render_frame(a.still).save(out.with_suffix('.png'));return
  silent=out if a.silent_only else out.with_name(out.stem+'_silent.mp4')
  actual=encode_frames(render_frame,silent,seconds,a.fps,start=a.start,size=(W,H))
  if not a.silent_only:
   from score_long import write_score
   wav=out.with_suffix('.wav');write_score(wav,actual,SEG,CRASH,GOLD,start=a.start);mux_audio(silent,wav,out)
  qa={'duration':actual,'source':source,'watermark':a.watermark,'observations':N,'first_date':str(DAILY.date.iloc[0].date()),'last_date':str(DAILY.date.iloc[-1].date()),'market_values_interpolated':False,'camera_values_eased':True,'demo':a.demo,'listening_check':'not performed by script','visual_check':'not performed by script'}
  out.with_suffix('.qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2));print(out)
 except (ValueError,RuntimeError,OSError) as error:p.error(str(error))

if __name__=='__main__':main()
