import json
from pathlib import Path

path = Path('c:/FIFA WC/tournament_engine/exports/tournament_state.json')
with open(path, 'r', encoding='utf-8') as f:
    state = json.load(f)

print('# FIFA World Cup 2026 — Complete Simulation Results\n')

print('## Group Stage (72 Matches)\n')
results = state.get('group_results', [])
for md in [1, 2, 3]:
    print(f'### Matchday {md}\n')
    md_results = [r for r in results if r['matchday'] == md]
    md_results.sort(key=lambda x: x['group'])
    for r in md_results:
        print(f"- **Group {r['group']}:** {r['home_team']} {r['home_goals']} - {r['away_goals']} {r['away_team']}")
    print('')

print('## Knockout Stage (32 Matches)\n')
stages = {
    'R32': 'Round of 32',
    'R16': 'Round of 16',
    'QF': 'Quarter-Finals',
    'SF': 'Semi-Finals',
    '3rd_place': 'Third Place Playoff',
    'Final': 'Final'
}

ko_results = state.get('knockout_results', [])
current_stage = ''
for r in ko_results:
    if r['stage'] != current_stage:
        current_stage = r['stage']
        print(f'\n### {stages.get(current_stage, current_stage)}\n')
    
    extra = ''
    if r.get('penalties'):
        extra = f" (PEN {r['penalty_score']})"
    elif r.get('extra_time'):
        extra = ' (AET)'
    
    print(f"- **M{r['match_id']}:** {r['home_team']} {r['home_goals']} - {r['away_goals']} {r['away_team']}{extra} → **{r['winner']} advances**")

champion = state.get('champion')
runner_up = state.get('runner_up')
print(f'\n## Tournament Summary\n')
print(f'- **CHAMPION:** 🏆 {champion}')
print(f'- **RUNNER-UP:** 🥈 {runner_up}')
