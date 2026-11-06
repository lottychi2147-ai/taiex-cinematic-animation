"""Original 232-second, 1999–2026 TAIEX story. External authorized daily OHLC required."""
from render import *
import high_fidelity_hook as hook
from effects import overlay_glow
import time
DAILY=None
N=0;FPS=30;DURATION=232
SEG=[];EVENTS=[];ANNUAL=[]
FONT14=font(14);FONT16=font(16);FONT18=font(18);FONT20=font(20);NUM14=font(14,True)

def validate_story_data(data):
 if data.empty or not data.ohlc_verified.all():raise ValueError('Full film requires verified daily OHLC on every row; use render.py for close-only observations.')
 if data.iloc[0].date!=pd.Timestamp('1999-01-05') or data.iloc[-1].date!=pd.Timestamp('2026-11-06'):
  raise ValueError('This fixed narrative requires a matching 1999-01-05 through 2026-11-06 daily TAIEX dataset. The bundled short sample cannot render the full story.')
 counts=data.groupby(data.date.dt.year).size()
 if len(counts)!=28 or (counts<150).any():raise ValueError('Full-film input must contain daily observations for every narrative year, not monthly or sparse points. Calendar completeness must also be verified independently.')

def initialize(data):
 global DAILY,N,EVENTS,RAW_C,RAW_H,RAW_L,RAW_O,DAY_RET,CUMHIGH,CUMLOW,CUMCLOSE,HOLDS,MOVE,SEG,LO,HI,ANNUAL
 DAILY=data.copy().reset_index(drop=True)
 validate_story_data(DAILY)
 hook.initialize(DAILY)
 N=len(DAILY)
 EVENTS=[dict(e) for e in json.loads((ROOT/'data/verified_milestones.json').read_text())['events']]
 RAW_C=DAILY.close.to_numpy();RAW_H=DAILY.high.to_numpy();RAW_L=DAILY.low.to_numpy();RAW_O=DAILY.open.to_numpy()
 DAY_RET=np.r_[0,RAW_C[1:]/RAW_C[:-1]-1];CUMHIGH=np.maximum.accumulate(RAW_H);CUMLOW=np.minimum.accumulate(RAW_L);CUMCLOSE=np.maximum.accumulate(RAW_C)
 for e in EVENTS:
  hits=DAILY.index[DAILY.date.eq(pd.Timestamp(e['date']))]
  if len(hits)!=1:raise ValueError(f"Event date not an observed session: {e['date']}")
  e['row']=int(hits[0]);e['hold']=2.5 if e['date'] in ['1999-09-27','2020-07-27'] else 2.0
  if 'close' in e and abs(e['close']-RAW_C[e['row']])>=.011:raise ValueError(f"Supplied close conflicts with cited event fact on {e['date']}")
 EVENTS.sort(key=lambda e:e['row'])
 HOLDS=sum(e['hold'] for e in EVENTS);MOVE=202-HOLDS;SEG=[];cursor=7.;last=0
 for e in EVENTS:
  length=(e['row']-last)/(N-1)*MOVE
  SEG.append({'start':cursor,'end':cursor+length,'from':last,'to':e['row'],'event':None});cursor+=length
  SEG.append({'start':cursor,'end':cursor+e['hold'],'from':e['row'],'to':e['row'],'event':e});cursor+=e['hold'];last=e['row']
 assert abs(cursor-209)<.0001

 # Deterministic precomputed camera easing only; market values are never interpolated.
 LO=np.empty(DURATION*FPS);HI=np.empty_like(LO);lo=CUMLOW[0]*.93;hi=CUMHIGH[0]*1.03
 for f in range(DURATION*FPS):
  t=f/FPS;i=at_time(t)[0] if t>=7 else 0;targetlo=CUMLOW[i]*.93;targethi=CUMHIGH[i]*1.03
  a=1-math.exp(-1/(FPS*.32));lo+=(targetlo-lo)*a;hi+=(targethi-hi)*a;LO[f]=lo;HI[f]=hi
 # Annual ranking excludes partial 1999 and incomplete 2026.
 annual=DAILY.set_index('date').close.resample('YE').last();yr=annual.pct_change().dropna();ANNUAL=[(int(k.year),float(v)) for k,v in yr.items() if 2000<=k.year<=2025];ANNUAL.sort(key=lambda z:z[1],reverse=True)


def at_time(t):
 for s in SEG:
  if s['start']<=t<s['end']:
   f=(t-s['start'])/max(1e-9,s['end']-s['start']);idx=round(s['from']+(s['to']-s['from'])*f)
   return idx,s['event'],t-s['start'],s['end']-t
 return N-1,None,0,0

Y,X=np.mgrid[0:H,0:W];RAD=np.exp(-(((X-365)/480)**2+((Y-750)/620)**2))
BGS={}
for key,c in [('up',RED),('down',GREEN),('gold',(245,190,55))]:
 a=np.zeros((H,W,3),dtype=np.uint8);a[:]=[4,6,7];BGS[key]=Image.fromarray(np.clip(a.astype(float)+RAD[:,:,None]*np.array(c)*.045,0,255).astype(np.uint8))

DETAILS={
 '1999-09-27':'9/21地震休市・9/27恢復交易',
 '2001-09-26':'盤中低見3411.68・此值不是收盤',
 '2003-04-28':'SARS疫情升溫・收盤4139.50',
 '2008-11-20':'全球金融海嘯・收盤4089.93',
 '2015-08-24':'收盤下跌376.58點',
 '2017-05-11':'收盤10001.48・重返萬點',
 '2020-03-19':'單日−5.83%・收盤8681.34',
 '2020-07-27':'盤中12686.36・改寫30年紀錄',
 '2022-12-30':'2022全年−22.40%・不是單日跌幅',
 '2024-03-08':'盤中首破20000・收盤19785.32',
 '2025-04-07':'單日−9.70%・當時最大收盤跌幅',
 '2026-11-06':'截至11/06・不是2026全年'}
GOLD={'2017-05-11','2020-07-27','2024-03-08'}
CRASH={'2001-09-26','2008-11-20','2015-08-24','2020-03-19','2025-04-07'}


def floor_heatmap(im,months,opacity):
 if len(months)<13 or opacity<=0:return
 rs=months.close.pct_change().dropna().tail(36);vals=rs.to_numpy();dates=rs.index
 layer=Image.new('RGBA',(W,H));dr=ImageDraw.Draw(layer)
 count=len(vals);cols=6;rows=math.ceil(count/cols)
 for k,(date,v) in enumerate(zip(dates,vals)):
  rr,cc=divmod(k,cols);u0=rr/rows;u1=(rr+1)/rows;s0=.32+.88*u0;s1=.32+.88*u1
  y0=540+(u0**1.45)*720;y1=540+(u1**1.45)*720
  x00=360+(cc-3)*108*s0+2;x01=360+(cc-2)*108*s0-2
  x10=360+(cc-3)*108*s1+2;x11=360+(cc-2)*108*s1-2
  color=RED if v>=0 else GREEN;power=min(1,.28+abs(v)*4);c=tuple(int(z*power) for z in color);alpha=int(95*opacity)
  dr.polygon([(x00,y0+2),(x01,y0+2),(x11,y1-3),(x10,y1-3)],fill=(*c,alpha),outline=(25,42,42,int(120*opacity)))
  if rr>=rows-2:
   tx=f'{date.year%100:02}/{date.month:02}';ret=f'{v*100:+.1f}%';ft=font(18 if rr==rows-1 else 14);cx=(x00+x01+x10+x11)/4;cy=(y0+y1)/2
   for text,dy in [(tx,-17),(ret,5)]:
    box=dr.textbbox((0,0),text,font=ft);dr.text((cx-(box[2]-box[0])/2,cy+dy),text,font=ft,fill=(218,237,230,int(215*opacity)))

 im.paste(layer,(0,0),layer)


def hud(im,idx,basecolor,dd,frame):
 dr=ImageDraw.Draw(im);r=DAILY.iloc[idx];dr.text((44,126),'加權指數',font=FONT20,fill=WHITE);dr.text((134,132),'TAIEX',font=font(12,True),fill=(184,188,190))
 hook.glowing_text(im,(42,155),f'{r.close:.2f}',NF[72],basecolor,blur=6,condense=.80)
 hook.glowing_text(im,(44,224),r.date.strftime('%Y.%m.%d'),font(30,True),WHITE,blur=0,condense=.85)
 dr=ImageDraw.Draw(im)
 if dd<-5:label='較1999起樣本收盤前高';pct=dd
 else:label='較'+DAILY.iloc[0].date.strftime('%Y.%m.%d')+'收盤';pct=(r.close/RAW_C[0]-1)*100
 dr.text((318,151),label,font=font(12),fill=WHITE);dr.rectangle((316,172,468,198),fill=tuple(int(x*.18) for x in basecolor));dr.text((322,173),f'{pct:+.2f}%',font=font(18,True),fill=basecolor)


def chart_frame(t,idx,event,age,remaining,overview=False):
 row=DAILY.iloc[idx];dd=(row.close/CUMCLOSE[idx]-1)*100;gold=event is not None and event['date'] in GOLD
 basekey='gold' if gold else ('down' if dd<-5 else 'up');color=(245,205,61) if gold else (GREEN if dd<-5 else RED);im=BGS[basekey].copy()
 hist=DAILY.iloc[:idx+1].set_index('date');months=hist.resample('ME').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna();n=len(months)
 lo,hi=LO[min(len(LO)-1,round(t*FPS))],HI[min(len(HI)-1,round(t*FPS))]
 if overview:lo=CUMLOW[-1]*.93;hi=CUMHIGH[-1]*1.03
 xstart=180-215*min(1,max(0,(n-64)/56));xend=min(560,180+(n-1)*6)
 def xp(j):return xend if n==1 else xstart+j/(n-1)*(xend-xstart)
 def yp(v):return 1225-(v-lo)/max(1,hi-lo)*745
 heat=event is not None and event['date'] in CRASH
 if heat:floor_heatmap(im,months,min(1,age/.4,remaining/.4))
 tails=np.asarray(im).copy()
 for j,r in enumerate(months.itertuples()):
  x=int(xp(j));c=np.array(RED if r.close>=r.open else GREEN);ystart=max(0,int(yp(r.close)));ystop=1270
  if x<0 or x>=W or ystart>=ystop:continue
  ys=np.arange(ystart,ystop);alpha=.095*(1-(ys-ystart)/max(1,ystop-ystart))**2.1;shade=np.clip(np.array([4,6,7])[None,:]+alpha[:,None]*c[None,:],0,255).astype(np.uint8)
  for xx in range(max(0,x-1),min(W,x+2)):tails[ys,xx]=np.maximum(tails[ys,xx],shade)
 im=Image.fromarray(tails);dr=ImageDraw.Draw(im)
 step=2000 if hi<16000 else (5000 if hi<35000 else 10000)
 for tick in range(step,int(hi)+step,step):
  yy=yp(tick)
  if not 480<yy<1225:continue
  dr.line((0,yy,635,yy),fill=(9,13,16))
  if not heat:dr.text((644,yy),f'{tick:,}',font=font(13,True),fill=(55,61,63))
 for k in range(27):dr.point(((k*137+23)%W,480+(k*181)%750),fill=(22,30,33))
 pitch=(xend-xstart)/max(1,n-1)
 for j,r in enumerate(months.itertuples()):
  x=xp(j);c=RED if r.close>=r.open else GREEN;ww=min(6,max(1,pitch*.57));a,b=sorted([yp(r.open),yp(r.close)])
  if x<-5:continue
  dr.line((x,yp(r.high),x,yp(r.low)),fill=c,width=1);dr.rectangle((x-ww/2,a,x+ww/2,max(a+1,b)),fill=c)
 end=(xp(n-1),yp(row.close));flow=RED if row.close>=(RAW_C[idx-1] if idx else row.open) else GREEN;im=overlay_glow(im,end,flow,t)
 hud(im,idx,color,dd,round(t*FPS));dr=ImageDraw.Draw(im)
 # Independently verified 1990 single-point reference, not fabricated older OHLC.
 if row.date<=pd.Timestamp('2020-07-27'):
  old=12682.41;raw_y=yp(old);yy=max(445,raw_y);refcolor=(245,213,75) if row.date==pd.Timestamp('2020-07-27') else (176,193,192)
  for x in range(0,635,12):dr.line((x,yy,x+7,yy),fill=refcolor,width=1)
  years=row.date.year-1990;months_elapsed=row.date.month-2
  if row.date.day<12:months_elapsed-=1
  if months_elapsed<0:years-=1;months_elapsed+=12
  label=('↑' if raw_y<445 else '')+'1990盤中前高 12682.41'
  dr.text((340,yy-26),label,font=FONT16,fill=refcolor)
  timing=f'距前高紀錄 {years}年{months_elapsed}月'
  if row.date==pd.Timestamp('2020-07-27'):timing='突破相隔 30年5月15天'
  dr.text((42,yy-26),timing,font=FONT16,fill=refcolor)

 if heat:
  # Ranking uses only observed prior daily returns, not invented company prices.
  picks=np.argsort(DAY_RET[:idx+1])[:6];dr.text((389,230),'1999起最大單日跌幅',font=FONT16,fill=DIM)
  for rank,j in enumerate(picks):
   yy=257+rank*27;dr.text((389,yy),DAILY.iloc[int(j)].date.strftime('%Y.%m.%d'),font=NUM14,fill=WHITE)
   bar=95*abs(DAY_RET[j])/max(abs(DAY_RET[picks[0]]),.001);dr.rectangle((510,yy+4,510+bar,yy+13),fill=(0,80,56));dr.text((605,yy-2),f'{DAY_RET[j]*100:.2f}%',font=NUM14,fill=GREEN)

 if event:
  dr=ImageDraw.Draw(im);dr.rectangle((42,284,45,350),fill=color)
  dr.text((58,294),event['category'],font=FONT20,fill=WHITE)
  if heat:dr.text((58,329),f'近{min(36,len(months)-1)}月報酬／末月截至當日',font=FONT16,fill=(179,193,187))
  opacity=max(0,min(1,age/.2,remaining/.25));title=event['title'];ft=F[44] if len(title)<=10 else F[32];bbox=ft.getbbox(title);tx=(W-(bbox[2]-bbox[0]))/2
  hook.glowing_text(im,(tx,555),title,ft,(245,213,75) if gold else WHITE,blur=6,opacity=opacity)
  detail=DETAILS[event['date']];ft=FONT20;box=ft.getbbox(detail);hook.glowing_text(im,((W-(box[2]-box[0]))/2,620),detail,ft,WHITE,blur=0,opacity=opacity)
  if event['date'] in CRASH:
   text=f'{dd:.2f}%';box=NF[90].getbbox(text);hook.glowing_text(im,((W-(box[2]-box[0])*.85)/2,695),text,NF[90],GREEN,blur=8,condense=.85,opacity=opacity)
   hook.glowing_text(im,(199,797),'相對1999起樣本收盤前高',FONT20,WHITE,blur=0,opacity=opacity)
   if age<.8:
    hud_patch=im.crop((40,120,485,263));rank_patch=im.crop((375,225,695,422));card_patch=im.crop((40,282,353,389))
    im=hook.lightning(im,4.567+age,end,flash=False);im.paste(hud_patch,(40,120));im.paste(rank_patch,(375,225));im.paste(card_patch,(40,282))
    if age<.133:im=Image.blend(im,Image.new('RGB',(W,H),(220,239,241)),.35*(1-age/.133))
  if gold:
   pdg=ImageDraw.Draw(im);rng=np.random.default_rng(338);ang=rng.uniform(0,math.tau,100);rad=np.sqrt(rng.uniform(0,1,100))*140
   for a0,r0 in zip(ang,rad):
    x=end[0]+math.cos(a0)*r0*min(1,age/.4);y=end[1]+math.sin(a0)*r0*.7*min(1,age/.4)
    pdg.ellipse((x-1,y-1,x+1,y+1),fill=(int(235*opacity),int(200*opacity),int(80*opacity)))
 elif overview:
  gain=(RAW_C[-1]/RAW_C[0]-1)*100
  hook.glowing_text(im,(140,340),'1999 → 2026',F[52],WHITE,blur=6)
  hook.glowing_text(im,(150,410),f'價格指數 {gain:+.2f}%',F[38],RED,blur=4)
 dr=ImageDraw.Draw(im);dr.text((42,1248),'月K·使用者提供資料 · 完整來源請見附帶報告',font=FONT14,fill=(121,132,136))
 return im


def ranking_frame(t):
 im=BGS['gold'].copy();dr=ImageDraw.Draw(im);dr.text((80,138),'完整年度漲幅排行',font=F[44],fill=(244,211,92));dr.text((100,205),'2000–2025・價格指數、不含股息',font=FONT20,fill=WHITE);dr.line((50,251,670,251),fill=(145,119,48),width=1)
 if t<222:
  offset=-330*(1-min(1,(t-216)/6))
  for rank,(year,ret) in enumerate(ANNUAL,1):
   rr,cc=divmod(rank-1,3);cx=[145,360,575][cc];yy=310+rr*110+offset
   if yy<270 or yy>1220:continue
   dr.text((cx-65,yy),f'#{rank:02}',font=FONT16,fill=(193,166,83));dr.text((cx-44,yy+20),str(year),font=NF[32],fill=WHITE);dr.text((cx-60,yy+63),f'{ret*100:+.2f}%',font=FONT20,fill=(246,215,115) if ret>=0 else GREEN)
 else:
  offset=-180*(1-min(1,(t-222)/5))
  for rank,(year,ret) in enumerate(ANNUAL,1):
   yy=310+(rank-1)*84+offset
   if yy<265 or yy>1210:continue
   dr.text((52,yy),f'{rank:02}',font=NF[32],fill=(219,187,85));dr.text((129,yy),str(year),font=NF[32],fill=WHITE)
   width=250*abs(ret)/ANNUAL[0][1];dr.rounded_rectangle((260,yy+9,260+max(1,width),yy+31),radius=3,fill=(185,145,43) if ret>=0 else GREEN);dr.text((540,yy),f'{ret*100:+.2f}%',font=NF[32],fill=(246,215,115))
 dr.rectangle((0,1215,W,H),fill=(4,6,7));dr.text((42,1248),'不含1999與2026・價格指數不含股息',font=FONT14,fill=DIM)
 if t>228.7:im=Image.blend(im,Image.new('RGB',(W,H),(4,6,7)),min(1,(t-228.7)/.3))
 return im


def end_frame(t):
 im=Image.new('RGB',(W,H),(4,6,7));dr=ImageDraw.Draw(im)
 for text,y,ft,col in [('台股，未完待續',460,F[52],WHITE),(DAILY.iloc[0].date.strftime('%Y.%m.%d')+' — '+DAILY.iloc[-1].date.strftime('%Y.%m.%d'),565,F[28],WHITE),(f'{RAW_C[0]:.2f} → {RAW_C[-1]:.2f}',630,F[38],RED),('行情來源：使用者提供及授權',735,FONT20,DIM),('資料使用限制由提供者決定',780,F[24],(239,205,112)),('K線1999起・1990前高為單點參考',840,FONT20,DIM),('原創圖形、程式與合成配樂',885,FONT20,DIM),('歷史價格指數不含股息・非投資建議',935,FONT18,DIM)]:
  b=ft.getbbox(text);dr.text(((W-(b[2]-b[0]))/2,y),text,font=ft,fill=col)
 if t<229.3:im=Image.blend(Image.new('RGB',(W,H),(4,6,7)),im,max(0,(t-229)/.3))
 return im


def render_frame(t):
 if t<7:return hook.frame(t)
 if t<209:
  idx,e,age,remaining=at_time(t);im=chart_frame(t,idx,e,age,remaining)
  if 7.133<=t<9.933:
   opacity=min(1,(t-7.133)/.1,(9.933-t)/.2)
   hook.glowing_text(im,(166,610),'回到1999',F[64],WHITE,blur=7,opacity=max(0,opacity))
  return im
 if t<216:return chart_frame(t,N-1,None,0,0,overview=True)
 if t<229:return ranking_frame(t)
 return end_frame(t)

def main():
 p=argparse.ArgumentParser(description='Fixed 1999–2026 cinematic story. Authorized matching daily data is not bundled.')
 p.add_argument('--data');p.add_argument('--start',type=float,default=0);p.add_argument('--seconds',type=float,default=DURATION);p.add_argument('--output',default='output/taiex_cinematic.mp4');p.add_argument('--silent-only',action='store_true');p.add_argument('--still',type=float);p.add_argument('--source-label',default='User-supplied authorized data')
 a=p.parse_args()
 try:
  initialize(load(input_path(a.data)))
  if a.start<0 or a.seconds<=0 or a.start+a.seconds>DURATION:raise ValueError('Render interval must be within the 232-second story')
  out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
  if a.still is not None:
   if not 0<=a.still<DURATION:raise ValueError('Still timestamp must be within [0,232)')
   render_frame(a.still).save(out.with_suffix('.png'));return
  silent=out if a.silent_only else out.with_name(out.stem+'_silent.mp4')
  actual=encode_frames(render_frame,silent,a.seconds,FPS,start=a.start,size=(W,H))
  if not a.silent_only:
   from score_long import write_score
   wav=out.with_suffix('.wav');write_score(wav,actual,SEG,CRASH,GOLD,start=a.start);mux_audio(silent,wav,out)
  qa={'duration':actual,'start':a.start,'source':a.source_label,'observations':N,'first_date':str(DAILY.iloc[0].date.date()),'last_date':str(DAILY.iloc[-1].date.date()),'event_sources':'data/verified_milestones.json','complete_trading_calendar_verified':False,'listening_check':'not performed by script','visual_check':'not performed by script'}
  out.with_suffix('.qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2));print(out)
 except (ValueError,RuntimeError,OSError) as error:p.error(str(error))
if __name__=='__main__':main()
