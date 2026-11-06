"""Public tests use only licensed short samples and clearly artificial fixtures."""
import csv
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
import wave
import numpy as np
from PIL import Image
import render
import high_fidelity_hook as hook
import long_film as film
from effects import endpoint_bloom,overlay_glow
from runtime import input_path
from score_long import write_score
from timeline import observation_at

ROOT=Path(__file__).resolve().parents[1]

class DataTests(unittest.TestCase):
    def load_rows(self,rows):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'artificial_fixture.csv'
            path.write_text(rows)
            return render.load(path)
    def test_official_three_days(self):
        data=render.load(ROOT/'data/official_20261102_04.csv')
        self.assertEqual(len(data),3);self.assertTrue(data.ohlc_verified.all())
        self.assertEqual(str(data.iloc[0].date.date()),'2026-11-02')
        self.assertEqual(str(data.iloc[-1].date.date()),'2026-11-04')
    def test_official_eleven_days(self):
        self.assertEqual(len(render.load(ROOT/'data/official_archive_20261001_16.csv')),11)
    def test_close_only(self):
        data=self.load_rows('date,close\n2020-01-02,100\n2020-01-03,101\n')
        self.assertFalse(data.ohlc_verified.any())
        self.assertEqual(render.make_frame(data,1,1,2,[]).size,(720,1280))
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):self.load_rows('date,close\n2020-01-02,100\n2020-01-02,101\n')
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):self.load_rows('date,close\n')
    def test_missing_column_rejected(self):
        with self.assertRaises(ValueError):self.load_rows('date,price\n2020-01-02,100\n')
    def test_nonfinite_rejected(self):
        for value in ['nan','inf','-inf','0','-1']:
            with self.subTest(value=value),self.assertRaises(ValueError):self.load_rows('date,close\n2020-01-02,'+value+'\n')
    def test_verified_missing_ohlc_rejected(self):
        with self.assertRaises(ValueError):self.load_rows('date,close,ohlc_verified\n2020-01-02,100,true\n')
    def test_invalid_bounds_rejected(self):
        with self.assertRaises(ValueError):self.load_rows('date,close,open,high,low,ohlc_verified\n2020-01-02,100,101,99,95,true\n')
    def test_invalid_flag_rejected(self):
        with self.assertRaises(ValueError):self.load_rows('date,close,ohlc_verified\n2020-01-02,100,yes\n')
    def test_no_implicit_input(self):
        with patch.dict(os.environ,{},clear=True),self.assertRaisesRegex(ValueError,'--data'):input_path()
    def test_environment_input(self):
        path=ROOT/'data/official_20261102_04.csv'
        with patch.dict(os.environ,{'TAIEX_INPUT_CSV':str(path)}):self.assertEqual(input_path(),path)
    def test_missing_path(self):
        with self.assertRaisesRegex(ValueError,'does not exist'):input_path('nonexistent_authorized_input.csv')
    def test_no_market_load_at_import(self):
        subprocess.run([sys.executable,'-c','import high_fidelity_hook as h, long_film as f; assert h.DAILY is None and f.DAILY is None'],cwd=ROOT,check=True)
    def test_short_sample_rejects_full_story(self):
        with self.assertRaisesRegex(ValueError,'matching'):film.validate_story_data(render.load(ROOT/'data/official_20261102_04.csv'))

class VisualTests(unittest.TestCase):
    def test_effect_deterministic(self):
        image=Image.new('RGB',(160,160),(4,6,7))
        self.assertEqual(endpoint_bloom(image,(80,80),(255,0,0),2).tobytes(),endpoint_bloom(image,(80,80),(255,0,0),2).tobytes())
    def test_crop_glow_offscreen(self):
        image=Image.new('RGB',(160,160));self.assertIs(overlay_glow(image,(-300,-300),(255,0,0),2),image)
    def test_preview_observations(self):
        from preview import preview_frame
        data=render.load(ROOT/'data/official_20261102_04.csv')
        for time in [0,4,8,11.99]:
            image=preview_frame(data,time,12);self.assertEqual(image.size,(720,1280));self.assertEqual(image.mode,'RGB')
    def test_timeline_boundaries(self):
        for time in [-1,0,1,6,12,20]:
            index,_,_=observation_at(time,12,3,[])
            self.assertIn(index,range(3))
        self.assertEqual(observation_at(12,12,3,[])[0],2)
    def test_hook_short_duration(self):
        self.assertTrue(observation_at(0,2,20,[2,3,4])[1])
        self.assertEqual(observation_at(2,2,20,[2,3,4])[0],19)
    def test_timeline_invalid(self):
        for args in [(0,0,3,[]),(0,1,0,[]),(float('nan'),1,3,[]),(0,1,3,[9])]:
            with self.assertRaises(ValueError):observation_at(*args)
    def test_event_citations(self):
        events=json.loads((ROOT/'data/verified_milestones.json').read_text())
        self.assertTrue(all(event['sources'] for event in events['events']))
        self.assertEqual(events['historical_reference_line']['value'],12682.41)
    def test_audio_deterministic_and_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a.wav';b=Path(folder)/'b.wav'
            qa=write_score(a,.25,sr=8000);write_score(b,.25,sr=8000)
            self.assertEqual(a.read_bytes(),b.read_bytes());self.assertLessEqual(qa['peak_dbfs'],0)
            with wave.open(str(a),'rb') as wav:
                self.assertEqual(wav.getnframes(),2000);self.assertEqual(wav.getnchannels(),2)
if __name__=='__main__':unittest.main()
