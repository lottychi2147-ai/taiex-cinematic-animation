"""Original world-space camera and partial-week candles. Explicit input only."""
from long_film import *
import long_film as story
from functools import lru_cache
DEMO=False
DEMO_DURATION=12
CAM=[]
PRICE_HEIGHT=685.; TOP=500.; BOTTOM=1185.
XLEFT=15.; XRIGHT=592.; XWIDTH=XRIGHT-XLEFT

def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)

def lerp(a,b,u):return a+(b-a)*smooth(u)

def continuous_observation(t):
 if DEMO:return min(N-1,max(0,t/DEMO_DURATION*N))
 if t<7:
  if t<2.1:return hook.START+(hook.P-hook.START)*smooth(t/2.1)
  if t<4.733:return hook.P+(hook.T-hook.P)*smooth((t-2.1)/2.633)
  return float(hook.T)
 if t>=209:return N-1.
 for seg in SEG:
  if seg['start']<=t<seg['end']:
   u=(t-seg['start'])/(seg['end']-seg['start'])
   return seg['from']+(seg['to']-seg['from'])*smooth(u)
 return N-1.

def weekly_coordinate(di):
 # Camera alone follows a continuous position; prices remain discrete observations.
 a=int(np.floor(di));b=min(N-1,a+1);u=di-a
 wa=float(WI[a]);wb=float(WI[b])
 return wa+(wb-wa)*u

def observed(t):
 if DEMO:return min(N-1,int(continuous_observation(t))),None,0.,0.
 if t<7:return int(round(continuous_observation(t))),None,0.,0.
 if t<209:
  _,event,age,remaining=at_time(t)
  return int(round(continuous_observation(t))),event,age,remaining
 return N-1,None,0.,0.

def event_weight(t,start,end):
 # Deliberate push-in, 1.1 s settled focus, then a smooth 1.8 s release.
 return smooth((t-(start-3.2))/3.35)*(1-smooth((t-(end-.2))/2.2))

def initialize(data, *, demo=False, duration=12):
 global DEMO, DEMO_DURATION, DAILY, N, SEG, RAW_O, RAW_H, RAW_L, RAW_C, CUMCLOSE, DAY_RET, ANNUAL
 global CAM, NW, PART_H, PART_L, PART_O, PERIOD, WC, WD, WEEK, WEND, WG, WH, WI, WL, WO, YEAR_START
 DEMO=demo;DEMO_DURATION=duration
 if not math.isfinite(duration) or duration*FPS<1:raise ValueError('Duration must be finite and positive')
 if demo:
  if data.empty or not data.ohlc_verified.all():raise ValueError('Camera demo requires verified OHLC')
  DAILY=data.copy().reset_index(drop=True);N=len(DAILY);SEG=[];ANNUAL=[]
  RAW_O=DAILY.open.to_numpy();RAW_H=DAILY.high.to_numpy();RAW_L=DAILY.low.to_numpy();RAW_C=DAILY.close.to_numpy()
  CUMCLOSE=np.maximum.accumulate(RAW_C);DAY_RET=np.r_[0,RAW_C[1:]/RAW_C[:-1]-1]
 else:
  story.initialize(data)
  for name in ('DAILY','N','SEG','RAW_O','RAW_H','RAW_L','RAW_C','CUMCLOSE','DAY_RET','ANNUAL'):
   globals()[name]=getattr(story,name)
 PERIOD=DAILY.date.dt.to_period('W-FRI')
 WG=DAILY.groupby(PERIOD,sort=True)
 WEEK=WG.agg({'date':'last','open':'first','high':'max','low':'min','close':'last'})
 WI=pd.factorize(PERIOD,sort=True)[0]
 PART_O=WG.open.transform('first').to_numpy()
 PART_H=WG.high.cummax().to_numpy()
 PART_L=WG.low.cummin().to_numpy()
 WO=WEEK.open.to_numpy(); WH=WEEK.high.to_numpy(); WL=WEEK.low.to_numpy(); WC=WEEK.close.to_numpy()
 WD=WEEK.date.to_numpy(); NW=len(WEEK)
 WEND=WG.apply(lambda g:int(g.index[-1]),include_groups=False).to_numpy()
 YEAR_START=[i for i in range(1,N) if DAILY.date.iloc[i].year!=DAILY.date.iloc[i-1].year]
 CAM=[]
 sl=None; sh=None; sw=None; sx=None
 for f in range(round((DEMO_DURATION if DEMO else DURATION)*FPS)):
  t=f/FPS;idx,event,age,remaining=observed(t);w=int(WI[idx]);wc=continuous_observation(t)
  if t<7:
   span=np.interp(t,[0,1.7,2.1,4.7,6.3,7],[84,102,113,155,142,142]);anchor=582
  else:
   span=np.interp(t,[7,20,40,58,75,90,110,130,150,166,180,195,207],[110,155,230,160,235,175,245,170,225,150,190,140,210]);anchor=584
   for seg in SEG:
    if not seg['event']:continue
    e=seg['event'];weight=event_weight(t,seg['start'],seg['end'])
    if weight<1e-8:continue
    # Original event-focused zoom envelopes affect only framing.
    factor={'2001-09-26':2.0,'2008-11-20':2.35,'2015-08-24':2.0,'2020-03-19':3.7,'2025-04-07':2.8}.get(e['date'],1.45 if e['date'] in GOLD else 1.28)
    span/=factor**weight
    anchor=anchor*(1-weight)+(552 if e['date'] in CRASH else 570)*weight
  span*=5
  if DEMO:span=2.5+.7*math.sin(t*math.tau/DEMO_DURATION);anchor=500
  if not DEMO and 7<=t<58:
   # Expand the available history across the canvas immediately; do not spend
   # the opening years as a narrow strip at the left of an empty viewport.
   span=min(span,max(22,idx*1.05+10))
  if not DEMO and t>=209:
   u=smooth((t-209)/4.8);span=(1-u)*CAM[209*FPS-1]['span']+u*(N-1)*1.025
   anchor=lerp(CAM[209*FPS-1]['anchor'],596,u)
  left=wc-span
  start=max(0,int(np.floor(left))-2)
  highs=RAW_H[start:idx+1];lows=RAW_L[start:idx+1]
  mn=float(lows.min());mx=float(highs.max());ran=max(mx-mn,mx*.12,1200.)
  targetlo=max(0,mn-ran*.18);targethi=mx+ran*.20
  # Intro view re-centres immediately at the actual 1999 reset. There is a wipe.
  if f==0 or (not DEMO and f==210):sl=targetlo;sh=targethi;sw=span;sx=anchor
  speed=1-math.exp(-1/(FPS*.36))
  sl+=(targetlo-sl)*speed;sh+=(targethi-sh)*speed;sw+=(span-sw)*speed;sx+=(anchor-sx)*speed
  # Ensure current observed extrema cannot clip while camera catches an abrupt move.
  sl=min(sl,mn-ran*.055);sh=max(sh,mx+ran*.07)
  if not DEMO and t>=209:
   # The final pull-out settles to the complete historical range.
   u=smooth((t-209)/4.8);sl=(1-u)*sl+u*max(0,float(WL.min())-2000);sh=(1-u)*sh+u*(float(WH.max())+5000)
  left=wc-sw
  # Let the first bar enter at the left before endpoint tracking takes over.
  anchor_real=min(sx,XLEFT+wc*XWIDTH/sw) if not DEMO and 7<=t<30 else sx
  CAM.append({'frame':f,'time':t,'index':idx,'week':w,'world_x':wc,'span':float(sw),'anchor':float(anchor_real),'lo':float(sl),'hi':float(sh),'x_scale':float(XWIDTH/sw),'y_scale':float(PRICE_HEIGHT/(sh-sl))})
 
 # Offline camera planning: reserve range before a rapid move instead of snapping
 # the y-scale at the instant a current price reaches a safety boundary. This
 # affects framing only, never prices, dates, partial candles or visible history.
 # The nested min/max envelope guarantees every original frame's range remains
 # contained after smoothing. The intentional opening flashback stays separate.
 for a,b in ([(0,len(CAM))] if DEMO else [(0,210),(210,6480)]):
  radius=18;xx=np.arange(-radius,radius+1);kernel=np.exp(-.5*(xx/6.)**2);kernel/=kernel.sum()
  lows=np.array([c['lo'] for c in CAM[a:b]]);highs=np.array([c['hi'] for c in CAM[a:b]])
  lower=np.lib.stride_tricks.sliding_window_view(np.pad(lows,radius,mode='edge'),2*radius+1).min(axis=1)
  upper=np.lib.stride_tricks.sliding_window_view(np.pad(highs,radius,mode='edge'),2*radius+1).max(axis=1)
  lower=np.convolve(np.pad(lower,radius,mode='edge'),kernel,mode='valid')
  upper=np.convolve(np.pad(upper,radius,mode='edge'),kernel,mode='valid')
  assert np.all(lower<=lows+1e-7) and np.all(upper>=highs-1e-7)
  for j,c in enumerate(CAM[a:b]):
   c['lo']=float(lower[j]);c['hi']=float(upper[j]);c['y_scale']=float(PRICE_HEIGHT/(upper[j]-lower[j]))
 

@lru_cache(maxsize=100)
def fnt(n,num=False):return font(n,num)

def chart_layer(t,idx,cam,color,event,age,remaining):
 key='down' if color==GREEN else ('gold' if color==(245,205,61) else 'up')
 im=BGS[key].copy()
 if event is not None and event['date'] in CRASH:
  months=DAILY.iloc[:idx+1].set_index('date').resample('ME').agg({'open':'first','high':'max','low':'min','close':'last'}).dropna()
  floor_heatmap(im,months,.48*min(1,age/.45,remaining/.4))
 dr=ImageDraw.Draw(im)
 def xp(j):return cam['anchor']+(j-cam['world_x'])*cam['x_scale']
 def yp(v):return BOTTOM-(v-cam['lo'])*cam['y_scale']
 w=int(WI[idx]);start=max(0,int(cam['world_x']-cam['span'])-8)
 daymode=cam['span']<440
 if daymode:
  arrs=[(j,RAW_O[j],RAW_H[j],RAW_L[j],RAW_C[j],1) for j in range(start,idx+1)]
 else:
  ws=max(0,int(WI[start])-2)
  arrs=[(WEND[j],WO[j],WH[j],WL[j],WC[j],max(1,WEND[j]-(WEND[j-1] if j else -1))) for j in range(ws,w)]
  arrs.append((idx,PART_O[idx],PART_H[idx],PART_L[idx],RAW_C[idx],max(1,idx-(WEND[w-1] if w else -1))))
 # World grid and moving year labels make the changing viewport legible.
 rawstep=(cam['hi']-cam['lo'])/5
 step=next((v for v in [250,500,1000,2000,5000,10000,20000] if v>=rawstep),20000)
 for tick in np.arange(math.ceil(cam['lo']/step)*step,cam['hi']+step,step):
  yy=yp(tick)
  if TOP<=yy<=BOTTOM:
   dr.line((0,yy,639,yy),fill=(13,23,24),width=1)
   heat=event is not None and event['date'] in CRASH
   if not (heat and yy>1100):dr.text((645,yy-8),f'{tick:,.0f}',font=fnt(14,True),fill=(84,98,99))
 if t>=7:
  markers=YEAR_START if not daymode else [j for j in range(start,idx+1) if j>0 and DAILY.date.iloc[j].month!=DAILY.date.iloc[j-1].month]
  last_label_x=-100
  for j in markers:
   if not start<=j<=idx:continue
   xx=xp(j)
   if 15<=xx<=622 and xx-last_label_x>=65:
    dr.line((xx,TOP,xx,BOTTOM),fill=(12,22,24),width=1)
    label=DAILY.date.iloc[j].strftime('%Y' if not daymode else '%y.%m')
    dr.text((xx-16,1198),label,font=fnt(13,True),fill=(104,119,122))
    last_label_x=xx
 # Subtle world-space light curtains, clipped to the chart region.
 tails=np.asarray(im).copy()
 for j,o,h,l,c,width_days in arrs:
  x=int(xp(j))
  if not 0<=x<638:continue
  col=np.array(RED if c>=o else GREEN);ystart=max(int(TOP),int(yp(c)));ystop=1195
  if ystart>=ystop:continue
  yy=np.arange(ystart,ystop);a=.13*(1-(yy-ystart)/max(1,ystop-ystart))**1.7
  shade=np.clip(np.array([4,6,7])[None,:]+a[:,None]*col[None,:],0,255).astype(np.uint8)
  tails[yy,x]=np.maximum(tails[yy,x],shade)
 im=Image.fromarray(tails);dr=ImageDraw.Draw(im)
 for j,o,h,l,c,width_days in arrs:
  x=xp(j)
  if not -8<=x<=638:continue
  col=RED if c>=o else GREEN;ww=min(9,max(.7,cam['x_scale']*width_days*.61))
  a,b=sorted([yp(o),yp(c)]);yh,yl=yp(h),yp(l)
  if yl<TOP or yh>BOTTOM:continue
  dr.line((x,max(TOP,yh),x,min(BOTTOM,yl)),fill=col,width=1)
  if b>=TOP and a<=BOTTOM:dr.rectangle((x-ww/2,max(TOP,a),x+ww/2,min(BOTTOM,max(a+1,b))),fill=col)
 end=(xp(idx),yp(RAW_C[idx]));flow=RED if RAW_C[idx]>=(RAW_C[idx-1] if idx else RAW_O[idx]) else GREEN
 if 0<=end[0]<640 and TOP<=end[1]<=BOTTOM:im=overlay_glow(im,end,flow,t)
 # Partial-week note is explicit; the row date and value never come from future bars.
 return im,end,xp,yp
