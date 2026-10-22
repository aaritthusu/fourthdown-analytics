"""FastAPI service. All displayed scores and predictions are from source data/models."""
from __future__ import annotations
import json
import os
from functools import lru_cache
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware
from .data import load_data,game_to_dict,DataUnavailable,ROOT,completed_games
from .features import build_features,FEATURE_NAMES,vector,summarize,team_summaries
from .modeling import ARTIFACT,REPORT,BACKTEST,dataset_hash

app=FastAPI(title='FourthDown Analytics API',version='1.0.0',description='Educational NFL outcome analytics, not wagering advice')
# The production frontend's exact HTTPS origin must be set on the API host.
# Example FRONTEND_ORIGINS=https://example.vercel.app,https://www.example.com
# Avoid reflecting arbitrary origins; this is a public read-only analytics API.
_extra_origins = [origin.strip().rstrip('/') for origin in os.getenv('FRONTEND_ORIGINS', '').split(',') if origin.strip()]
_cors_origins = list(dict.fromkeys(['http://localhost:3000', 'http://127.0.0.1:3000', *_extra_origins]))
app.add_middleware(CORSMiddleware, allow_origins=_cors_origins,
                   allow_credentials=False, allow_methods=['GET'], allow_headers=['*'])

@lru_cache(maxsize=1)
def state():
    try:
        games,source=load_data()
    except (DataUnavailable,ValueError) as e:
        return {'error':str(e)}
    features,history=build_features(games)
    model=None;report=None;backtest=None;model_warning=None
    if ARTIFACT.exists() and REPORT.exists():
        try:
            model=joblib.load(ARTIFACT)
            report=json.loads(REPORT.read_text())
            if BACKTEST.exists():backtest=pd.read_csv(BACKTEST)
            candidate=features.dropna(subset=['outcome']).copy()
            seasons=sorted(candidate.season.unique().tolist())
            if len(seasons)>=6:
                candidate=candidate[candidate.season>=max(2015,seasons[-1]-10)].copy()
            if model.get('data_hash')!=dataset_hash(candidate):
                model=None;report=None;backtest=None
                model_warning='Saved model does not match the currently loaded data; retrain with python -m backend.modeling.'
        except (OSError,ValueError,EOFError,KeyError,TypeError) as exc:
            model=None;report=None;backtest=None;model_warning=f'Model artifact could not be loaded: {exc}'
    comp=completed_games(games)
    last_season=int(games.season.max())
    this_season=games[games.season==last_season]
    valid=this_season.dropna(subset=['home_score','away_score'])
    last_week=int(valid.week.max()) if len(valid) else 0
    return dict(games=games,features=features,history=history,model=model,report=report,backtest=backtest,
                source=source,season=last_season,last_week=last_week,
                total_completed=int(len(comp)),partial=('PARTIAL' in source),model_warning=model_warning)


def get_state():
    s=state()
    if 'error' in s:raise HTTPException(503,s['error'])
    return s


def predict_game(s,home,away,season,week,neutral=False):
    modeldata=s['model']
    if modeldata is None:return None
    teamset=set(s['games'].home_team)|set(s['games'].away_team)
    if home not in teamset or away not in teamset or home==away:raise HTTPException(422,'Select two distinct known teams')
    arr=np.array([vector(home,away,season,week,s['history'],neutral)])
    data=modeldata['model']
    proba=float(data.predict_proba(arr)[0,1])
    fvals=arr[0]
    # Explain the actual decision where linear-model coefficients are available.
    # A standardized coefficient times its standardized feature value is an exact
    # additive contribution to logistic-regression log odds (not causal SHAP).
    contributions=None
    explanation_type='matchup_differences'
    if hasattr(data,'named_steps') and 'logisticregression' in data.named_steps:
        scaler=data.named_steps['standardscaler']
        reg=data.named_steps['logisticregression']
        contributions=((fvals-scaler.mean_)/scaler.scale_) * reg.coef_[0]
        explanation_type='log_odds_contributions'
    factors=[]
    for i,(feature,value) in enumerate(zip(FEATURE_NAMES,fvals)):
        if feature=='home_field':continue
        item={'label':feature.replace('_difference','').replace('_',' ').title(),
              'difference':round(float(value),2)}
        if contributions is not None:
            item['effect_log_odds']=round(float(contributions[i]),4)
        factors.append(item)
    factors.sort(key=lambda d:abs(d.get('effect_log_odds',d['difference'])),reverse=True)
    return {'home':home,'away':away,'season':season,'week':week,
            'home_win_probability':round(proba,4),'away_win_probability':round(1-proba,4),
            'predicted_winner':home if proba>=.5 else away,
            'factors':factors[:5],'explanation_type':explanation_type,'data_cutoff':f'Only results before {season} week {week} are eligible',
            'model_version':modeldata['version'],'generated_at':modeldata['trained_at'],
            'partial_coverage':s['partial']}

@app.get('/api/health')
def health():
    s=state()
    return {'ok':'error' not in s,'model_loaded':bool(s.get('model')),'error':s.get('error'),'model_warning':s.get('model_warning')}

@app.get('/api/overview')
def overview():
    s=get_state(); allg=s['games'];done=completed_games(allg)
    # Only unplayed games from the latest season, sorted by earliest week.
    pending=allg[(allg.season==s['season']) & allg.home_score.isna() & allg.away_score.isna()]
    next_week=int(pending.week.min()) if len(pending) else None
    upcoming=pending[pending.week==next_week].head(16) if next_week else pending
    recent=done.sort_values(['season','week','gameday','game_id'],ascending=False).head(10)
    teams=team_summaries(s['history'],s['season'],s['last_week']+1)
    return {'season':s['season'],'last_completed_week':s['last_week'],'next_week':next_week,
            'source':s['source'],'partial_coverage':s['partial'],'completed_game_count':s['total_completed'],
            'model_ready':s['model'] is not None,'model_warning':s['model_warning'],'model_version':s['model']['version'] if s['model'] else None,
            'model_performance':s['report']['test'] if s['report'] else None,
            'upcoming':[dict(game_to_dict(r),prediction=predict_game(s,r.home_team,r.away_team,int(r.season),int(r.week),str(r.location).lower()=='neutral')) for _,r in upcoming.iterrows()],
            'recent':[game_to_dict(r) for _,r in recent.iterrows()],
            'top_teams':teams[:8]}

@app.get('/api/teams')
def teams(season:int|None=None):
    s=get_state();year=season or s['season']
    valid=s['games'].season.unique().tolist()
    if year not in valid:raise HTTPException(404,'Unknown season')
    # Construct independent week-start team statistics for the chosen season.
    history={k:[v for v in vals if v[0]<=year] for k,vals in s['history'].items()}
    last=int(s['games'].loc[s['games'].season==year,'week'].max())
    return {'season':year,'teams':team_summaries(history,year,last+1),'partial_coverage':s['partial']}

@app.get('/api/compare')
def compare(home:str,away:str,season:int|None=None):
    s=get_state();year=season or s['season']
    if home==away:raise HTTPException(422,'Choose different teams')
    teams={t['team']:t for t in team_summaries(s['history'],year,100)}
    if home not in teams or away not in teams:raise HTTPException(404,'Team not found')
    games=s['games'];filtered=games[(games.season==year) & (((games.home_team==home)&(games.away_team==away))|((games.home_team==away)&(games.away_team==home)))]
    return {'home':teams[home],'away':teams[away],'head_to_head':[game_to_dict(r) for _,r in filtered.iterrows()],
            'partial_coverage':s['partial']}

@app.get('/api/predictions')
def predictions():
    s=get_state();g=s['games'];pending=g[(g.season==s['season'])&g.home_score.isna()&g.away_score.isna()].sort_values(['week','gameday','game_id'])
    upcoming=pending.head(32)
    return {'games':[dict(game_to_dict(r),prediction=predict_game(s,r.home_team,r.away_team,int(r.season),int(r.week),str(r.location).lower()=='neutral')) for _,r in upcoming.iterrows()],
            'version':s['model']['version'] if s['model'] else None,'partial_coverage':s['partial']}

@app.get('/api/predict')
def predict(home:str,away:str,season:int|None=None,week:int|None=None,neutral:bool=False):
    s=get_state()
    season=season or s['season'];week=week or (s['last_week']+1)
    if not 1<=week<=18:raise HTTPException(422,'Week must be 1–18')
    if season!=s['season'] or week<=s['last_week']:
        raise HTTPException(422,'This endpoint only forecasts a future week in the latest loaded season. For past games, use saved out-of-sample backtests in /api/games.')
    return predict_game(s,home,away,season,week,neutral)

@app.get('/api/performance')
def performance():
    s=get_state()
    if not s['report']:raise HTTPException(503,'No training artifact. Run: python -m backend.modeling --refresh')
    return s['report']

@app.get('/api/games')
def games(season:int|None=None,week:int|None=None,team:str|None=None,result:str|None=None,
          limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
    s=get_state(); df=s['games']
    if season is not None:df=df[df.season==season]
    if week is not None:df=df[df.week==week]
    if team is not None:df=df[(df.home_team==team)|(df.away_team==team)]
    if result=='final':df=df.dropna(subset=['home_score','away_score'])
    if result=='scheduled':df=df[df.home_score.isna()]
    df=df.sort_values(['season','week','gameday','game_id'],ascending=False)
    b=s['backtest']
    predmap={str(row.game_id):row for _,row in b.iterrows()} if b is not None else {}
    items=[]
    for _,g in df.iloc[offset:offset+limit].iterrows():
        entry=game_to_dict(g)
        saved=predmap.get(str(g.game_id))
        if saved is not None:entry['historical_prediction']={'home_win_probability':round(float(saved.home_win_probability),4),
            'correct':bool((saved.home_win_probability>=.5)==bool(saved.outcome)),'evaluation_season':int(saved.season)}
        items.append(entry)
    return {'games':items,'count':int(len(df)),'offset':offset,'limit':limit,
            'seasons':sorted(s['games'].season.unique().astype(int).tolist(),reverse=True),
            'partial_coverage':s['partial']}
