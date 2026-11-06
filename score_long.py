"""Original sample-free procedural soundtrack, rebuilt without any audio-file input."""
import argparse
import json
import math
import wave
from pathlib import Path
import numpy as np


def opening_score(sr=44100):
    """Recreate the original eight-second study from oscillators and seeded noise."""
    duration=8;time=np.arange(duration*sr)/sr;y=np.zeros(len(time))
    for k in range(math.ceil(duration/4)):
        a=k*4;b=min(duration,a+4.4);sel=(time>=a)&(time<b);x=time[sel]-a
        root=[45,41,48,43][k%4];env=np.minimum(x/.5,1)*np.minimum((b-a-x)/.8,1)
        for j in [0,7,12,15]:
            hz=440*2**((root+j-69)/12)
            y[sel]+=.025*env*np.sin(2*np.pi*hz*x+.2*np.sin(2*np.pi*.2*x))
    for k in range(duration*2):
        a=k*.5;sel=(time>=a)&(time<a+.24);x=time[sel]-a
        y[sel]+=(.1 if k%2==0 else .045)*np.exp(-x*24)*np.sin(2*np.pi*(46*x+2.5*(1-np.exp(-x*20))))
        if k%2:y[sel]+=.008*np.sin(2*np.pi*3500*x)*np.exp(-x*60)
    y=np.tanh(y*1.5)*np.minimum(time/2,1)*np.minimum((duration-time)/3,1)
    stereo=np.int16(np.clip(np.stack([y,y*.98],axis=1),-1,1)*32767).astype(float)/32767
    effects=np.zeros(len(time));rng=np.random.default_rng(2026)
    sel=time<2.1;x=time[sel];effects[sel]+=.045*(x/2.1)**2*np.sin(2*np.pi*(110*x+190*x*x))
    for onset,amp in [(2.1,.11),(4.567,.18)]:
        sel=(time>=onset)&(time<onset+.8);x=time[sel]-onset
        effects[sel]+=amp*np.exp(-x*8)*np.sin(2*np.pi*(52*x+4*(1-np.exp(-x*12))))
        effects[sel]+=.02*rng.standard_normal(len(x))*np.exp(-x*15)
    stereo+=effects[:,None];stereo*=min(1,.48/max(np.max(np.abs(stereo)),1e-8))
    return stereo.mean(axis=1).astype(np.float32)


def write_score(path,duration,segments=(),crash_dates=(),gold_dates=(),start=0,sr=44100):
    if duration<=0 or start<0 or sr<8000:raise ValueError('Positive duration, nonnegative start and sample rate >=8000 are required')
    full_duration=max(8,start+duration);n=round(full_duration*sr)
    y=np.zeros(n,dtype=np.float32);rng=np.random.default_rng(6284);accents=[]
    for k in range(math.ceil(full_duration/4)):
        a=k*4;i0=round(a*sr);i1=min(n,round((a+4.4)*sr));x=np.arange(i1-i0,dtype=np.float32)/sr
        roots=[45,41,48,43] if a<216 else [48,43,45,41];root=roots[k%4]
        env=np.minimum(x/.5,1)*np.minimum((len(x)/sr-x)/.9,1)
        for offset in [0,7,12,15 if a<216 else 16]:
            hz=440*2**((root+offset-69)/12)
            y[i0:i1]+=.022*env*np.sin(2*np.pi*hz*x+.15*np.sin(2*np.pi*.17*x))
    for k in range(math.ceil(full_duration*2)):
        a=k*.5;i0=round(a*sr);i1=min(n,i0+round(.24*sr));x=np.arange(i1-i0,dtype=np.float32)/sr
        amp=[.065,.085,.055][int(a//32)%3]
        y[i0:i1]+=amp*np.exp(-x*24)*np.sin(2*np.pi*(46*x+2.5*(1-np.exp(-x*20))))
        if k%2:y[i0:i1]+=.006*rng.standard_normal(len(x)).astype(np.float32)*np.exp(-x*60)
    for segment in segments:
        event=segment['event'];onset=segment['start']
        if not event or onset>=full_duration:continue
        i0=round(onset*sr);i1=min(n,i0+round(.9*sr));x=np.arange(i1-i0,dtype=np.float32)/sr
        if event['date'] in crash_dates:
            y[i0:i1]+=.16*np.exp(-x*7)*np.sin(2*np.pi*(48*x+4*(1-np.exp(-x*12))))
            y[i0:i1]+=.025*rng.standard_normal(len(x)).astype(np.float32)*np.exp(-x*16)
            accents.append({'time':onset,'kind':'original synthetic impact','event':event['title']})
        elif event['date'] in gold_dates:
            for j,hz in enumerate([261.626,329.628,391.995,523.251]):
                first=i0+round(j*.13*sr);last=min(n,first+round(1.1*sr))
                if first>=last:continue
                t=np.arange(last-first,dtype=np.float32)/sr
                y[first:last]+=.04*np.exp(-t*3)*np.sin(2*np.pi*hz*t)
            accents.append({'time':onset,'kind':'original chord chime','event':event['title']})
    intro=opening_score(sr);length=min(7*sr,n);y[:length]=intro[:length]
    y*=1.8
    fade=min(2*sr,n);y[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)
    fade=min(round(.5*sr),n);y[:fade]*=np.linspace(0,1,fade,dtype=np.float32)
    y*=min(1,.65/max(float(np.max(np.abs(y))),1e-9))
    y=y[round(start*sr):round((start+duration)*sr)]
    stereo=np.stack((y,y*.985),axis=1);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as output:
        output.setnchannels(2);output.setsampwidth(2);output.setframerate(sr);output.writeframes((stereo*32767).astype(np.int16).tobytes())
    report={'duration':len(y)/sr,'sample_rate':sr,'channels':2,'peak_dbfs':float(20*np.log10(max(np.max(np.abs(y)),1e-12))),'provenance':'Original oscillators and seeded-noise synthesis. No samples, recordings or input WAV files.','accents':[dict(e,time=e['time']-start) for e in accents if start<=e['time']<start+duration],'listening_check':'not performed by script'}
    path.with_suffix('.audio.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));return report


def main():
    parser=argparse.ArgumentParser(description='Generate original music without a market dataset')
    parser.add_argument('--output',default='output/original_score.wav');parser.add_argument('--seconds',type=float,default=12)
    args=parser.parse_args()
    try:write_score(args.output,args.seconds);print(args.output)
    except (ValueError,OSError) as error:parser.error(str(error))
if __name__=='__main__':main()
