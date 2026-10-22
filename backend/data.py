"""Real NFL schedule/results ingestion. No sample data is synthesized."""
from __future__ import annotations
import io
import os
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
RAW_CACHE = DATA_DIR / 'nfl_games.csv'
SNAPSHOT = DATA_DIR / 'verified_excerpt.csv'
URLS = (
    'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv',
    'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv',
)
KEEP = ['game_id', 'season', 'game_type', 'week', 'gameday', 'gametime',
        'away_team', 'away_score', 'home_team', 'home_score', 'location']
ALIASES = {'STL':'LA', 'SD':'LAC', 'OAK':'LV', 'JAC':'JAX', 'WSH':'WAS'}

class DataUnavailable(RuntimeError):
    pass


def canonical(team: str) -> str:
    return ALIASES.get(str(team).upper(), str(team).upper())


def clean(df: pd.DataFrame) -> pd.DataFrame:
    missing = set(KEEP[:4] + ['away_team', 'home_team']) - set(df.columns)
    if missing:
        raise ValueError(f'Missing schedule fields: {sorted(missing)}')
    df = df.copy()
    for col in KEEP:
        if col not in df.columns:
            df[col] = None
    df = df[KEEP]
    df['season'] = pd.to_numeric(df['season'], errors='coerce')
    df['week'] = pd.to_numeric(df['week'], errors='coerce')
    df = df.loc[df['game_type'].astype(str).eq('REG') & df['season'].ge(2002) & df['week'].between(1, 18)].copy()
    for col in ('away_score','home_score'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['home_team'] = df['home_team'].map(canonical)
    df['away_team'] = df['away_team'].map(canonical)
    df['game_id'] = df['game_id'].astype(str)
    df = df.dropna(subset=['game_id','season','week','away_team','home_team'])
    df['season'] = df['season'].astype(int)
    df['week'] = df['week'].astype(int)
    df['gameday'] = df['gameday'].fillna('').astype(str).replace({'nan':''})
    df['gametime'] = df['gametime'].fillna('').astype(str).replace({'nan':''})
    df['location'] = df['location'].fillna('Home').astype(str)
    df = df.sort_values(['season','week','gameday','game_id']).drop_duplicates('game_id',keep='last')
    return df.reset_index(drop=True)


def refresh_data() -> tuple[pd.DataFrame, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    errors=[]
    for url in URLS:
        try:
            r=requests.get(url,timeout=35,headers={'User-Agent':'FourthDownAnalytics/1.0 (+educational project)'})
            r.raise_for_status()
            parsed=clean(pd.read_csv(io.BytesIO(r.content), low_memory=False))
            completed=parsed.dropna(subset=['home_score','away_score'])
            if len(completed)<100 or parsed['season'].max()<2025:
                raise ValueError('Source did not contain at least 100 games and a recent season')
            tmp=RAW_CACHE.with_suffix('.tmp')
            parsed.to_csv(tmp,index=False)
            os.replace(tmp,RAW_CACHE)
            return parsed, f'nflverse schedule, refreshed {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}'
        except (requests.RequestException, ValueError, pd.errors.ParserError) as exc:
            errors.append(f'{url}: {exc}')
    raise DataUnavailable('Unable to refresh: '+'; '.join(errors))


def load_data(refresh: bool=False) -> tuple[pd.DataFrame,str]:
    if refresh:
        return refresh_data()
    if RAW_CACHE.exists():
        try:
            return clean(pd.read_csv(RAW_CACHE,low_memory=False)), f'Local nflverse cache (mtime {datetime.fromtimestamp(RAW_CACHE.stat().st_mtime,timezone.utc).strftime("%Y-%m-%d %H:%M UTC")})'
        except (OSError,ValueError,pd.errors.ParserError):
            pass
    if SNAPSHOT.exists():
        return clean(pd.read_csv(SNAPSHOT)), 'Verified excerpt from nflverse; PARTIAL COVERAGE, refresh for complete statistics'
    return refresh_data()


def completed_games(df:pd.DataFrame) -> pd.DataFrame:
    d=df.dropna(subset=['home_score','away_score']).copy()
    # Ties are retained for team statistics but omitted from binary classifier.
    return d


def game_to_dict(row:pd.Series, status:str|None=None) -> dict:
    ah=row['away_score']; hh=row['home_score']
    completed=pd.notna(ah) and pd.notna(hh)
    return {'id': str(row['game_id']), 'season':int(row['season']), 'week':int(row['week']),
            'date':str(row['gameday']) if row['gameday'] else None,
            'time':str(row['gametime']) if row['gametime'] else None,
            'away':str(row['away_team']),'home':str(row['home_team']),
            'away_score':int(ah) if completed else None,'home_score':int(hh) if completed else None,
            'neutral':str(row['location']).lower()=='neutral',
            'status':status or ('final' if completed else 'scheduled')}
