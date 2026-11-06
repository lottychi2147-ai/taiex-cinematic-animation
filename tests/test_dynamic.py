"""Public samples and visibly artificial in-memory validation fixtures only."""
import json
import math
from pathlib import Path
import subprocess
import tempfile
import zipfile
import hashlib
import sys
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from PIL import Image
import render
import camera_film as camera
import dynamic_film as dynamic
from branding import stamp,validate_label
ROOT=Path(__file__).resolve().parents[1]

class DynamicTests(unittest.TestCase):
 def setUp(self):
  self.data=render.load(ROOT/'data/official_20261102_04.csv')
 def test_import_reads_no_market_data(self):
  subprocess.run([sys.executable,'-c','import dynamic_film as d; assert d.DAILY is None; assert d.CAM == []'],cwd=ROOT,check=True)
 def test_first_session_change_is_unknown(self):
  dynamic.initialize(self.data,demo=True,duration=1)
  original=dynamic.ImageDraw.ImageDraw.text
  for idx in [0,1]:
   captured={}
   def capture(draw,xy,text,*args,**kwargs):
    captured[xy]=text
    return original(draw,xy,text,*args,**kwargs)
   with patch.object(dynamic.ImageDraw.ImageDraw,'text',capture):
    dynamic.header(Image.new('RGB',(720,1280)),7,idx,render.RED,0)
   if idx==0:
    self.assertEqual(captured[(487,185)],'N/A')
    self.assertEqual(captured[(487,225)],'未提供前收')
   else:
    change=self.data.close.iloc[1]-self.data.close.iloc[0]
    self.assertEqual(captured[(487,185)],f'{change/self.data.close.iloc[0]*100:+.2f}%')
    self.assertEqual(captured[(487,225)],f'{change:+,.2f} 點')
 def test_full_story_rejects_short_sample(self):
  with self.assertRaisesRegex(ValueError,'matching'):dynamic.initialize(self.data)
 def test_label_validation(self):
  for label in ['x'*65,'bad\nlabel',None]:
   with self.assertRaises(ValueError):validate_label(label)
 def test_watermark_visible_and_optional(self):
  im=Image.new('RGB',(720,1280))
  self.assertEqual(stamp(im.copy(),'').tobytes(),im.tobytes())
  self.assertNotEqual(stamp(im.copy()).tobytes(),im.tobytes())
 def test_invalid_duration(self):
  for duration in [0,-1,float('nan'),float('inf'),.001]:
   with self.assertRaises(ValueError):camera.initialize(self.data,demo=True,duration=duration)
 def test_demo_camera_and_true_observations(self):
  dynamic.initialize(self.data,demo=True,duration=3,source_label='TWSE public sample')
  self.assertEqual(len(camera.CAM),90)
  self.assertGreater(np.ptp([c['span'] for c in camera.CAM]),.1)
  self.assertEqual([camera.observed(t)[0] for t in [0,.99,1,1.99,2,2.99]],[0,0,1,1,2,2])
  np.testing.assert_array_equal(camera.RAW_C,self.data.close)
  for c in camera.CAM:
   self.assertTrue(all(math.isfinite(c[k]) for k in ['lo','hi','span','x_scale','y_scale']))
   self.assertLess(c['lo'],self.data.low.iloc[c['index']]);self.assertGreater(c['hi'],self.data.high.iloc[c['index']])
  for t in [0,.8,1,2.2,2.99]:
   a=dynamic.render_frame(t);b=dynamic.render_frame(t)
   self.assertEqual(a.size,(720,1280));self.assertEqual(a.mode,'RGB');self.assertEqual(a.tobytes(),b.tobytes())
  for t in [-1,3,float('nan')]:
   with self.assertRaises(ValueError):dynamic.render_frame(t)
 def test_partial_week_uses_only_reached_rows(self):
  camera.initialize(self.data,demo=True,duration=1)
  for idx in range(3):
   self.assertEqual(camera.PART_O[idx],self.data.open.iloc[0])
   self.assertEqual(camera.PART_H[idx],self.data.high.iloc[:idx+1].max())
   self.assertEqual(camera.PART_L[idx],self.data.low.iloc[:idx+1].min())
 def test_fx_protects_information_planes(self):
  dynamic.initialize(self.data,demo=True,duration=3)
  im=Image.new('RGB',(720,1280),(4,7,12));result=dynamic.fx(im.copy(),2.2,2,(500,900),render.RED)
  # Glow is also clipped, not merely its sharp light source.
  self.assertEqual(im.crop((0,0,720,499)).tobytes(),result.crop((0,0,720,499)).tobytes())
  self.assertEqual(im.crop((0,1190,720,1280)).tobytes(),result.crop((0,1190,720,1280)).tobytes())
 def test_strict_package_members_and_hashes(self):
  import build_source_zip as package
  with tempfile.TemporaryDirectory() as folder:
   a=Path(folder)/'a.zip';b=Path(folder)/'b.zip'
   self.assertEqual(package.build(a),package.build(b))
   with zipfile.ZipFile(a) as archive:
    expected={'taiex_cinematic/'+name for name in package.FILES}|{'taiex_cinematic/SHA256SUMS'}
    self.assertEqual(set(archive.namelist()),expected)
    for line in archive.read('taiex_cinematic/SHA256SUMS').decode().splitlines():
     digest,name=line.split('  ',1)
     self.assertEqual(digest,hashlib.sha256(archive.read('taiex_cinematic/'+name)).hexdigest())
 def test_full_story_artificial_fixture(self):
  # Intentionally artificial observations, not a historical market-data fixture.
  dates=pd.bdate_range('1999-01-05','2026-11-06')
  close=np.linspace(6000,18000,len(dates));data=pd.DataFrame({'date':dates,'close':close})
  for event in json.loads((ROOT/'data/verified_milestones.json').read_text())['events']:
   if 'close' in event:data.loc[data.date.eq(event['date']),'close']=event['close']
  data['open']=data.close;data['high']=data.close+10;data['low']=data.close-10;data['ohlc_verified']=True
  dynamic.initialize(data)
  self.assertEqual(len(camera.CAM),232*30)
  self.assertEqual(len(dynamic.ANNUAL),26)
  for t in [0,2.2,6.8,7,58,150,209,215,216,225,230]:
   self.assertEqual(dynamic.render_frame(t).size,(720,1280))
  # Reset does not retain historical arrays or cues in the short public demo.
  dynamic.initialize(self.data,demo=True,duration=1)
  self.assertEqual(dynamic.N,3);self.assertEqual(dynamic.EVENT_CUES,[])

if __name__=='__main__':unittest.main()
