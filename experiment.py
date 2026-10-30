"""Synthetic statistical falsification experiment; not a detector simulator.
Run: python3 experiment.py. Requires numpy/scipy. Fixed plan below precedes results.
"""
import json
import math
import hashlib
from copy import deepcopy
from pathlib import Path
import numpy as np
from scipy.stats import poisson, binom, beta

PLAN = dict(seed=20261019, families=20000, trials=100, alpha=.01,
            on_mean=.2, off_exposure_ratio=10., injected_signal_mean=6.,
            assumptions='fixed windows/cuts; stationary equal on/off rates; independent on/off Poisson counts; full exposure; trusted quality metadata',
            scope='per-family false-alert probability, not yearly FAR or astrophysical discovery significance')

def valid_count(x):
    return type(x) is int and x >= 0

def decide(event, trials=100, alpha=.01):
    if type(trials) is not int or trials < 1 or not 0 < alpha < 1:
        raise ValueError('invalid frozen family')
    if not isinstance(event, dict):
        return dict(status='INCONCLUSIVE', reason='schema')
    if event.get('retracted') is True:
        return dict(status='RETRACTED', reason='source retraction')
    # External quality/exposure attestations: their truth is NOT verified here.
    flags = ('clock_ok','quality_ok','complete','stationarity_supported')
    if not all(event.get(k) is True for k in flags):
        return dict(status='INCONCLUSIVE', reason='quality/exposure/background')
    a,b,r = event.get('on'),event.get('off'),event.get('ratio')
    if not valid_count(a) or not valid_count(b) or type(r) not in (int,float) or not math.isfinite(r) or r <= 0:
        return dict(status='INCONCLUSIVE', reason='counts/exposure')
    # Conditional on N_on+N_off, the unknown common Poisson rate cancels.
    p = float(binom.sf(a-1,a+b,1/(1+r)))
    return dict(status='CANDIDATE' if p <= alpha/trials else 'NO_THRESHOLD_CROSSING',
                p=p, adjusted_p=min(1.,p*trials))

class Ledger:
    """Bounded in-memory audit reference. No persistence/security claim.
    One immutable analysis per preregistered ID; corrections require new study.
    Retraction withdraws candidate without reclaiming its trial allocation.
    """
    def __init__(self, ids):
        if not ids or len(set(ids)) != len(ids) or not all(type(x) is str and x for x in ids):
            raise ValueError('manifest')
        self.ids=tuple(ids); self.latest={}; self.log=[]
    def apply(self, eid, event):
        if type(eid) is not str or eid not in self.ids:
            raise ValueError('unregistered trial')
        if type(event) is not dict:
            raise ValueError('event schema')
        event=json.loads(json.dumps(event,allow_nan=False))
        if eid in self.latest and event != self.latest[eid]['event'] and event.get('retracted') is not True:
            raise ValueError('revision requires separately budgeted analysis')
        if eid in self.latest and event == self.latest[eid]['event']:
            return deepcopy(self.latest[eid]['result'])
        result=decide(event,len(self.ids))
        payload=json.loads(json.dumps(dict(id=eid,event=event,result=result),allow_nan=False))
        payload['previous']=self.log[-1]['digest'] if self.log else '0'*64
        payload['digest']=hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()
        self.log.append(payload); self.latest[eid]=payload
        return result
    def replay(self):
        replay=Ledger(self.ids)
        for entry in self.log:
            replay.apply(entry['id'],entry['event'])
            if replay.log[-1] != entry:
                raise ValueError('replay mismatch')
        return replay

def interval(k,n):
    return [0. if k==0 else float(beta.ppf(.025,k,n-k+1)),
            1. if k==n else float(beta.ppf(.975,k+1,n-k))]

def summarize(mask):
    k=int(np.count_nonzero(mask));n=int(mask.size)
    return dict(count=k,total=n,rate=k/n,clopper_pearson_95=interval(k,n))

def run():
    rng=np.random.default_rng(PLAN['seed']); n=PLAN['families']; m=PLAN['trials']; alpha=PLAN['alpha']; lam=PLAN['on_mean']; r=PLAN['off_exposure_ratio']
    on=rng.poisson(lam,(n,m));off=rng.poisson(lam*r,(n,m))
    p_oracle=poisson.sf(on-1,lam)
    p_plugin=poisson.sf(on-1,off/r)
    p_exact=binom.sf(on-1,on+off,1/(1+r))
    result={'plan':PLAN,'null':{}}
    for name,p,threshold in [('uncorrected_known_background',p_oracle,alpha),('bonferroni_known_background',p_oracle,alpha/m),('bonferroni_naive_estimated_background',p_plugin,alpha/m),('bonferroni_exact_on_off',p_exact,alpha/m)]:
        result['null'][name]=summarize((p<=threshold).any(axis=1))
    # Separate seed, frozen test, one injected window per family. This is synthetic power.
    sig=np.random.default_rng(PLAN['seed']+1)
    a=sig.poisson(lam+PLAN['injected_signal_mean'],n);b=sig.poisson(lam*r,n)
    result['injected_window_power']=summarize(binom.sf(a-1,a+b,1/(1+r))<=alpha/m)
    # Deliberate assumption failure: on-window background rises 5x; off does not.
    bad=np.random.default_rng(PLAN['seed']+2)
    a=bad.poisson(5*lam,(n,m));b=bad.poisson(lam*r,(n,m))
    result['unflagged_rate_shift_stress']=summarize((binom.sf(a-1,a+b,1/(1+r))<=alpha/m).any(axis=1))
    # Trials may be dependent: all 100 are exact duplicates of one valid pair.
    result['perfectly_correlated_windows']=summarize(p_exact[:,0]<=alpha/m)
    # Overdispersed on and off counts, independently varying rates: assumptions broken.
    stress=np.random.default_rng(PLAN['seed']+3)
    a=stress.negative_binomial(lam/2,1/3,(n,m))
    b=stress.negative_binomial(lam*r/2,1/3,(n,m))
    result['unflagged_overdispersion_stress']=summarize((binom.sf(a-1,a+b,1/(1+r))<=alpha/m).any(axis=1))
    result['notes']=['No full light/particle transport, spatial likelihood or real observations.',
                     'Flags can suppress a known problem; unknown rate shifts can still invalidate inference.',
                     'No blind human custody: seeds are separate, but author can inspect all synthetic data.',
                     'Bonferroni validity needs valid marginal p-values, not independent windows.']
    Path('results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':run()
