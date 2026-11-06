"""Original TAIEX animation engine. No copied creator assets or fabricated OHLC.
Input CSV: date,close[,open,high,low,ohlc_verified]. Boolean true is required for candles.
Missing OHLC ALWAYS uses observed close line. Never interpolate observations as facts.
"""
import argparse,json,math,subprocess,wave,os
from runtime import input_path, font_path, encode_frames, mux_audio
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from timeline import observation_at
from effects import endpoint_bloom
ROOT=Path(__file__).resolve().parent
CONFIG=json.loads((ROOT/'config.json').read_text())
FONT=font_path('cjk',CONFIG['fonts']['cjk'])
NUM=font_path('latin',CONFIG['fonts']['latin'])
W,H=CONFIG['canvas']['width'],CONFIG['canvas']['height']
RED=tuple(CONFIG['theme']['up']); GREEN=tuple(CONFIG['theme']['down']); WHITE=(237,242,247); DIM=(116,132,149)
def font(n,num=False): return ImageFont.truetype(NUM if num else FONT,n,index=int(os.environ.get('TAIEX_CJK_FACE_INDEX',CONFIG['fonts'].get('cjk_face_index',0))) if not num else 0)
F={n:font(n) for n in [18,22,24,28,32,38,44,52,64,80]}
NF={n:font(n,True) for n in [20,26,32,50,72,90]}
def load(path):
 """Validate observations without interpolating, deduplicating or repairing prices."""
 d=pd.read_csv(path)
 d.columns=d.columns.str.strip().str.lower()
 if not {'date','close'}.issubset(d.columns):raise ValueError('CSV requires date and close columns')
 if d.empty:raise ValueError('CSV contains no observations')
 d['date']=pd.to_datetime(d['date'],format='%Y-%m-%d',errors='raise')
 if d.date.isna().any() or d.date.duplicated().any():raise ValueError('Dates must be present and unique')
 d=d.sort_values('date').reset_index(drop=True)
 d['close']=pd.to_numeric(d.close,errors='raise')
 if not np.isfinite(d.close.to_numpy()).all() or not (d.close>0).all():raise ValueError('Close values must be finite and positive')
 if 'ohlc_verified' not in d:d['ohlc_verified']=False
 flags=d.ohlc_verified.fillna(False).astype(str).str.strip().str.lower()
 if not flags.isin(['true','false']).all():raise ValueError('ohlc_verified must be true or false')
 d['ohlc_verified']=flags.eq('true')
 for c in ['open','high','low']:
  if c not in d:d[c]=np.nan
  d[c]=pd.to_numeric(d[c],errors='raise')
 valid=d.ohlc_verified
 values=d.loc[valid,['open','high','low']].to_numpy()
 if not np.isfinite(values).all() or not (values>0).all():raise ValueError('Verified OHLC values must be finite and positive')
 if not (d.loc[valid,'high']>=d.loc[valid,['open','close']].max(axis=1)).all():raise ValueError('High must be at least open and close')
 if not (d.loc[valid,'low']<=d.loc[valid,['open','close']].min(axis=1)).all():raise ValueError('Low must be at most open and close')
 return d

def write_music(path,duration,sr=44100):
 """Original procedural soundtrack; no samples, third-party melodies or recordings."""
 n=int(duration*sr); t=np.arange(n)/sr; y=np.zeros(n,dtype=np.float64)
 # A minor progression, breathing chord pads, separate tension/relief sections.
 for k in range(math.ceil(duration/4)):
  a=k*4; b=min(duration,a+4.4); sel=(t>=a)&(t<b); x=t[sel]-a
  roots=[45,41,48,43]; root=roots[k%4]; env=np.minimum(x/.5,1)*np.minimum((b-a-x)/.8,1)
  for j in [0,7,12,15]:
   hz=440*2**((root+j-69)/12); y[sel]+=.025*env*np.sin(2*np.pi*hz*x+.2*np.sin(2*np.pi*.2*x))
 beat=.5
 for k in range(int(duration/beat)):
  a=k*beat; sel=(t>=a)&(t<a+.24); x=t[sel]-a
  y[sel]+=(.1 if k%2==0 else .045)*np.exp(-x*24)*np.sin(2*np.pi*(46*x+2.5*(1-np.exp(-x*20))))
  if k%2: y[sel]+=.008*np.sin(2*np.pi*3500*x)*np.exp(-x*60)
 fade=np.minimum(t/2,1)*np.minimum((duration-t)/3,1); y=np.tanh(y*1.5)*fade
 stereo=np.stack([y,y*.98],axis=1); pcm=np.int16(np.clip(stereo,-1,1)*32767)
 with wave.open(str(path),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes(pcm.tobytes())
 return {'peak_dbfs':float(20*np.log10(np.max(np.abs(y)))),'duration':duration,'provenance':'Original procedural synthesis, no samples'}
def make_frame(d,idx,t,duration,events,overview=False,hook=False):
 row=d.iloc[idx]; val=float(row.close); prev=float(d.iloc[idx-1].close) if idx>0 else (float(row.open) if row.ohlc_verified else val); color=RED if val>=prev else GREEN
 im=Image.new('RGB',(W,H),tuple(CONFIG['theme']['background'])); draw=ImageDraw.Draw(im)
 draw.text((42,55),'加權指數',font=F[32],fill=WHITE);draw.text((224,65),'TAIEX',font=NF[20],fill=DIM)
 draw.text((38,98),f'{val:,.2f}',font=NF[72],fill=color)
 draw.text((44,188),row.date.strftime('%Y.%m.%d'),font=NF[26],fill=WHITE)
 mode='真實 OHLC' if row.ohlc_verified else '歷史收盤走勢'
 draw.text((44,230),mode,font=F[22],fill=DIM)
 start=0 if overview else max(0,idx-150)
 sub=d.iloc[start:idx+1]
 values=sub.close.to_numpy(); lo=float(values.min()); hi=float(values.max())
 verified=sub[sub.ohlc_verified]
 if len(verified):lo=min(lo,float(verified.low.min()));hi=max(hi,float(verified.high.max()))
 span=max(hi-lo,hi*.08)
 low=max(0,lo-span*.12); high=hi+span*.28
 x0,x1,y0,y1=42,622,372,1020
 def xp(i):return x0+(i-start)/(max(2,len(d)-1) if len(d)<20 else max(55,idx-start))*(x1-x0)
 def yp(v):return y1-(v-low)/(high-low)*(y1-y0)
 for lev in np.linspace(low,high,5):
  yy=yp(lev);draw.line((x0,yy,x1+8,yy),fill=(22,29,38),width=1);draw.text((635,yy-10),f'{lev:,.0f}',font=NF[20],fill=DIM)
 pts=[(xp(j),yp(float(d.iloc[j].close))) for j in range(start,idx+1)]
 if len(pts)>1:
  glow=Image.new('RGB',(W,H));gd=ImageDraw.Draw(glow);gd.line(pts,fill=color,width=6);glow=glow.filter(ImageFilter.GaussianBlur(12));im=Image.blend(im,Image.fromarray(np.clip(np.asarray(im).astype(int)+np.asarray(glow).astype(int),0,255).astype('uint8')),0.65);draw=ImageDraw.Draw(im)
  for j in range(start+1,idx+1):
   r=d.iloc[j]; p=d.iloc[j-1];c=RED if r.close>=p.close else GREEN
   if r.ohlc_verified and idx-start<350 and not overview:
    xx=xp(j);ww=max(2,min(20,(x1-x0)/(max(2,len(d)-1) if len(d)<20 else max(55,idx-start))*.55));draw.line((xx,yp(r.high),xx,yp(r.low)),fill=c,width=1)
    top,bottom=sorted([yp(r.open),yp(r.close)]);draw.rectangle((xx-ww/2,top,xx+ww/2,max(top+1,bottom)),fill=c)
   else:draw.line((xp(j-1),yp(p.close),xp(j),yp(r.close)),fill=c,width=3 if not overview else 2)
 if pts and sub.iloc[0].ohlc_verified:
  xx,yy=pts[0];first=sub.iloc[0];cc=RED if first.close>=first.open else GREEN
  draw.line((xx,yp(first.high),xx,yp(first.low)),fill=cc,width=2)
  top,bottom=sorted([yp(first.open),yp(first.close)]);draw.rectangle((xx-3,top,xx+3,max(top+1,bottom)),fill=cc)
 if pts:
  xx,yy=pts[-1];draw.line((xx,yy,xx,y1+35),fill=tuple(int(c*.2) for c in color),width=1);draw.ellipse((xx-6,yy-6,xx+6,yy+6),fill=WHITE)
 peak=float(d.iloc[:idx+1].close.max()); dd=(val/peak-1)*100
 if dd<-15:
  draw.text((42,288),f'{dd:.1f}%',font=NF[50],fill=GREEN);draw.text((270,310),'距先前收盤高點',font=F[22],fill=DIM)
 ev=next((e for e in events if pd.Timestamp(e['start'])<=row.date<=pd.Timestamp(e['end'])),None)
 if ev:
  title=ev['title']; fs=52 if len(title)<10 else 38
  box=draw.textbbox((0,0),title,font=F[fs]); tw=box[2]
  draw.rounded_rectangle((32,1060,655,1160),radius=14,fill=(16,24,34));draw.text(((W-tw)/2,1079),title,font=F[fs],fill=WHITE)
 else:draw.text((42,1080),f'{row.date.year}  /  台股歷史',font=F[38],fill=WHITE)
 progress=t/duration; draw.line((42,1200,650,1200),fill=(41,48,57),width=3);draw.line((42,1200,42+608*progress,1200),fill=color,width=3)
 draw.text((42,1220),'歷史資料視覺化・不構成投資建議',font=F[18],fill=DIM)
 if hook:draw.text((42,348),'從高峰，到谷底',font=F[44],fill=WHITE)
 if pts:im=endpoint_bloom(im,pts[-1],color,t)
 return im

def main():
 p=argparse.ArgumentParser(description='Original TAIEX renderer. Supply authorized observations explicitly.')
 p.add_argument('--data');p.add_argument('--events');p.add_argument('--output',default='output/taiex.mp4');p.add_argument('--duration',type=float,default=CONFIG['story']['duration_seconds']);p.add_argument('--fps',type=int,default=CONFIG['canvas']['fps']);p.add_argument('--preview',action='store_true')
 a=p.parse_args()
 try:
  d=load(input_path(a.data))
  if a.duration<=0 or a.fps<=0:raise ValueError('Duration and FPS must be positive')
  events=json.loads(Path(a.events).read_text()) if a.events else []
  out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
  if a.preview:
   make_frame(d,len(d)-1,1,2,events).save(out.with_suffix('.png'));print(out.with_suffix('.png'));return
  hooks=d.index[(d.date>=CONFIG['story']['hook_start'])&(d.date<=CONFIG['story']['hook_end'])].to_numpy()
  def draw(t):
   idx,is_hook,overview=observation_at(t,a.duration,len(d),hooks,CONFIG['story']['hook_seconds'],CONFIG['story']['overview_seconds'])
   return make_frame(d,idx,t,a.duration,events,overview=overview,hook=is_hook)
  silent=out.with_name(out.stem+'_silent.mp4')
  actual=encode_frames(draw,silent,a.duration,a.fps,size=(W,H))
  wav=out.with_suffix('.wav');qa=write_music(wav,actual);mux_audio(silent,wav,out)
  qa.update({'first_date':str(d.date.min().date()),'last_date':str(d.date.max().date()),'observations':len(d),'verified_ohlc_rows':int(d.ohlc_verified.sum()),'visual_check':'not performed by script','listening_check':'not performed by script'})
  out.with_suffix('.qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2));print(out)
 except (ValueError,RuntimeError,OSError) as error:p.error(str(error))
if __name__=='__main__':main()
