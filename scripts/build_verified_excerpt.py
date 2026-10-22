"""Offline demo excerpt manually transcribed from nflverse games.csv.

Public source: https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv
Source checked: 2026-10-21. Each game is a real observation. This is NOT
complete-season data, and it must not be treated as representative for model
science. With internet access, run `python -m backend.modeling --refresh`.
"""
import csv
from pathlib import Path

# week away score home score; exact scores as listed in the source.
DONE={
2024:"""
1 BAL 20 KC 27
1 GB 29 PHI 34
1 PIT 18 ATL 10
1 ARI 28 BUF 34
1 TEN 17 CHI 24
1 NE 16 CIN 10
1 HOU 29 IND 27
1 JAX 17 MIA 20
1 CAR 10 NO 47
2 BUF 31 MIA 10
2 LV 26 BAL 23
2 LAC 26 CAR 3
2 NO 44 DAL 19
2 TB 20 DET 16
2 IND 10 GB 16
2 CLE 18 JAX 13
2 SF 17 MIN 23
2 SEA 23 NE 20
2 NYJ 24 TEN 17
2 NYG 18 WAS 21
2 LA 10 ARI 41
2 PIT 13 DEN 6
2 CIN 25 KC 26
2 CHI 13 HOU 19
2 ATL 22 PHI 21
3 NE 3 NYJ 24
3 NYG 21 CLE 15
3 CHI 16 IND 21
3 HOU 7 MIN 34
3 PHI 15 NO 12
3 LAC 10 PIT 20
3 DEN 26 TB 7
3 GB 30 TEN 14
3 CAR 36 LV 22
3 MIA 3 SEA 24
3 DET 20 ARI 13
3 BAL 28 DAL 25
3 SF 24 LA 27
3 KC 22 ATL 17
3 JAX 10 BUF 47
3 WAS 38 CIN 33
4 DAL 20 NYG 15
4 NO 24 ATL 26
4 CIN 34 CAR 24
4 LA 18 CHI 24
4 MIN 31 GB 29
4 JAX 20 HOU 24
4 PIT 24 IND 27
4 DEN 10 NYJ 9
4 PHI 16 TB 33
4 WAS 42 ARI 14
4 NE 13 SF 30
4 KC 17 LAC 10
4 CLE 16 LV 20
4 BUF 10 BAL 35
4 TEN 31 MIA 12
4 SEA 29 DET 42
5 TB 30 ATL 36
5 NYJ 17 MIN 23
5 CAR 10 CHI 36
5 BAL 41 CIN 38
5 BUF 20 HOU 23
5 IND 34 JAX 37
5 MIA 15 NE 10
5 CLE 13 WAS 34
5 LV 18 DEN 34
""",
2025:"""
1 KC 21 LAC 27
1 TB 23 ATL 20
1 CIN 17 CLE 16
1 MIA 8 IND 33
1 CAR 10 JAX 26
1 LV 20 NE 13
1 ARI 20 NO 13
1 PIT 34 NYJ 32
1 NYG 6 WAS 21
1 TEN 12 DEN 20
1 SF 17 SEA 13
1 DET 13 GB 27
1 HOU 9 LA 14
1 BAL 40 BUF 41
1 MIN 27 CHI 24
2 WAS 18 GB 27
2 CLE 17 BAL 41
2 JAX 27 CIN 31
2 NYG 37 DAL 40
2 CHI 21 DET 52
2 NE 33 MIA 27
2 SF 26 NO 21
2 BUF 30 NYJ 10
2 SEA 31 PIT 17
2 LA 33 TEN 19
2 CAR 22 ARI 27
2 DEN 28 IND 29
2 PHI 20 KC 17
2 ATL 22 MIN 6
2 TB 20 HOU 19
2 LAC 20 LV 9
3 MIA 21 BUF 31
3 ATL 0 CAR 30
3 GB 10 CLE 13
3 HOU 10 JAX 17
3 CIN 10 MIN 48
3 PIT 21 NE 14
3 LA 26 PHI 33
3 NYJ 27 TB 29
3 IND 41 TEN 20
3 LV 24 WAS 41
3 DEN 20 LAC 23
3 NO 13 SEA 44
3 DAL 14 CHI 31
3 ARI 15 SF 16
3 KC 22 NYG 9
3 DET 38 BAL 30
4 SEA 23 ARI 20
4 MIN 21 PIT 24
4 WAS 27 ATL 34
4 NO 19 BUF 31
4 CLE 10 DET 34
4 TEN 0 HOU 26
4 CAR 13 NE 42
4 LAC 18 NYG 21
4 IND 20 LA 27
4 JAX 26 SF 21
4 BAL 20 KC 37
4 CHI 25 LV 24
4 GB 40 DAL 40
4 NYJ 21 MIA 27
4 CIN 3 DEN 28
""",
2026:"""
1 BAL 41 IND 23
1 CLE 10 JAX 34
1 ATL 13 PIT 20
1 NYJ 23 TEN 10
1 ARI 26 LAC 14
1 MIA 13 LV 27
1 GB 22 MIN 39
1 WAS 22 PHI 24
1 DAL 20 NYG 28
1 DEN 10 KC 31
2 DET 31 BUF 41
2 CAR 34 ATL 3
2 NO 24 BAL 17
2 MIN 9 CHI 3
2 CIN 20 HOU 6
2 PIT 3 NE 20
2 GB 20 NYJ 17
2 CLE 23 TB 19
2 PHI 24 TEN 20
2 JAX 13 DEN 20
2 LV 26 LAC 14
2 SEA 31 ARI 7
2 WAS 20 DAL 37
2 MIA 13 SF 35
2 IND 30 KC 33
2 NYG 6 LA 28
3 ATL 35 GB 14
3 LAC 16 BUF 24
3 CAR 18 CLE 21
3 NYJ 24 DET 31
3 HOU 17 IND 19
3 NE 6 JAX 35
3 KC 24 MIA 10
3 TEN 7 NYG 12
3 CIN 27 PIT 30
3 SEA 31 WAS 33
3 ARI 30 SF 36
3 MIN 23 TB 16
3 BAL 34 DAL 31
3 LV 35 NO 27
3 LA 26 DEN 30
3 PHI 7 CHI 27
4 PIT 24 CLE 27
4 IND 30 WAS 13
4 TEN 18 BAL 24
4 NE 29 BUF 26
4 NYJ 12 CHI 23
4 JAX 22 CIN 17
4 DAL 34 HOU 30
4 ARI 24 NYG 36
4 LA 24 PHI 20
4 GB 17 TB 14
4 MIA 10 MIN 15
4 KC 30 LV 27
4 LAC 23 SEA 30
5 IND 22 PIT 34
5 HOU 26 TEN 3
5 NYG 27 WAS 27
5 DEN 23 LAC 17
5 DET 45 ARI 21
5 SF 32 SEA 29
5 BAL 30 ATL 23
5 BUF 37 LA 34
6 SEA 14 DEN 17
6 HOU 34 JAX 31
6 CHI 31 ATL 23
6 BAL 10 CLE 13
6 TEN 26 IND 20
6 NYJ 19 NE 26
6 NO 34 NYG 27
6 CAR 25 PHI 14
6 PIT 26 TB 19
6 ARI 18 LA 16
6 LAC 6 KC 22
6 BUF 33 LV 30
6 DAL 13 GB 23
6 WAS 17 SF 23
"""
}
# Upcoming schedule taken from the same public nflverse source, with actual
# published dates, times, and home/away codes. No outcome is manufactured.
UPCOMING="""
7 2026-10-22 20:15 NE CHI
7 2026-10-25 09:30 PIT NO
7 2026-10-25 13:00 SF ATL
7 2026-10-25 13:00 CIN BAL
7 2026-10-25 13:00 TB CAR
7 2026-10-25 13:00 NYG HOU
7 2026-10-25 13:00 IND MIN
7 2026-10-25 13:00 MIA NYJ
7 2026-10-25 13:00 CLE TEN
7 2026-10-25 16:05 DEN ARI
7 2026-10-25 16:25 GB DET
7 2026-10-25 16:25 LA LV
7 2026-10-25 20:20 KC SEA
7 2026-10-26 20:15 DAL PHI
8 2026-10-29 20:15 CAR GB
8 2026-11-01 13:00 BAL BUF
8 2026-11-01 13:00 TEN CIN
8 2026-11-01 13:00 ARI DAL
8 2026-11-01 13:00 MIN DET
8 2026-11-01 13:00 IND JAX
8 2026-11-01 13:00 LV NYJ
8 2026-11-01 13:00 CLE PIT
8 2026-11-01 13:00 ATL TB
8 2026-11-01 16:05 LAC LA
8 2026-11-01 16:25 KC DEN
8 2026-11-01 16:25 NE MIA
8 2026-11-01 20:20 PHI WAS
8 2026-11-02 20:15 CHI SEA
"""
NEUTRAL={'2024_01_GB_PHI','2025_01_KC_LAC','2025_04_MIN_PIT',
         '2026_03_BAL_DAL','2026_04_IND_WAS','2026_06_HOU_JAX','2026_07_PIT_NO'}
rows=[]
for season,block in DONE.items():
    for line in block.strip().splitlines():
        week,away,aws,home,hs=line.split()
        game_id=f'{season}_{int(week):02d}_{away}_{home}'
        rows.append(dict(game_id=game_id,season=season,game_type='REG',week=int(week),
                         gameday='',gametime='',away_team=away,away_score=int(aws),home_team=home,home_score=int(hs),
                         location='Neutral' if game_id in NEUTRAL else 'Home'))
for line in UPCOMING.strip().splitlines():
    week,date,time,away,home=line.split()
    game_id=f'2026_{int(week):02d}_{away}_{home}'
    rows.append(dict(game_id=game_id,season=2026,game_type='REG',week=int(week),
                     gameday=date,gametime=time,away_team=away,away_score='',home_team=home,home_score='',
                     location='Neutral' if game_id in NEUTRAL else 'Home'))
assert len({r['game_id'] for r in rows})==len(rows),'Duplicate game ID in excerpt'
p=Path(__file__).resolve().parents[1]/'data'/'verified_excerpt.csv'
with p.open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(f'Created {p}, {len(rows)} source-verified rows, {sum(bool(str(x["away_score"])) for x in rows)} completed')
