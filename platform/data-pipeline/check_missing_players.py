import os
import re
import unicodedata
import pandas as pd
import uuid

# Helper to normalize names
def clean_name(name):
    if not isinstance(name, str):
        return ""
    # Normalize accents
    name_clean = "".join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    # Lowercase, replace non-alphanumeric/spaces with space, then join single spaces
    name_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', name_clean)
    name_clean = " ".join(name_clean.lower().strip().split())
    return name_clean

# Helper for substring matching that works in order of words
def matches_fuzzy(name1, name2):
    n1 = clean_name(name1)
    n2 = clean_name(name2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    
    words1 = n1.split()
    words2 = n2.split()
    
    # Exact word match for shorter word combinations (e.g. Heung-min Son vs Son Heung-min)
    # Check if the set of words is identical
    if set(words1) == set(words2):
        return True
        
    # Also handle standard full containment of significant words
    # A match is valid if one is a sub-phrase of another (e.g., "mousa tamari" and "mousa al tamari")
    # For this to be safe, the significant tokens must match.
    # Exclude common stopwords or short words
    ignored = {'al', 'el', 'de', 'dos', 'santos', 'da', 'der', 'van', 'di'}
    sig1 = [w for w in words1 if w not in ignored and len(w) >= 3]
    sig2 = [w for w in words2 if w not in ignored and len(w) >= 3]
    
    if not sig1 or not sig2:
        return False
        
    # If all significant words of one name are in the other name, match it
    if len(sig1) < len(sig2):
        shorter, longer = sig1, sig2
    else:
        shorter, longer = sig2, sig1
        
    if all(w in longer for w in shorter):
        # Additional protection: prevent matching "Lionel Messi" to "Lionel Mpasi" 
        # because "Lionel" is in both, but "messi" is not in "mpasi". 
        # Shorter must be at least 2 significant words, or if it is 1 word, it must be the ONLY significant word.
        if len(shorter) >= 2:
            return True
        elif len(shorter) == 1 and len(longer) == 1:
            return True
            
    return False

# Read missing players
with open('c:/FIFA WC/platform/data/processed/missing_players.txt', 'r', encoding='utf-8') as f:
    missing_players_raw = [p.strip() for p in f.read().split(',') if p.strip()]

print(f"Total Missing Players Loaded: {len(missing_players_raw)}")

# Load datasets
players_data_df = pd.read_csv('c:/FIFA WC/DATA/latest/players_data-2025_2026.csv')
players_df = pd.read_csv('c:/FIFA WC/DATA/transfer market/players.csv')
valuations_df = pd.read_csv('c:/FIFA WC/DATA/transfer market/player_valuations.csv')

# Prep match keys
players_data_df['clean_name'] = players_data_df['Player'].apply(clean_name)
players_df['clean_name'] = players_df['name'].apply(clean_name)

# Create lookup dicts
players_data_lookup = {}
for idx, row in players_data_df.iterrows():
    c_name = row['clean_name']
    if c_name and c_name not in players_data_lookup:
        players_data_lookup[c_name] = row

players_lookup = {}
for idx, row in players_df.iterrows():
    c_name = row['clean_name']
    if c_name and c_name not in players_lookup:
        players_lookup[c_name] = row

# Valuations prep: get latest valuation per player_id
valuations_df['player_id'] = valuations_df['player_id'].astype(str)
valuations_df['date'] = pd.to_datetime(valuations_df['date'], errors='coerce')
latest_valuations = (
    valuations_df.sort_values('date')
    .groupby('player_id', as_index=False)
    .last()
)
valuations_lookup = {row['player_id']: row for idx, row in latest_valuations.iterrows()}

# Perform recovery
recovered_from_stats = []
recovered_from_players = []
still_missing = []

# To trace recovery status for recovery_report.csv
recovery_report_rows = []

for p_name in missing_players_raw:
    clean_p = clean_name(p_name)
    
    # Try match against players_data-2025_2026.csv
    match_row = None
    if clean_p in players_data_lookup:
        match_row = players_data_lookup[clean_p]
    else:
        # Fuzzy check
        for c_name, row in players_data_lookup.items():
            if matches_fuzzy(clean_p, c_name):
                match_row = row
                break
    
    if match_row is not None:
        recovered_from_stats.append((p_name, match_row))
        recovery_report_rows.append({
            'original_name': p_name,
            'status': 'Recovered from stats dataset',
            'matched_name': match_row['Player'],
            'source_dataset': 'players_data-2025_2026.csv',
            'player_id': ''
        })
        continue
        
    # Try match against players.csv
    match_player_row = None
    if clean_p in players_lookup:
        match_player_row = players_lookup[clean_p]
    else:
        for c_name, row in players_lookup.items():
            if matches_fuzzy(clean_p, c_name):
                match_player_row = row
                break
                    
    if match_player_row is not None:
        p_id = str(match_player_row['player_id'])
        has_val = p_id in valuations_lookup
        recovered_from_players.append((p_name, match_player_row, has_val))
        recovery_report_rows.append({
            'original_name': p_name,
            'status': 'Recovered from players.csv',
            'matched_name': match_player_row['name'],
            'source_dataset': 'players.csv',
            'player_id': p_id
        })
    else:
        still_missing.append(p_name)
        recovery_report_rows.append({
            'original_name': p_name,
            'status': 'Still missing',
            'matched_name': '',
            'source_dataset': '',
            'player_id': ''
        })

# Phase 4 counts
recovered_val_count = sum(1 for item in recovered_from_players if item[2])
missing_val_count = len(recovered_from_players) - recovered_val_count

# Save Phase reports
pd.DataFrame(recovery_report_rows).to_csv('c:/FIFA WC/platform/data/processed/recovery_report.csv', index=False)
pd.DataFrame({'name': still_missing}).to_csv('c:/FIFA WC/platform/data/processed/missing_after_all_matches.csv', index=False)

# Phase 5 Summary
print("--- Recovery Summary ---")
print(f"Total Missing: {len(missing_players_raw)}")
print(f"Recovered from stats: {len(recovered_from_stats)}")
print(f"Recovered from players.csv: {len(recovered_from_players)}")
print(f"Recovered valuations: {recovered_val_count}")
print(f"Still Missing: {len(still_missing)}")

# Phase 6: Generate Enriched Auction Pool
orig_auction_df = pd.read_csv('c:/FIFA WC/platform/data/processed/auction_players.csv')
print(f"Original Pool Size: {len(orig_auction_df)}")

# Keep track of existing names to avoid duplicates
existing_names = set(orig_auction_df['name'].apply(clean_name))
new_players_rows = []

# Mapping flags logic
from build_auction_players import FLAG_MAP, normalize_pos, assign_tier, ensure_uuid

# Helper to look up players.csv row details for stats matched players
def get_player_fields(clean_n):
    if clean_n in players_lookup:
        row = players_lookup[clean_n]
        return row
    return None

for p_name, row in recovered_from_stats:
    c_name = clean_name(row['Player'])
    if c_name in existing_names:
        continue
    
    iso = str(row['Nation']).split()[-1].upper() if pd.notna(row['Nation']) else ""
    flag = FLAG_MAP.get(iso, "un")
    pos = normalize_pos(row['Pos'])
    
    p_fields = get_player_fields(c_name)
    p_id = str(p_fields['player_id']) if p_fields is not None else str(uuid.uuid4())
    nat = p_fields['country_of_citizenship'] if p_fields is not None else ""
    sub_pos = p_fields['sub_position'] if p_fields is not None else ""
    img = p_fields['image_url'] if p_fields is not None else ""
    caps = p_fields['international_caps'] if p_fields is not None else 0
    
    latest_val = valuations_lookup.get(p_id)['market_value_in_eur'] if p_id in valuations_lookup else pd.NA
    if pd.isna(latest_val):
        latest_val = 0.0
        
    tier, base_price = assign_tier(latest_val)
    
    goals_per_90 = round(float(row.get('Gls', 0)) / float(row.get('90s', 1)) if float(row.get('90s', 0)) > 0 else 0.0, 2)
    assists_per_90 = round(float(row.get('Ast', 0)) / float(row.get('90s', 1)) if float(row.get('90s', 0)) > 0 else 0.0, 2)
    ga_per_90 = round(float(row.get('G+A', 0)) / float(row.get('90s', 1)) if float(row.get('90s', 0)) > 0 else 0.0, 2)
    
    form_score = round(
        goals_per_90 * 40 + assists_per_90 * 25 + 
        (float(row.get('Min', 0)) / 3060) * 20 + 
        (float(row.get('MP', 0)) / 38) * 15,
        2
    )
    form_score = min(max(form_score, 0.0), 100.0)
    
    new_players_rows.append({
        'id': p_id,
        'name': row['Player'],
        'nationality': nat,
        'iso_code': iso,
        'flag_code': flag,
        'position': pos,
        'sub_position': sub_pos,
        'club': row['Squad'],
        'league': row['Comp'],
        'age': row['Age'],
        'market_value': latest_val,
        'base_price': base_price,
        'tier': tier,
        'form_score': form_score,
        'goals_2526': int(row.get('Gls', 0)),
        'assists_2526': int(row.get('Ast', 0)),
        'minutes_2526': int(row.get('Min', 0)),
        'matches_2526': int(row.get('MP', 0)),
        'goals_per_90': goals_per_90,
        'assists_per_90': assists_per_90,
        'ga_per_90': ga_per_90,
        'yellow_cards': int(row.get('CrdY', 0)),
        'red_cards': int(row.get('CrdR', 0)),
        'image_url': img,
        'international_caps': int(caps) if pd.notna(caps) else 0,
        'val_date': valuations_lookup.get(p_id)['date'].strftime('%Y-%m-%d') if p_id in valuations_lookup else "",
        'created_at': pd.Timestamp.utcnow()
    })
    existing_names.add(c_name)

# Case 2: Only found in players.csv
for p_name, row, has_val in recovered_from_players:
    c_name = clean_name(row['name'])
    if c_name in existing_names:
        continue
        
    p_id = str(row['player_id'])
    latest_val = valuations_lookup.get(p_id)['market_value_in_eur'] if p_id in valuations_lookup else 0.0
    tier, base_price = assign_tier(latest_val)
    
    raw_pos = row.get('position', 'Midfield')
    pos_map = {'Goalkeeper': 'GK', 'Defender': 'DEF', 'Midfield': 'MID', 'Attack': 'FWD'}
    pos = pos_map.get(raw_pos, 'MID')
    
    if latest_val >= 20000000:
        form_score = 85.0 + min((latest_val - 20000000) / 80000000 * 7.0, 7.0)
    elif latest_val >= 1000000:
        form_score = 75.0 + (latest_val - 1000000) / 19000000 * 9.0
    else:
        form_score = 60.0 + (latest_val / 1000000) * 14.0
    form_score = round(form_score, 2)
    
    if 'age' in row and pd.notna(row['age']):
        age = row['age']
    elif pd.notna(row.get('date_of_birth')):
        try:
            birth_year = pd.to_datetime(row['date_of_birth']).year
            age = 2026 - birth_year
        except Exception:
            age = 25
    else:
        age = 25
        
    nat = row['country_of_citizenship']
    iso = ""
    flag = "un"
    
    new_players_rows.append({
        'id': p_id,
        'name': row['name'],
        'nationality': nat,
        'iso_code': iso,
        'flag_code': flag,
        'position': pos,
        'sub_position': row.get('sub_position', ''),
        'club': row.get('current_club_name', ''),
        'league': '',
        'age': age,
        'market_value': latest_val,
        'base_price': base_price,
        'tier': tier,
        'form_score': form_score,
        'goals_2526': 0,
        'assists_2526': 0,
        'minutes_2526': 0,
        'matches_2526': 0,
        'goals_per_90': 0.0,
        'assists_per_90': 0.0,
        'ga_per_90': 0.0,
        'yellow_cards': 0,
        'red_cards': 0,
        'image_url': row.get('image_url', ''),
        'international_caps': 0,
        'val_date': valuations_lookup.get(p_id)['date'].strftime('%Y-%m-%d') if p_id in valuations_lookup else "",
        'created_at': pd.Timestamp.utcnow()
    })
    existing_names.add(c_name)

# Combine and save enriched dataset
new_players_df = pd.DataFrame(new_players_rows)
enriched_df = pd.concat([orig_auction_df, new_players_df], ignore_index=True)
enriched_df.to_csv('c:/FIFA WC/platform/data/processed/auction_players_recovered.csv', index=False)

print(f"Added {len(new_players_df)} players.")
print(f"Enriched Pool Size: {len(enriched_df)}")

# Validation printouts
print("\n--- Validation: Check key players ---")
key_players = [
    'Lionel Messi', 'Cristiano Ronaldo', 'Neymar', 'Riyad Mahrez', 
    'Akram Afif', 'Son Heung-min', 'Dominik Livakovic', 'Mousa Al-Tamari', 'Sadio Mane'
]
for kp in key_players:
    clean_kp = clean_name(kp)
    match = enriched_df[enriched_df['name'].apply(clean_name) == clean_kp]
    if not match.empty:
        print(f"SUCCESS: {kp} is in the pool! (Club: {match.iloc[0]['club']}, Value: {match.iloc[0]['market_value']})")
    else:
        matched_row = None
        for idx, row in enriched_df.iterrows():
            if matches_fuzzy(kp, row['name']):
                matched_row = row
                break
        if matched_row is not None:
             print(f"SUCCESS (Fuzzy matched): {kp} found as {matched_row['name']} (Club: {matched_row['club']}, Value: {matched_row['market_value']})")
        else:
             print(f"FAILED: {kp} not found in pool.")
