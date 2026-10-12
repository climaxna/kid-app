import unittest
from unittest.mock import patch
import pipeline as p

class ValidationTests(unittest.TestCase):
    def spec(self):
        return {'source':'dummy.mp4','start':10,'end':30,'title':['첫 줄','두 줄'],'captions':[]}

    def test_time_formats(self):
        self.assertEqual(p.parse_time('2:00.5'),120.5)
        self.assertEqual(p.parse_time('1:02:03'),3723)
        for value in ('NaN','inf','-1'):
            with self.assertRaises(ValueError):p.parse_time(value)

    @patch('pipeline.media_info',return_value={'duration':100})
    def test_reject_outside_source(self,_):
        for start,end in ((-1,10),(10,10),(30,10),(90,101),(0,float('nan'))):
            s=self.spec();s.update(start=start,end=end)
            with self.assertRaises(ValueError):p.validate_spec(s)

    @patch('pipeline.media_info',return_value={'duration':100})
    def test_caption_times_relative_and_nonoverlapping(self,_):
        s=self.spec();s['captions']=[{'start':0,'end':12,'text':'a'},{'start':10,'end':18,'text':'b'}]
        with self.assertRaises(ValueError):p.validate_spec(s)
        s['captions']=[{'start':0,'end':21,'text':'a'}]
        with self.assertRaises(ValueError):p.validate_spec(s)
        s['captions']=[{'start':0,'end':10,'text':'a'},{'start':10,'end':20,'text':'b'}]
        p.validate_spec(s)

    def test_candidates_respect_duration(self):
        segments=[{'start':i,'end':i+4,'text':'왜 그래요?'} for i in range(0,60,4)]
        candidates=p.propose(segments,60)
        self.assertTrue(candidates)
        self.assertTrue(all(0<=c['start']<c['end']<=60 for c in candidates))
        self.assertLessEqual(len(candidates),6)

if __name__=='__main__':unittest.main()
