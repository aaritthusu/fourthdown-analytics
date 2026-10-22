"""Auditable, non-betting team trends computed solely from final scores.

No pattern is asserted for missing games; each card contains its observed denominator
and game IDs. A partial source is explicitly identified as available-record coverage.
"""
from __future__ import annotations
import pandas as pd
from .data import canonical, completed_games, game_to_dict


def _perspective(df: pd.DataFrame, team: str) -> list[dict]:
    result = []
    for _, g in df.iterrows():
        home = g.home_team == team
        if not home and g.away_team != team:
            continue
        scored = int(g.home_score if home else g.away_score)
        conceded = int(g.away_score if home else g.home_score)
        result.append({
            'id': str(g.game_id), 'season': int(g.season), 'week': int(g.week),
            'date': str(g.gameday), 'opponent': str(g.away_team if home else g.home_team),
            'venue': 'neutral' if str(g.location).lower() == 'neutral' else ('home' if home else 'away'),
            'points_for': scored, 'points_against': conceded,
            'margin': scored - conceded, 'win': scored > conceded,
            'tie': scored == conceded,
            'total_points': scored + conceded,
        })
    return result


def _run_length(records: list[dict], condition) -> int:
    length = 0
    for game in records:
        if condition(game):
            length += 1
        else:
            break
    return length


def _card(slug, category, title, games, condition, metric='games', minimum=3):
    sample = len(games)
    if sample < minimum:
        return None
    matches = [g for g in games if condition(g)]
    return {
        'id': slug, 'category': category, 'title': title,
        'hits': len(matches), 'sample': sample,
        'rate': round(len(matches) / sample, 3),
        'current_streak': _run_length(games, condition),
        'sample_note': f'{sample} completed games in available records',
        'game_ids': [g['id'] for g in matches],
        'games': games[:min(len(games), 10)],
        'metric': metric,
    }


def trends(games: pd.DataFrame, team: str, opponent: str | None = None,
           venue: str = 'all', sample_size: int = 5, partial: bool = False) -> dict:
    """Return observed, filter-aware rates and games for independent verification.

    Filters are applied before selecting the most recent N games. No rates are
    generated from future games, unplayed games, or unidentified opponents.
    """
    team = canonical(team)
    opponent = canonical(opponent) if opponent else None
    if venue not in {'all', 'home', 'away', 'neutral'}:
        raise ValueError('venue must be all, home, away, or neutral')
    if not 3 <= sample_size <= 20:
        raise ValueError('sample_size must be between 3 and 20')
    done = completed_games(games).sort_values(['season','week','gameday','game_id'],ascending=False)
    known = set(games.home_team) | set(games.away_team)
    if team not in known or (opponent is not None and opponent not in known):
        raise ValueError('Unknown team or opponent')
    if opponent == team:
        raise ValueError('Opponent must differ from selected team')
    all_team = _perspective(done, team)
    scoped = [g for g in all_team if (opponent is None or g['opponent'] == opponent)
              and (venue == 'all' or g['venue'] == venue)]
    selected = scoped[:sample_size]
    cards=[]
    def add(slug, category, title, condition, minimum=3):
        card = _card(slug,category,title,selected,condition,minimum=minimum)
        if card is not None:
            cards.append(card)
    add('wins','Results','Games won',lambda g:g['win'])
    add('one-score','Results','Decided by 8 points or fewer',lambda g:abs(g['margin'])<=8)
    add('double-digit-win','Results','Wins by 10+ points',lambda g:g['margin']>=10)
    add('scored-24','Offense','Scored at least 24 points',lambda g:g['points_for']>=24)
    add('scored-30','Offense','Scored at least 30 points',lambda g:g['points_for']>=30)
    add('under-17','Defense','Allowed fewer than 17 points',lambda g:g['points_against']<17)
    add('under-21','Defense','Allowed fewer than 21 points',lambda g:g['points_against']<21)
    add('positive-margin','Consistency','Finished with a positive point differential',lambda g:g['margin']>0)
    add('combined-40','Game flow','Both teams combined for 40+ points',lambda g:g['total_points']>=40)
    # These split-specific patterns always refer to the last N games in the
    # split, not last N overall games (important to avoid misleading streaks).
    for key, title in [('home','At home'),('away','On the road')]:
        if venue not in ('all', key):
            continue
        split = [g for g in all_team if g['venue']==key and (opponent is None or g['opponent']==opponent)][:sample_size]
        card=_card(f'{key}-wins','Venue',f'{title}: games won',split,lambda g:g['win'])
        if card:cards.append(card)
        card=_card(f'{key}-scoring','Venue',f'{title}: scored 24+ points',split,lambda g:g['points_for']>=24)
        if card:cards.append(card)
    if opponent is not None:
        h2h = selected
        card=_card('h2h','Head to head',f'Wins against {opponent}',h2h,lambda g:g['win'])
        if card:cards.append(card)
        if venue in ('all', 'home'):
            home_h2h=[g for g in all_team if g['opponent']==opponent and g['venue']=='home'][:sample_size]
            card=_card('h2h-home','Head to head',f'Home wins against {opponent}',home_h2h,lambda g:g['win'])
            if card:cards.append(card)
    averages = (dict(points_for=round(sum(g['points_for'] for g in selected)/len(selected),1),
                     points_against=round(sum(g['points_against'] for g in selected)/len(selected),1),
                     point_margin=round(sum(g['margin'] for g in selected)/len(selected),1))
                if selected else None)
    return {
        'team':team,'opponent':opponent,'venue':venue,'requested_games':sample_size,
        'available_games':len(scoped),'sample_games':len(selected),
        'partial_coverage':partial,'coverage_note':(
            'Incomplete offline excerpt: gaps may exist; streaks and samples refer only to available records.'
            if partial else 'Computed from completed regular-season games in the loaded dataset.'),
        'averages':averages,'cards':cards,'recent_games':selected,
        'filters':{'venues':['all','home','away','neutral'],'sample_sizes':[3,5,8,10,15,20]},
    }
