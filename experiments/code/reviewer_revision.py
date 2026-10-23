"""Additive reviewer analysis; never rewrites the frozen scientific runs."""
from __future__ import annotations
import numpy as np


def chow_decide(prob: np.ndarray) -> np.ndarray:
    """Minimize risks in action order NO_MATCH, REVIEW, MATCH; first wins ties.

    Costs: NO_MATCH=(0,1), REVIEW=(.1,.1), MATCH=(2,0), columns y=0,1.
    No labels, validation tuning, or empirical cost estimates are inputs.
    """
    p = np.asarray(prob, dtype=float)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('posterior must be finite and in [0,1]')
    return np.argmin(np.column_stack([p, np.full(p.shape, .1), 2*(1-p)]), axis=1).astype(np.int8)


def metrics(frame) -> dict:
    y, d = frame.actual.to_numpy(), frame.decision.to_numpy()
    tp = int(((y==1)&(d==2)).sum())
    fp = int(((y==0)&(d==2)).sum())
    fn = int(((y==1)&(d==0)).sum())
    rp = int(((y==1)&(d==1)).sum())
    rv = int((d==1).sum())
    candidates = int((frame.pair_type!='BLOCKING_MISS').sum())
    def ratio(n, den):
        return n/den if den else 0.
    return dict(TP=tp, FP=fp, FN=fn, positive_REVIEW=rp, REVIEW=rv,
                candidates=candidates, workflow_rows=len(frame),
                precision=ratio(tp,tp+fp), decision_recall=ratio(tp,tp+fn),
                end_to_end_recall=ratio(tp,tp+fn+rp), decision_F1=ratio(2*tp,2*tp+fp+fn),
                end_to_end_F1=ratio(2*tp,2*tp+fp+fn+rp), review_rate=ratio(rv,candidates),
                coverage=1-ratio(rv,candidates), U=2*fp+fn+.1*rv)

