"""Screen-space credit applied after effects, with configurable text."""
from PIL import ImageDraw

def validate_label(value):
 if not isinstance(value,str) or len(value)>64 or any(ord(c)<32 for c in value):
  raise ValueError('Labels must be at most 64 characters, without control characters')
 return value

def stamp(image,text='紀順文X小狐AI'):
 validate_label(text)
 if not text:return image
 from render import font
 dr=ImageDraw.Draw(image);size=22;ft=font(size)
 while dr.textbbox((0,0),text,font=ft)[2]>image.width-60 and size>8:
  size-=1;ft=font(size)
 box=dr.textbbox((0,0),text,font=ft);w=box[2]-box[0]
 x=image.width-w-30;y=15
 dr.rounded_rectangle((x-9,y-3,image.width-21,y+size+10),radius=5,fill=(5,12,18))
 dr.text((x,y),text,font=ft,fill=(212,230,239))
 return image
