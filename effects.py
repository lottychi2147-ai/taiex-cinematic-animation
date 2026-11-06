"""Original deterministic visual accents; no borrowed effect code or assets."""
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

def endpoint_bloom(image,point,color,time):
 layer=Image.new('RGB',image.size);d=ImageDraw.Draw(layer);x,y=point
 radius=14+3*math.sin(time*4)
 d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color)
 glow=layer.filter(ImageFilter.GaussianBlur(16))
 out=Image.fromarray(np.clip(np.asarray(image).astype(np.uint16)+np.asarray(glow).astype(np.uint16),0,255).astype(np.uint8))
 d=ImageDraw.Draw(out)
 # Fixed phases: rerendering a timestamp always produces identical particles.
 for k in range(28):
  phase=(time*.3+k/28)%1;angle=k*2.39996
  px=x+math.cos(angle)*phase*70;py=y+math.sin(angle)*phase*55
  c=tuple(int(v*(1-phase)*.7) for v in color)
  d.ellipse((px-1,py-1,px+1,py+1),fill=c)
 d.ellipse((x-3.5,y-3.5,x+3.5,y+3.5),fill=(245,255,253))
 return out


def overlay_glow(image, point, color, time):
 """Original crop-based endpoint glow; independent of any private renderer."""
 x,y=point;width,height=image.size
 left=max(0,int(x)-90);top=max(0,int(y)-90)
 right=min(width,int(x)+90);bottom=min(height,int(y)+90)
 if left>=right or top>=bottom:return image
 crop=image.crop((left,top,right,bottom))
 crop=endpoint_bloom(crop,(x-left,y-top),color,time)
 image.paste(crop,(left,top))
 return image
