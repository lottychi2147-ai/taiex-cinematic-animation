"""Runnable three-day official open-data demo. Never reads external private data."""
import argparse
import json
from pathlib import Path
from PIL import ImageDraw
import render
from runtime import encode_frames,mux_audio
from branding import stamp

ROOT=Path(__file__).resolve().parent


def preview_frame(data,time,duration):
    index=min(len(data)-1,int(time/duration*len(data)))
    image=render.make_frame(data,index,time,duration,[],overview=False)
    draw=ImageDraw.Draw(image)
    draw.rectangle((32,270,680,355),fill=(5,8,13))
    draw.text((42,285),'三日官方資料・技術預覽',font=render.F[32],fill=render.WHITE)
    draw.rectangle((32,1060,680,1180),fill=(5,8,13))
    draw.text((42,1080),'2026.11.02 — 11.04',font=render.NF[32],fill=render.WHITE)
    draw.text((42,1132),'僅三筆觀測，不代表完整歷史',font=render.F[24],fill=render.DIM)
    draw.rectangle((32,1210,710,1280),fill=(5,8,13))
    draw.text((42,1212),'臺灣證券交易所・政府資料開放授權1.0',font=render.F[18],fill=render.DIM)
    draw.text((42,1243),'原創合成配樂・非投資建議',font=render.F[18],fill=render.DIM)
    return stamp(image)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='output/three_day_preview.mp4')
    parser.add_argument('--seconds',type=float,default=12);parser.add_argument('--fps',type=int,default=30)
    parser.add_argument('--still',action='store_true');args=parser.parse_args()
    try:
        if args.seconds<=0 or args.fps<=0:raise ValueError('Seconds and FPS must be positive')
        data=render.load(ROOT/'data/official_20261102_04.csv')
        out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
        if args.still:
            preview_frame(data,args.seconds*.99,args.seconds).save(out.with_suffix('.png'));print(out.with_suffix('.png'));return
        silent=out.with_name(out.stem+'_silent.mp4')
        actual=encode_frames(lambda t:preview_frame(data,t,args.seconds),silent,args.seconds,args.fps,size=(render.W,render.H))
        from score_long import write_score
        wav=out.with_suffix('.wav');write_score(wav,actual);mux_audio(silent,wav,out)
        report={'duration':actual,'fps':args.fps,'observations':3,'first_date':'2026-11-02','last_date':'2026-11-04','source':'https://data.gov.tw/dataset/11755','data_license':'https://data.gov.tw/license','purpose':'Three-day technical preview, not the full historical film','visual_check':'not performed by script','listening_check':'not performed by script'}
        out.with_suffix('.qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(out)
    except (ValueError,RuntimeError,OSError) as error:parser.error(str(error))
if __name__=='__main__':main()
