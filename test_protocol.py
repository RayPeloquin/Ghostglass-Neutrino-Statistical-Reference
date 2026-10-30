import unittest
from copy import deepcopy
from experiment import Ledger,decide

def good(**kwargs):
    return dict(dict(on=10,off=2,ratio=10,clock_ok=True,quality_ok=True,complete=True,stationarity_supported=True),**kwargs)

class Protocol(unittest.TestCase):
    def test_candidate(self):
        self.assertEqual(decide(good())['status'],'CANDIDATE')
    def test_zero_counts(self):
        self.assertEqual(decide(good(on=0,off=0))['p'],1.)
    def test_zero_off_is_not_zero_background(self):
        self.assertAlmostEqual(decide(good(on=1,off=0))['p'],1/11)
    def test_inconclusive_health(self):
        for flag in ['clock_ok','quality_ok','complete','stationarity_supported']:
            self.assertEqual(decide(good(**{flag:False}))['status'],'INCONCLUSIVE')
    def test_missing_counts(self):
        e=good();del e['on']
        self.assertEqual(decide(e)['status'],'INCONCLUSIVE')
    def test_bad_types(self):
        for v in [True,-1,2.5,None,'3']:
            self.assertEqual(decide(good(on=v))['status'],'INCONCLUSIVE')
        for r in [True,0,-1,float('nan'),float('inf')]:
            self.assertEqual(decide(good(ratio=r))['status'],'INCONCLUSIVE')
    def test_duplicates(self):
        l=Ledger(['a','b']);l.apply('a',good());l.apply('a',good())
        self.assertEqual(len(l.log),1)
    def test_returned_results_cannot_mutate_ledger(self):
        l=Ledger(['a'])
        first=l.apply('a',good())
        first['status']='ALTERED'
        self.assertEqual(l.latest['a']['result']['status'],'CANDIDATE')
        duplicate=l.apply('a',good())
        duplicate['status']='ALTERED'
        self.assertEqual(l.latest['a']['result']['status'],'CANDIDATE')
        self.assertEqual(l.replay().latest,l.latest)
    def test_retraction(self):
        l=Ledger(['a','b']);l.apply('a',good());l.apply('a',{'retracted':True})
        self.assertEqual(l.latest['a']['result']['status'],'RETRACTED')
        self.assertEqual(len(l.ids),2)
        with self.assertRaises(ValueError):l.apply('a',good())
    def test_manifest_budget(self):
        l=Ledger(['a','b']);result=l.apply('a',good(on=2))
        self.assertAlmostEqual(result['adjusted_p'],min(1,2*result['p']))
        with self.assertRaises(ValueError):l.apply('new',good())
    def test_revision_denied(self):
        l=Ledger(['a']);l.apply('a',good())
        with self.assertRaises(ValueError):l.apply('a',good(on=11))
    def test_replay_and_tamper(self):
        l=Ledger(['a','b']);l.apply('a',good());l.apply('b',good(complete=False));l.apply('a',{'retracted':True})
        self.assertEqual(l.replay().latest,l.latest)
        l.log[0]['event']['on']=11
        with self.assertRaises(ValueError):l.replay()
    def test_input_detached(self):
        e=good();l=Ledger(['a']);l.apply('a',e);e['on']=0
        self.assertEqual(l.latest['a']['event']['on'],10)
    def test_invalid_no_mutation(self):
        l=Ledger(['a'])
        for v in [[],None,good(ratio=float('nan'))]:
            with self.assertRaises((ValueError,TypeError)):l.apply('a',v)
        self.assertEqual(l.log,[])

if __name__=='__main__':unittest.main(verbosity=2)
