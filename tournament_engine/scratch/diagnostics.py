import json
from pathlib import Path

state_path = Path('c:/FIFA WC/tournament_engine/exports/tournament_state.json')
with open(state_path, 'r', encoding='utf-8') as f:
    state = json.load(f)

ko = state.get('knockout_results', [])
total = len(ko)
et_count  = sum(1 for m in ko if m.get('extra_time'))
pen_count = sum(1 for m in ko if m.get('penalties'))
upsets    = sum(1 for m in ko if m.get('is_upset'))
dramatic  = sum(1 for m in ko if m.get('is_dramatic'))

print('=== Phase 4.2 Realism Diagnostics ===')
print(f'Total KO matches : {total}')
print(f'Extra Time       : {et_count} ({et_count/total*100:.1f}%)  [target: 20-30%]')
print(f'Penalties        : {pen_count} ({pen_count/total*100:.1f}%)  [target:  8-15%]')
print(f'Upsets (flagged) : {upsets} ({upsets/total*100:.1f}%)')
print(f'Dramatic matches : {dramatic} ({dramatic/total*100:.1f}%)')

print()
print('=== Knockout Match Detail ===')
for m in ko:
    stage = m['stage']
    extra = ' [AET]' if m.get('extra_time') else ''
    ps    = m.get('penalty_score', '')
    pens  = f' (PEN {ps})' if m.get('penalties') else ''
    upset = ' <<UPSET>>' if m.get('is_upset') else ''
    hg    = m['home_goals']
    ag    = m['away_goals']
    print(f"  M{m['match_id']:>3}: {m['home_team']:>25s} {hg}-{ag} {m['away_team']:<25s} [{stage}]{extra}{pens}{upset}")

print()
print('=== Final Standings ===')
print(f"Champion  : {state.get('champion')}")
print(f"Runner-up : {state.get('runner_up')}")
print(f"Third     : {state.get('third_place')}")
print(f"Fourth    : {state.get('fourth_place')}")
