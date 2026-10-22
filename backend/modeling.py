"""Train, select, walk-forward holdout-evaluate, then refit deployable model."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss,confusion_matrix,precision_score,recall_score
from .data import load_data,completed_games,ROOT
from .features import build_features,FEATURE_NAMES

ARTIFACT=ROOT/'artifacts'/'model.joblib'
REPORT=ROOT/'artifacts'/'evaluation.json'
BACKTEST=ROOT/'artifacts'/'backtest.csv'


def make_models():
    return {
        'Logistic regression':make_pipeline(StandardScaler(),LogisticRegression(max_iter=1500,C=0.5,random_state=42)),
        'Random forest':RandomForestClassifier(n_estimators=160,min_samples_leaf=7,max_depth=7,random_state=42,n_jobs=-1),
        'Gradient boosting':HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=9,min_samples_leaf=12,l2_regularization=8,learning_rate=.035,random_state=42),
    }


def scoring(y,p):
    pred=(np.asarray(p)>=0.5).astype(int)
    return {'count':int(len(y)),'accuracy':round(float(accuracy_score(y,pred)),5),
            'precision':round(float(precision_score(y,pred,zero_division=0)),5),
            'recall':round(float(recall_score(y,pred,zero_division=0)),5),
            'log_loss':round(float(log_loss(y,np.clip(p,1e-6,1-1e-6),labels=[0,1])),5),
            'brier':round(float(brier_score_loss(y,p)),5),
            'confusion':confusion_matrix(y,pred,labels=[0,1]).tolist()}


def calibration(y,p):
    d=pd.DataFrame({'actual':y,'probability':p})
    d['bucket']=pd.cut(d.probability,np.linspace(0,1,6),include_lowest=True)
    return [{'predicted':round(float(group.probability.mean()),4),
             'observed':round(float(group.actual.mean()),4),
             'count':int(len(group))}
            for _,group in d.groupby('bucket',observed=True) if len(group)]


def dataset_hash(dataset:pd.DataFrame) -> str:
    """Fingerprints the exact source features + outcomes used in model fitting."""
    canonical=dataset[['game_id','outcome',*FEATURE_NAMES]].copy()
    canonical['outcome']=canonical['outcome'].astype(int)
    values=pd.util.hash_pandas_object(canonical,index=False).values.tobytes()
    return hashlib.sha256(values).hexdigest()[:12]


def train(refresh:bool=False) -> dict:
    games,source=load_data(refresh)
    feats,_=build_features(games)
    dataset=feats.dropna(subset=['outcome']).copy()
    dataset['outcome']=dataset['outcome'].astype(int)
    seasons=sorted(dataset['season'].unique().tolist())
    if len(dataset)<100 or len(seasons)<3:
        raise ValueError(f'Need 100+ finished, non-tied games from 3+ seasons; got {len(dataset)} from {seasons}')
    # Constrain full nflverse training to reasonably modern seasons; the verified
    # offline excerpt may have fewer seasons, so keep all of those.
    if len(seasons)>=6:
        dataset=dataset[dataset.season>=max(2015,seasons[-1]-10)].copy()
        seasons=sorted(dataset.season.unique().tolist())
    val_year,test_year=seasons[-2:]
    tr=dataset[dataset.season<val_year].copy()
    va=dataset[dataset.season==val_year].copy()
    te=dataset[dataset.season==test_year].copy()
    if len(tr)<35 or len(va)<10 or len(te)<10:
        raise ValueError(f'Chronological splits too small: train {len(tr)}, validation {len(va)}, test {len(te)}')
    def xs(frame):return frame[FEATURE_NAMES].astype(float).values
    xtr,xva,xtest=xs(tr),xs(va),xs(te)
    ytr,yva,ytest=(x.outcome.values for x in (tr,va,te))
    if len(set(ytr))<2 or len(set(yva))<2 or len(set(ytest))<2:
        raise ValueError('Each chronological split must contain both home and away wins')
    baseline_rate=float(np.clip(np.mean(ytr),.05,.95))
    candidates={}
    models=make_models()
    for name,model in models.items():
        model.fit(xtr,ytr)
        vprob=model.predict_proba(xva)[:,1]
        candidates[name]={'validation':scoring(yva,vprob),'test':None}
    candidates['Home-field baseline']={'validation':scoring(yva,np.full(len(yva),baseline_rate)),'test':None}
    winner=min(models,key=lambda name:candidates[name]['validation']['log_loss'])
    best=make_models()[winner]
    # Test is evaluated only once, after selection on the validation season.
    train_val=pd.concat([tr,va])
    best.fit(xs(train_val),train_val.outcome.values)
    test_prob=best.predict_proba(xtest)[:,1]
    test_score=scoring(ytest,test_prob)
    baseline_full=float(np.clip(np.mean(train_val.outcome),.05,.95))
    baseline_test=scoring(ytest,np.full(len(te),baseline_full))
    back=te[['game_id','season','week','home_team','away_team','outcome']].copy()
    back['home_win_probability']=test_prob
    back['predicted_home_win']=(test_prob>=.5).astype(int)
    # Deployment fit intentionally includes holdout only AFTER scoring above.
    deployed=make_models()[winner]
    deployed.fit(xs(dataset),dataset.outcome.values)
    datahash=dataset_hash(dataset)
    version=f'{winner.lower().replace(" ","-")}-{datahash}'
    if winner=='Logistic regression':
        impacts=deployed.named_steps['logisticregression'].coef_[0]
    elif winner=='Random forest':
        impacts=deployed.feature_importances_
    else:
        impacts=np.zeros(len(FEATURE_NAMES))  # Not presented as evidence
    importance=sorted([{'feature':k,'importance':round(float(v),5)} for k,v in zip(FEATURE_NAMES,impacts)],key=lambda a:abs(a['importance']),reverse=True)
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'dataset_source':source,
        'coverage':'partial excerpt — refresh required' if 'PARTIAL' in source else 'complete source as downloaded',
        'rows_total':int(len(games)),'finished_regular_games':int(len(completed_games(games))),
        'non_tied_model_rows':int(len(dataset)),
        'training_seasons':sorted(int(x) for x in tr.season.unique()),
        'validation_season':int(val_year),'test_season':int(test_year),
        'training_games':int(len(tr)),'validation_games':int(len(va)),'test_games':int(len(te)),
        'selected_model':winner,'version':version,
        'candidates':candidates,'test':test_score,'baseline_test':baseline_test,
        'calibration':calibration(ytest,test_prob),
        'feature_importance':importance if winner!='Gradient boosting' else [],
        'limitations':['Available schedule scores do not include injuries, starting lineup changes or play-level efficiency.',
                       'Partial offline excerpt, if used, omits many games; refresh for scientifically useful results.',
                       'Predicted probabilities are estimates, not guaranteed outcomes.'],
        'protocol':'Select algorithm using validation log loss, refit on train+validation, evaluate next season once, then refit on all observed seasons for future predictions.'}
    ARTIFACT.parent.mkdir(exist_ok=True,parents=True)
    joblib.dump({'model':deployed,'feature_names':FEATURE_NAMES,'version':version,
                 'data_hash':datahash,'trained_at':report['generated_at'],
                 'through_season':int(dataset.season.max()),'through_week':int(dataset.loc[dataset.season==dataset.season.max(),'week'].max()),
                 'data_source':source},ARTIFACT)
    REPORT.write_text(json.dumps(report,indent=2))
    back.to_csv(BACKTEST,index=False)
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--refresh',action='store_true')
    a=p.parse_args()
    print(json.dumps(train(refresh=a.refresh),indent=2))
