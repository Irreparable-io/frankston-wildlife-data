import pandas as pd
import simplekml
import json
import os
import random
import requests
import time
from datetime import datetime
import gspread
import pickle
import numpy as np
import math

# ==========================================
# --- CONFIGURATION ---
# ==========================================
SHEET_KEY = "1yx3Jq6JQmpLkL737nwahTfOMAHjy52rZ1LULIyXRZRY"
OUTPUT_DIR = "H:/My Drive/Squarespace Stats Utilities"
INAT_USERNAME = "irreparable" 
MAX_TARGETS_PER_ZONE = 4

# OFFICIAL RESERVES (Must match Website CSS)
RESERVES = {
    "The Pines Flora and Fauna Reserve": (-38.135, -38.115, 145.161, 145.189),
    "Frankston Nature Conservation Reserve": (-38.184, -38.166, 145.124, 145.136),
    "Kananook Creek": (-38.141, -38.081, 145.120, 145.128),
    "Langwarrin Flora and Fauna Reserve": (-38.179, -38.166, 145.165, 145.188)
}

ICON_TARGET = "http://maps.google.com/mapfiles/kml/paddle/red-stars.png"

GHOST_SPECIES = [
    "glossy black cockatoo", "southern brown bandicoot", 
    "swift parrot", "orange bellied parrot", "regent honeyeater"
]

# ==========================================
# --- HELPER FUNCTIONS ---
# ==========================================

def normalize_zone_name(zone_raw):
    z = str(zone_raw).lower().strip()
    if "pines" in z: return "The Pines Flora and Fauna Reserve"
    if "frankston" in z: return "Frankston Nature Conservation Reserve"
    if "kananook" in z: return "Kananook Creek"
    if "langwarrin" in z: return "Langwarrin Flora and Fauna Reserve"
    return "Unknown"

def obfuscate_location(lat, lon, status):
    if status.lower() == "least concern":
        jitter = 0.0001
        return lat + random.uniform(-jitter, jitter), lon + random.uniform(-jitter, jitter)
    offset = 0.0045 # Tier 2 Fuzzing
    return lat + random.uniform(-offset, offset), lon + random.uniform(-offset, offset)

def fetch_inat_hunt_targets():
    # ... (Standard API Logic) ...
    return []

def calculate_vpd(temp_c, humidity_perc):
    """Calculates Vapor Pressure Deficit (VPD) in kPa."""
    try:
        # Saturation Vapor Pressure (SVP)
        svp = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
        # Actual Vapor Pressure (AVP)
        avp = svp * (humidity_perc / 100.0)
        # VPD
        return round(svp - avp, 3)
    except Exception:
        return None

# ==========================================
# --- MAIN RADAR SYSTEM ---
# ==========================================

def run_radar_system():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    print("\n📡 INITIALIZING DUNKLEY BIODIVERSITY RADAR (V4.5 - DAILY AGGREGATION)...")
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token: creds = pickle.load(token)
    else: print("❌ Error: 'token.pickle' not found."); return

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_KEY).get_worksheet(0)
    df = pd.DataFrame(sheet.get_all_records())

    # --- 1. COLUMN MAPPING (Do this FIRST so Pandas knows the names) ---
    cols = {k.lower(): k for k in df.columns}
    name_col = cols.get('common name', cols.get('species', 'Common Name'))
    dist_col = next((c for c in df.columns if 'distance' in c.lower()), 'Distance')
    dur_col = next((c for c in df.columns if 'duration' in c.lower()), 'Duration')
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Date/Time')
    zone_col = next((c for c in df.columns if 'zone' in c.lower()), 'Zone')
    notes_col = next((c for c in df.columns if 'note' in c.lower()), 'Notes')
    media_col = next((c for c in df.columns if 'media' in c.lower()), 'Media Type')

    df.rename(columns={
        name_col: 'Common Name', 
        dist_col: 'Distance', 
        dur_col: 'Duration', 
        date_col: 'Date/Time', 
        zone_col: 'Zone',
        notes_col: 'Notes',
        media_col: 'Media Type'
    }, inplace=True)

    # --- 2. PURGE UNVERIFIED RECORDS BEFORE DOING ANY MATH ---
    df = df[~df['Notes'].astype(str).str.upper().str.contains(r'\[CONTENDED\]')]

    # --- 2.5 PROJECT SCOPE FILTER (Remove Out-of-Scope Taxa) ---
    print("   📊 Removing out-of-scope taxonomy (Insects, Fish, etc.)...")
    if 'Taxonomy' in df.columns:
        tax_blacklist = ["insect", "spider", "fish", "aquatic", "invertebrate", "crustacean"]
        df = df[~df['Taxonomy'].astype(str).str.lower().str.contains('|'.join(tax_blacklist))]

    # --- 3. DAILY AGGREGATION ---
    df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce').fillna(0)
    df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce').fillna(0)
    df['DateOnly'] = pd.to_datetime(df['Date/Time'], format="%d/%m/%Y %H:%M", errors='coerce').dt.date
    daily_stats = df.groupby('DateOnly')[['Distance', 'Duration']].max()

    total_km = float(daily_stats['Distance'].sum())
    total_hours = float(round(daily_stats['Duration'].sum() / 60, 1))
    
    print(f"   📊 MATH CHECK: {total_hours} Hours across {len(daily_stats)} unique field days.")

    # =========================================================
    # 🚨 VPD SCATTER PLOT ENGINE & JSON EXPORT
    # =========================================================
    print("   📊 Calculating Vapor Pressure Deficit (VPD)...")
    
    # 1. Ensure columns are numeric
    df['Temp. (°C)'] = pd.to_numeric(df['Temp. (°C)'], errors='coerce')
    df['Humidity (%)'] = pd.to_numeric(df['Humidity (%)'], errors='coerce')

    # 2. Apply VPD math row by row
    df['VPD_kPa'] = df.apply(
        lambda row: calculate_vpd(row['Temp. (°C)'], row['Humidity (%)']) 
        if pd.notnull(row['Temp. (°C)']) and pd.notnull(row['Humidity (%)']) 
        else None, 
        axis=1
    )

    # 3. Filter missing data
    vpd_df = df.dropna(subset=['VPD_kPa', 'Zone'])
    
    # 4. Extract only what the scatter plot needs (Includes Taxonomy)
    # Use .get() to avoid crashing if 'Taxonomy' happens to be blank
    vpd_export = vpd_df[['Date/Time', 'Zone', 'Common Name', 'VPD_kPa']].copy()
    vpd_export['Taxonomy'] = vpd_df.get('Taxonomy', 'Unknown')
    
    vpd_export_data = vpd_export.to_dict(orient='records')
    
    # 5. ATOMIC EXPORT: Write temp file, then replace (Prevents web sync errors)
    vpd_path = os.path.join(OUTPUT_DIR, 'vpd_scatter_data.json')
    with open(vpd_path + ".tmp", 'w') as f:
        json.dump(vpd_export_data, f, separators=(',', ':'))
    os.replace(vpd_path + ".tmp", vpd_path)
    
    print(f"   ✅ Generated {len(vpd_export_data)} VPD records for the dashboard.")
    # =========================================================

    # --- 3. ZONE STATS & MAP PROCESSING (COMPRESSED) ---
    zone_stats = {z: {"total_obs": 0, "species": set(), "tax_split": {"Birds":0, "Amphibians":0, "Reptiles":0, "Mammals":0, "Insects":0}} for z in RESERVES.keys()}
    
    # LEGENDS for compression
    species_legend = []
    zone_legend = []
    status_legend = []
    media_legend = []

    def get_id(val, legend_list):
        if val not in legend_list: legend_list.append(val)
        return legend_list.index(val)

    compressed_obs = []     # For the map markers
    optimized_heatmap = []  # For the heatmap layer

    for _, row in df.iterrows():
        # --- INTEGRITY BYPASS ---
        row_notes = str(row.get('Notes', '')).upper()
        if "[CONTENDED]" in row_notes:
            continue
        # ------------------------

        # Clean Inputs
        species_name = str(row.get('Common Name', 'Unknown')).strip()
        raw_zone = str(row.get('Zone', ''))
        clean_zone = normalize_zone_name(raw_zone)
        status = str(row.get('Conservation Status', 'Least Concern')).strip()
        st_lower = status.lower()
        media_val = str(row.get('Media Type', 'Unknown')).strip()
        
        # --- NEW STATUS LOGIC ---
        is_ghost = any(g in species_name.lower() for g in GHOST_SPECIES)
        is_pest = st_lower in ["introduced", "invasive", "pest", "feral"]
        
        # True Threatened: Not Least Concern, Not Unknown, AND Not a Pest
        is_threatened = (st_lower != "least concern" and st_lower != "unknown" and not is_pest) or is_ghost

        # A. UPDATE ZONE CARDS (Standard Logic)
        if clean_zone != "Unknown" and not is_threatened:
            zone_stats[clean_zone]["total_obs"] += 1
            zone_stats[clean_zone]["species"].add(species_name)
            
            tax = str(row.get('Taxonomy', 'Fauna')).lower()
            if "bird" in tax: zone_stats[clean_zone]["tax_split"]["Birds"] += 1
            elif "frog" in tax: zone_stats[clean_zone]["tax_split"]["Amphibians"] += 1
            elif "reptile" in tax: zone_stats[clean_zone]["tax_split"]["Reptiles"] += 1
            elif "mammal" in tax: zone_stats[clean_zone]["tax_split"]["Mammals"] += 1
            else: zone_stats[clean_zone]["tax_split"]["Insects"] += 1

        # B. BUILD COMPRESSED LISTS
        if clean_zone != "Unknown":
            try:
                lat = float(row.get('Latitude', 0))
                lon = float(row.get('Longitude', 0))
                
                if lat == 0 or lon == 0 or pd.isna(lat): continue 
                               
                if is_threatened:
                    clean_zone = "Obscured"
                    # Lock coordinates to generic Frankston center
                    s_lat, s_lon = -38.1400, 145.1500 
                else:
                    # Pests and Least Concern species will pass through here normally
                    s_lat, s_lon = obfuscate_location(lat, lon, status)
                    s_lat = round(s_lat, 5)
                    s_lon = round(s_lon, 5)
                # ---------------------------------

                # 2. Get IDs
                sp_id = get_id(species_name, species_legend)
                zn_id = get_id(clean_zone, zone_legend)
                st_id = get_id(status, status_legend)
                md_id = get_id(media_val, media_legend)

                # 3. Minified Date (DD/MM/YY)
                raw_date = str(row.get('Date/Time', ''))
                try:
                    mini_date = datetime.strptime(raw_date, "%d/%m/%Y %H:%M").strftime("%d/%m/%y")
                except: mini_date = ""

                # 4. COMPRESSED ROW
                compressed_obs.append([s_lat, s_lon, sp_id, zn_id, st_id, mini_date, md_id])
                
                # 5. HEATMAP (EXCLUDE THREATENED)
                if not is_threatened:
                    optimized_heatmap.append([s_lat, s_lon, 0.5])
            except: continue

    # --- 3.5. DYNAMIC SEASONAL SPUE ENGINE ---
    print("   📊 Calculating Dynamic Seasonal SPUE...")
    
    # 1. Parse timestamps and extract components
    df['dt_obj'] = pd.to_datetime(df['Date/Time'], dayfirst=True, errors='coerce')
    df['Month'] = df['dt_obj'].dt.month
    df['Hour'] = df['dt_obj'].dt.hour
    df['DateOnly'] = df['dt_obj'].dt.date

    # 2. Map Months to Seasons
    def get_season(month):
        if pd.isna(month): return "Unknown"
        if month in [12, 1, 2]: return "Summer"
        if month in [3, 4, 5]: return "Autumn"
        if month in [6, 7, 8]: return "Winter"
        if month in [9, 10, 11]: return "Spring"
        return "Unknown"

    df['Season'] = df['Month'].apply(get_season)

    # 3. Setup the blank dictionary structure (None = Un-surveyed)
    seasons_list = ["All Year", "Summer", "Autumn", "Winter", "Spring"]
    core_reserves = [
        "The Pines Flora and Fauna Reserve", 
        "Langwarrin Flora and Fauna Reserve", 
        "Kananook Creek", 
        "Frankston Nature Conservation Reserve"
    ]
    
    # Initialize everything with None (translates to null in JSON)
    temporal_rates = {s: {z: [None] * 24 for z in core_reserves} for s in seasons_list}

    # 4. Calculate Effort-Corrected Rates
    for z in core_reserves:
        zone_df = df[df['Zone'] == z]
        if zone_df.empty: continue
        
        for h in range(24):
            # Get all observations for this specific hour in this zone
            hr_all_df = zone_df[zone_df['Hour'] == h]
            
            if not hr_all_df.empty:
                # Effort Correction: Divide total sightings by number of unique days surveyed at this hour
                days_all = hr_all_df['DateOnly'].nunique()
                temporal_rates["All Year"][z][h] = round(len(hr_all_df) / days_all, 2)
                
            # Break it down further by Season
            for s in ["Summer", "Autumn", "Winter", "Spring"]:
                hr_season_df = hr_all_df[hr_all_df['Season'] == s]
                if not hr_season_df.empty:
                    days_season = hr_season_df['DateOnly'].nunique()
                    temporal_rates[s][z][h] = round(len(hr_season_df) / days_season, 2)     

    # Package clean zones and other metadata...
    clean_zones = {}
    for k, v in zone_stats.items():
        clean_zones[k] = {
            "total_obs": int(v["total_obs"]),
            "species": int(len(v["species"])),
            "taxonomy_split": v["tax_split"]
        }
        
    # ==========================================
    # --- LIBRARY PRE-CALCULATION ENGINE ---
    # ==========================================
    print("   📊 Pre-calculating Library stats...")
    library_payload = {}
    
    # 0. Clean up headers
    df.columns = df.columns.str.strip()
    
    # 1. HARD-LOCKED COLUMNS
    species_col = 'Common Name'
    date_col = 'Date/Time'
    media_col = 'Media Type'
    status_col = 'Conservation Status'
    tax_col = 'Taxonomy'
    zone_col = 'Zone'

    # 2. Parse the exact Date format
    df['DateObj'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')

    # 3. Group the spreadsheet by the matched column
    for species, group in df.groupby(species_col):
        clean_species_name = str(species).strip()
        
        # --- EXCLUSION ENGINE ---
        matrix_blacklist = ["Common Froglet", "Human", "Dog", "Short-finned Eel"]
        if clean_species_name in matrix_blacklist:
            continue 
            
        try:
            if tax_col in group.columns:
                valid_tax = group[tax_col].replace(["", "nan", "NaN", "None"], pd.NA).dropna()
                if len(valid_tax) > 0:
                    raw_tax = str(valid_tax.to_list()).strip().lower()
                    allowed_taxa = ["bird", "mammal", "reptile", "amphibian"]
                    if not any(allowed in raw_tax for allowed in allowed_taxa):
                        continue
        except Exception:
            pass 
            
        # A. Total Encounters
        encounters = int(len(group))
        
        # B. Latest Date
        latest_date = group['DateObj'].max()
        latest_str = "Unknown" if pd.isna(latest_date) else latest_date.strftime('%d/%m/%y')
            
        # C. Detection Profile
        media_counts = group[media_col].astype(str).str.lower().value_counts()
        audio_c, visual_c = 0, 0
        
        for media_val, count in media_counts.items():
            if 'audio' in media_val and 'visual' in media_val or 'both' in media_val:
                audio_c += count; visual_c += count
            elif 'audio' in media_val:
                audio_c += count
            else:
                visual_c += count
                
        total_av = audio_c + visual_c
        if total_av > 0:
            a_pct = (audio_c / total_av) * 100
            if a_pct >= 75: detection = "Audio"
            elif a_pct <= 25: detection = "Visual"
            else: detection = "Mixed"
        else:
            detection = "Unknown"

        # D. Security Check
        try:
            if status_col in group.columns:
                valid_status = group[status_col].replace(["", "nan", "NaN", "None"], pd.NA).dropna()
                raw_status = str(valid_status.to_list()).strip().lower() if len(valid_status) > 0 else "unknown"
            else:
                raw_status = "unknown"
        except:
            raw_status = "unknown"

        threat_keywords = ["vulnerable", "endangered", "critically", "threatened", "near threatened", "rare", "extinct"]
        is_safe = not any(keyword in raw_status for keyword in threat_keywords)
        
        if "glossy black-cockatoo" in str(species).lower() or "powerful owl" in str(species).lower():
            is_safe = False

        # E. Primary Hotspot
        if not is_safe:
            hotspot = "Hidden" 
        else:
            try:
                if zone_col in group.columns:
                    valid_zones = group[zone_col].replace(["", "nan", "NaN"], pd.NA).dropna()
                    if len(valid_zones) > 0:
                        raw_hotspot = str(valid_zones.mode().to_list())
                        clean_hs = raw_hotspot.replace('[', '').replace(']', '').replace("'", "").replace('"', '').strip()
                        
                        if "Frankston Nature" in clean_hs or "Frankston NCR" in clean_hs: hotspot = "Frankston NCR"
                        elif "Langwarrin" in clean_hs: hotspot = "Langwarrin FFR"
                        elif "Pines" in clean_hs: hotspot = "The Pines"
                        elif "Kananook" in clean_hs: hotspot = "Kananook Creek"
                        else:
                            words = clean_hs.split()
                            hotspot = " ".join(words[:2]) if len(words) > 2 else clean_hs
                    else: hotspot = "Unknown"
                else: hotspot = "Unknown"
            except: hotspot = "Unknown"

        # F. Taxonomy
        try:
            if tax_col in group.columns:
                valid_tax = group[tax_col].replace(["", "nan", "NaN", "None"], pd.NA).dropna()
                if len(valid_tax) > 0:
                    taxonomy = str(valid_tax.to_list()).strip().title()
                    if taxonomy.lower() == "nan": taxonomy = "Unknown"
                else: taxonomy = "Unknown"
            else: taxonomy = "Unknown"
        except: taxonomy = "Unknown"

        # Save to the dictionary
        library_payload[clean_species_name] = {
            "count": encounters,
            "latest_date": latest_str,
            "detection": detection, 
            "hotspot": hotspot,
            "taxonomy": taxonomy
        }

    # Write the new Library JSON
    library_path = os.path.join(OUTPUT_DIR, "library_stats.json")
    with open(library_path + ".tmp", 'w') as f:
        json.dump(library_payload, f, separators=(',', ':'))
    os.replace(library_path + ".tmp", library_path)
    print("   ✅ library_stats.json generated successfully!")

    # ==========================================
    # --- FINAL PAYLOAD SPLIT (3-TIER ARCHITECTURE) ---
    # ==========================================
    print("   📦 Splitting and writing final payloads...")

    # --- THE PERFECT MATCH ALGORITHM ---
    js_omit_list = ['bee', 'wasp', 'ant', 'butterfly', 'moth', 'spider', 'insect', 'fish', 'eel', 'gambusia', 'dragonfly', 'crustacean', 'invertebrate']
    js_threat_blacklist = ["least concern", "introduced", "invasive", "pest", "feral", "unknown"]
    
    strict_species_set = set()
    strict_threatened_set = set()
    strict_obs_count = 0
    
    valid_zones = [
        "The Pines Flora and Fauna Reserve", 
        "Langwarrin Flora and Fauna Reserve", 
        "Kananook Creek", 
        "Frankston Nature Conservation Reserve",
        "Obscured"
    ]

    # Tracker for the Zone Badges
    zone_species_sets = {z: set() for z in valid_zones if z != "Obscured"}
    
    for row in compressed_obs:
        if len(row) < 5: continue
        
        # Safe extraction
        sp_idx = row.__getitem__(2)
        zn_idx = row.__getitem__(3)
        st_idx = row.__getitem__(4)
        
        sp_name = species_legend.__getitem__(sp_idx)
        zn_name = zone_legend.__getitem__(zn_idx)
        st_name = status_legend.__getitem__(st_idx)
        
        # 1. Javascript Exclusion Rule
        if any(omit in str(sp_name).lower() for omit in js_omit_list):
            continue
            
        # 2. Zone Exclusion Rule
        if zn_name not in valid_zones:
            continue
            
        # 3. Add to Final Counts
        if zn_name != "Unknown":
            strict_obs_count += 1
            strict_species_set.add(sp_name)
            
            if not any(b in str(st_name).lower() for b in js_threat_blacklist):
                strict_threatened_set.add(sp_name)

            # 4. Add to Zone Badges (tracks unique species per zone)
            if zn_name in zone_species_sets:
                zone_species_sets[zn_name].add(sp_name)

    # Calculate final zone badges directly from the tracker
    final_zone_badges = {z: len(sp_set) for z, sp_set in zone_species_sets.items()}

    # 1. LANDING PAGE DATA (Summary Stats + Heatmap + Zone Badges)
    landing_payload = {
        "meta": {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")},
        "summary": {
            "total_observations": strict_obs_count, 
            "total_species": len(strict_species_set), 
            "total_km": total_km, 
            "total_hours": total_hours,
            "threatened_count": len(strict_threatened_set)
        },
        "zone_badges": final_zone_badges,
        "heatmap_data": optimized_heatmap 
    }

    # 2. DASHBOARD DATA (Charts, Zones, VPD, Feed)
    dashboard_payload = {
        "meta": {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")},
        "summary": landing_payload["summary"], # Keep a copy here so the header numbers still work
        "legends": {
            "species": species_legend,
            "zones": zone_legend,
            "status": status_legend,
            "media": media_legend
        },
        "zones": clean_zones,
        "temporal_rates": temporal_rates,
        "vpd_data": vpd_export_data,  
        "data": compressed_obs 
    }

    import shutil

    # Helper function for Atomic Writes
    def atomic_write(payload_data, filename):
        final_path = os.path.join(OUTPUT_DIR, filename)
        temp_path = final_path + ".tmp"
        try:
            with open(temp_path, 'w') as f:
                json.dump(payload_data, f, separators=(',', ':'))
            shutil.move(temp_path, final_path)
            print(f"   ✅ {filename} Written Successfully.")
        except Exception as e:
            print(f"   ❌ Error writing {filename}: {e}")

    # Write the two master files!
    atomic_write(landing_payload, "landing_data.json")
    atomic_write(dashboard_payload, "dashboard_data.json")