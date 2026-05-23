import json
from pathlib import Path

path = Path('c:/FIFA WC/tournament_engine/exports/tournament_state.json')
with open(path, 'r', encoding='utf-8') as f:
    state = json.load(f)

print('# FIFA World Cup 2026 — Tournament Results\n')

print('## Group Stage Results\n')
for r in state.get('group_results', []):
    print(f"- **Group {r['group']}, MD{r['matchday']}**: {r['home_team']} {r['home_goals']} - {r['away_goals']} {r['away_team']}")

print('\n## Knockout Stage Results\n')
stages = {
    'R32': 'Round of 32',
    'R16': 'Round of 16',
    'QF': 'Quarter-Finals',
    'SF': 'Semi-Finals',
    '3rd_place': 'Third Place Playoff',
    'Final': 'Final'
}

current_stage = ''
for r in state.get('knockout_results', []):
    if r['stage'] != current_stage:
        current_stage = r['stage']
        print(f'\n### {stages.get(current_stage, current_stage)}\n')
    
    et_marker = ''
    if r.get('penalties'):
        et_marker = f" (PEN {r['penalty_score']})"
    elif r.get('extra_time'):
        et_marker = ' (AET)'
    
    print(f"- **M{r['match_id']}**: {r['home_team']} {r['home_goals']} - {r['away_goals']} {r['away_team']}{et_marker} → **Winner: {r['winner']}**")
