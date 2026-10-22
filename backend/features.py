"""Leakage-resistant pre-game features, frozen at the start of every NFL week."""
from __future__ import annotations
from collections import defaultdict
import numpy as np
import pandas as pd
from .data import canonical

FIELDS = ['win_rate','points_for','points_against','point_diff','last3_margin','games_played']
FEATURE_NAMES = [f'{c}_difference' for c in FIELDS] + ['home_field']


def summarize(games:list[tuple], season:int, current_week:int) -> dict[str,float]:
    # Prior seasons are deliberately not included in the season's W-L record.
    current=[g for g in games if g[0]==season and g[1]<current_week]
    # Use a rolling window (max 8 earlier games) for skill indicators.
    recent=[g for g in games if g[0]<season or (g[0]==season and g[1]<current_week)][-8:]
    if not recent:
        return {'win_rate':0.5, 'points_for':0.0, 'points_against':0.0, 'point_diff':0.0, 'last3_margin':0.0, 'games_played':0.0}
    margins=[g[2]-g[3] for g in recent]
    win_scores=lambda xs: sum(1 if g[2]>g[3] else .5 if g[2]==g[3] else 0 for g in xs)
    return {
        'win_rate': (win_scores(current)/len(current)) if current else 0.5,
        'points_for': float(np.mean([g[2] for g in recent])),
        'points_against': float(np.mean([g[3] for g in recent])),
        'point_diff': float(np.mean(margins)),
        'last3_margin': float(np.mean(margins[-3:])),
        'games_played': float(len(current)),
    }


def vector(home:str,away:str,season:int,week:int,history:dict,neutral:bool=False):
    home=canonical(home);away=canonical(away)
    a=summarize(history.get(home,[]),season,week)
    b=summarize(history.get(away,[]),season,week)
    return [float(a[f]-b[f]) for f in FIELDS] + [0.0 if neutral else 1.0]


def build_features(games:pd.DataFrame) -> tuple[pd.DataFrame,dict]:
    """All teams in a (season,week) share the SAME frozen history.

    A game result from Friday, Sunday, or Monday cannot leak into another
    match in that week. Future and current game scores are never features.
    """
    games=games.sort_values(['season','week','game_id']).reset_index(drop=True)
    history=defaultdict(list)
    results=[]
    for (season,week), frame in games.groupby(['season','week'],sort=True):
        pending=[]
        for _,g in frame.iterrows():
            neutral=str(g['location']).lower()=='neutral'
            x=vector(g['home_team'],g['away_team'],int(season),int(week),history,neutral)
            row={'game_id':g['game_id'],'season':int(season),'week':int(week),
                 'home_team':g['home_team'],'away_team':g['away_team'],
                 'gameday':g['gameday'],'neutral':neutral,
                 **dict(zip(FEATURE_NAMES,x))}
            if pd.notna(g['home_score']) and pd.notna(g['away_score']):
                # Ties do not fit a binary winner classifier.
                row['outcome'] = (1 if g['home_score']>g['away_score'] else
                                  0 if g['home_score']<g['away_score'] else np.nan)
                hs=float(g['home_score']); aws=float(g['away_score'])
                pending.extend([(canonical(g['home_team']),(int(season),int(week),hs,aws)),
                                (canonical(g['away_team']),(int(season),int(week),aws,hs))])
            else:
                row['outcome']=np.nan
            results.append(row)
        for team,result in pending:
            history[team].append(result)
    return pd.DataFrame(results),dict(history)


def team_summaries(history:dict,season:int,week:int) -> list[dict]:
    rows=[]
    for team, games in history.items():
        current=[x for x in games if x[0]==season and x[1]<week]
        s=summarize(games,season,week)
        wins=sum(x[2]>x[3] for x in current)
        losses=sum(x[2]<x[3] for x in current)
        ties=sum(x[2]==x[3] for x in current)
        rows.append({'team':team,'wins':wins,'losses':losses,'ties':ties,**s})
    return sorted(rows,key=lambda x:(-x['win_rate'],-x['point_diff'],x['team']))
