"""Independent pregame-only feature research and multi-season forward evaluation.

Does NOT overwrite the live model. New candidates must earn deployment through
out-of-sample testing with complete historical coverage, never by narrative.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .data import load_data, ROOT, canonical
from .features import build_features, FEATURE_NAMES
from .modeling import scoring

ADDITIONAL = ['elo_difference', 'venue_margin_difference', 'rest_days_difference',
              'five_game_form_difference', 'opponent_quality_difference']
RESEARCH_PATH = ROOT/'artifacts'/'research_report.json'


def _last_margin(history: list[dict], n: int = 5, venue: str | None = None) -> float:
    values=[g['margin'] for g in history if venue is None or g['venue']==venue][-n:]
    return float(np.mean(values)) if values else 0.0


def _rest(history: list[dict], game_day: pd.Timestamp | None) -> float:
    if game_day is None or pd.isna(game_day) or not history:
        return 7.0
    last=history[-1]['date']
    if pd.isna(last):return 7.0
    return float(np.clip((game_day-last).days,0,21))


def augment_features(games: pd.DataFrame, basic: pd.DataFrame | None = None) -> pd.DataFrame:
    """Add pre-week Elo, venue, rest and opponent-quality context.

    Elo updates and history additions happen AFTER *all* games in each week are
    featurized, so same-week results cannot leak even across Thursday–Monday.
    """
    basic = basic if basic is not None else build_features(games)[0]
    ratings=defaultdict(lambda:1500.0)
    past=defaultdict(list)
    details=[]
    previous_season=None
    ordered=games.sort_values(['season','week','game_id'])
    for (season,week),frame in ordered.groupby(['season','week'],sort=True):
        if previous_season is not None and season!=previous_season:
            for team in ratings:
                ratings[team]=1500+.68*(ratings[team]-1500)
        previous_season=season
        pending=[]
        week_games=[]
        for _,g in frame.iterrows():
            h=canonical(g.home_team);a=canonical(g.away_team)
            neutral=str(g.location).lower()=='neutral'
            date=pd.to_datetime(g.gameday,errors='coerce')
            if pd.isna(date):date=None
            hv='neutral' if neutral else 'home';av='neutral' if neutral else 'away'
            # Quality of earlier opposition uses that opponent's rating AS OF
            # THE MATCH, not its later rating or end-of-season record.
            qa=float(np.mean([x['opp_rating'] for x in past[h][-8:]])) if past[h] else 1500.0
            qb=float(np.mean([x['opp_rating'] for x in past[a][-8:]])) if past[a] else 1500.0
            home_adv=0.0 if neutral else 45.0
            details.append({'game_id':str(g.game_id),
                'elo_difference':(ratings[h]-ratings[a]+home_adv)/100.0,
                'venue_margin_difference': _last_margin(past[h],5,hv)-_last_margin(past[a],5,av),
                'rest_days_difference': _rest(past[h],date)-_rest(past[a],date),
                'five_game_form_difference':_last_margin(past[h])-_last_margin(past[a]),
                'opponent_quality_difference':(qa-qb)/100.0})
            if pd.notna(g.home_score) and pd.notna(g.away_score):
                hs=float(g.home_score);aws=float(g.away_score)
                # Freeze both pre-week ratings. Batch Elo adjustments after week.
                expected=1/(1+10**(-((ratings[h]-ratings[a]+home_adv)/400.0)))
                outcome=1.0 if hs>aws else 0.0 if hs<aws else .5
                delta=20*(outcome-expected)
                pending.append((h,a,delta,hs,aws,date,hv,av,ratings[h],ratings[a]))
        # No observations become available until the week is complete.
        for h,a,delta,hs,aws,date,hv,av,rh,ra in pending:
            past[h].append({'date':date,'margin':hs-aws,'venue':hv,'opp_rating':ra})
            past[a].append({'date':date,'margin':aws-hs,'venue':av,'opp_rating':rh})
            ratings[h]+=delta;ratings[a]-=delta
    extras=pd.DataFrame(details)
    output=basic.merge(extras,on='game_id',how='left',validate='one_to_one')
    if output[ADDITIONAL].isna().any().any():
        raise ValueError('Enhanced features are missing for some games')
    return output


def _make_model(name):
    if name in {'Basic logistic','Enhanced logistic'}:
        return make_pipeline(StandardScaler(),LogisticRegression(C=.35,max_iter=2500,random_state=42))
    if name=='Enhanced random forest':
        return RandomForestClassifier(n_estimators=160,max_depth=7,min_samples_leaf=12,n_jobs=-1,random_state=42)
    return HistGradientBoostingClassifier(max_iter=120,learning_rate=.03,max_leaf_nodes=9,
                                          min_samples_leaf=20,l2_regularization=12,random_state=42)


def study(refresh: bool = False, max_folds: int = 4) -> dict:
    games,source=load_data(refresh)
    if 'PARTIAL' in source.upper():
        raise ValueError('This research requires complete seasons. First run with --refresh to download nflverse; the bundled excerpt is incomplete.')
    basic,_=build_features(games)
    augmented=augment_features(games,basic)
    data=augmented.dropna(subset=['outcome']).copy()
    data['outcome']=data['outcome'].astype(int)
    seasons=sorted(data.season.unique().tolist())
    if len(seasons)<5:
        raise ValueError('Need at least 5 seasons to run forward validation')
    # Only FULL historical test seasons; do not evaluate an in-progress season.
    counts=data.groupby('season').size()
    eligible=[int(y) for y in seasons if counts[y]>=240]
    targets=eligible[-max_folds:]
    if len(targets)<2:
        raise ValueError('Need 2 or more complete evaluation seasons (240+ games each)')
    combos={'Basic logistic':FEATURE_NAMES,
            'Enhanced logistic':FEATURE_NAMES+ADDITIONAL,
            'Enhanced random forest':FEATURE_NAMES+ADDITIONAL,
            'Enhanced boosting':FEATURE_NAMES+ADDITIONAL}
    folds=[]
    for year in targets:
        tr=data[(data.season<year)&(data.season>=year-9)]
        te=data[data.season==year]
        if len(tr)<450 or len(set(tr.outcome))<2:continue
        yr={'season':year,'train_games':len(tr),'test_games':len(te),'models':{}}
        for name,cols in combos.items():
            fitted=_make_model(name)
            fitted.fit(tr[cols].values,tr.outcome.values)
            prob=fitted.predict_proba(te[cols].values)[:,1]
            yr['models'][name]=scoring(te.outcome.values,prob)
        folds.append(yr)
    if len(folds)<2:raise ValueError('Not enough chronological folds after training-history checks')
    summary={}
    for model in combos:
        w=sum(f['test_games'] for f in folds)
        summary[model]={k:round(sum(f['test_games']*f['models'][model][k] for f in folds)/w,5)
                        for k in ('accuracy','brier','log_loss')}
    base=summary['Basic logistic']
    # The full-data comparison is descriptive only. Never silently replace a
    # deployed artifact: promotion requires a deliberate second review.
    winner=min(summary,key=lambda name:summary[name]['log_loss'])
    report={'created_at':datetime.now(timezone.utc).isoformat(), 'source':source,
        'years':[f['season'] for f in folds], 'folds':folds,'weighted_summary':summary,
        'best_by_mean_log_loss':winner,'incumbent':'Basic logistic',
        'beats_basic_log_loss':summary[winner]['log_loss']<base['log_loss'],
        'beats_basic_brier':summary[winner]['brier']<base['brier'],
        'production_model_replaced':False,
        'caveats':['Each test year is scored using preceding years only.',
                   'Multiple candidates were compared: selected results require another independent verification before promotion.',
                   'Schedules and scores lack injuries, player health and all play-by-play efficiency.',
                   'Sports outcomes remain uncertain; probabilities cannot be perfect.']}
    RESEARCH_PATH.parent.mkdir(exist_ok=True,parents=True)
    RESEARCH_PATH.write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Evaluate enhanced NFL prediction features against baseline; does not deploy.')
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--folds',type=int,default=4)
    args=parser.parse_args()
    print(json.dumps(study(args.refresh,args.folds),indent=2))
