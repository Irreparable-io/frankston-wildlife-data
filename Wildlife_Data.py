import difflib
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
import shutil
import glob
import io
import re

# ==========================================
# --- CONFIGURATION ---
# ==========================================

BASE_DIR = "."
VBA_DIR = os.path.join(BASE_DIR, "VBA_Raw_Data")
SHEET_KEY = "1yx3Jq6JQmpLkL737nwahTfOMAHjy52rZ1LULIyXRZRY"
OUTPUT_DIR = "."
INAT_USERNAME = "irreparable" 
MAX_TARGETS_PER_ZONE = 4

# --- MASTER TAXONOMY MAP ---
SPECIES_MAP = {
    "gray fantail": "Grey Fantail",
    "gray shrikethrush": "Grey Shrikethrush",
    "gray butcherbird": "Grey Butcherbird",
    "gray teal": "Grey Teal",
    "peewee": "Magpie-lark",
    "magpie lark": "Magpie-lark",
    "willie wagtail": "Willie Wagtail",
    "willie-wagtail": "Willie Wagtail",
    "rainbow lorikeet": "Eastern Rainbow Lorikeet",
    "echidna": "Eastern Short-beaked Echidna",
    "magpie": "Australian Magpie",
    "tasmanian scrubwren": "White-browed Scrubwren",
    "kookaburra": "Laughing Kookaburra",
    "red browed firetail": "Red-browed Finch",
    "gbc": "Glossy Black-Cockatoo",
    "glossy black cockatoo": "Glossy Black-Cockatoo",
    "yellow tailed black cockatoo": "Yellow-tailed Black-Cockatoo",
    "black shouldered kite": "Black-shouldered Kite",
    "australian swamp rat": "Swamp Rat",
    "australian ibis": "Australian White Ibis",
    "australian rufous fantail": "Rufous Fantail",
    "pale-flecked garden sunskink": "Garden Skink",
    "grey shrike thrush": "Grey Shrikethrush",
    "superb fairy wren": "Superb Fairywren",
    "yellow rumped thornbill": "Yellow-rumped Thornbill",
    "white browed scrubwren": "White-browed Scrubwren",
    "white striped free tailed bat": "White-striped Free-tailed Bat",
    "southern free tailed bat": "South-eastern Free-tailed Bat",
    "eastern shrike tit": "Eastern Shriketit", 
    "white winged triller": "White-winged Triller",
    "white throated treecreeper": "White-throated Treecreeper",
    "white naped honeyeater": "White-naped Honeyeater",
    "brown headed honeyeater": "Brown-headed Honeyeater",
    "yellow faced honeyeater": "Yellow-faced Honeyeater",
    "white eared honeyeater": "White-eared Honeyeater",
    "white plumed honeyeater": "White-plumed Honeyeater",
    "red browed finch": "Red-browed Finch",
    "eastern snake necked turtle": "Eastern Snake-necked Turtle",
    "eastern three lined skink": "Eastern Three-lined Skink",
    "lesser long eared bat": "Lesser Long-eared Bat",
    "short beaked echidna": "Eastern Short-beaked Echidna",
    "common brush tailed possum": "Common Brushtail Possum",
    "eastern ring tailed possum": "Common Ringtail Possum",
    "black tailed wallaby": "Swamp Wallaby",
    "bare nosed wombat": "Bare-nosed Wombat",
    "straw necked ibis": "Straw-necked Ibis",
    "white faced heron": "White-faced Heron",
    "sulphur crested cockatoo": "Sulphur-crested Cockatoo",
    "blue winged parrot": "Blue-winged Parrot",
    "australian owlet nightjar": "Australian Owlet-nightjar",
    "fan tailed cuckoo": "Fan-tailed Cuckoo",
    "southern brown tree frog southern": "Southern Brown Tree Frog",
    "hoary headed grebe": "Hoary-headed Grebe",
    "blue billed duck": "Blue-billed Duck",
    "scaly breasted lorikeet": "Scaly-breasted Lorikeet",
    "painted button quail": "Painted Buttonquail",
    "white necked heron": "White-necked Heron",
    "gang gang cockatoo": "Gang-gang Cockatoo",
    "white throated needletail": "White-throated Needletail",
    "white fronted chat": "White-fronted Chat",
    "southern emu wren": "Southern Emu-wren",
    "olive backed oriole": "Olive-backed Oriole",
    "black faced cuckooshrike": "Black-faced Cuckooshrike",
    "red bellied black snake": "Red-bellied Black Snake",
    "wedge tailed eagle": "Wedge-tailed Eagle",
    "white winged chough": "White-winged Chough",
    "white throated nightjar": "White-throated Nightjar",
    "pale flecked garden sunskink": "Pale-flecked Garden Sunskink",
    "dark flecked garden sunskink": "Dark-flecked Garden Sunskink",
    "great crested tern": "Greater Crested Tern",
    "red necked avocet": "Red-necked Avocet",
    "short tailed shearwater": "Short-tailed Shearwater",
    "blotched bluetongue": "Blotched Blue-tongued Lizard",
    "common bluetongue": "Common Blue-tongued Lizard",
    "blotched blue tongued lizard": "Blotched Blue-tongued Lizard",
    "common blue tongued lizard": "Common Blue-tongued Lizard",
    "garden skink": "Pale-flecked Garden Sunskink",
    "pobblebonk frog": "Eastern Banjo Frog",
    "blue faced honeyeater": "Blue-faced Honeyeater",
    "grey headed flying fox": "Grey-headed Flying-fox",
    "white lipped snake": "White-lipped Snake",
    "eastern short necked turtle": "Eastern Short-necked Turtle",
    "long billed corella": "Long-billed Corella",
    "tree dragon": "Jacky Dragon",
    "white footed dunnart": "White-footed Dunnart",
    "whites skink": "White's Skink",
    "white s skink": "White's Skink",
    "eurasian blackbird": "Common Blackbird",
    "rock pigeon": "Feral Pigeon",
    "lowlands copperhead": "Lowland Copperhead",
    "buff banded rail": "Buff-banded Rail",
    "eastern small eyed snake": "Eastern Small-eyed Snake",
    "pink eared duck": "Pink-eared Duck",
    "european starling": "Common Starling"
}

EXCLUDE_LIST = [
    "fur seal", "little penguin", "red junglefowl", 
    "undetermined", "dingo", "dog", "domestic", "unidentified", "kangaroo", 
    " and ", "possums", "unknown", "×", " sp.", "birds", "cattle", 
    "pardalotes", "black faced cuckoo shrike", "scarlet myzomela",
    "blue spotted hawker", "ferret", "common froglet", "domestic cat", "hawker",
    "eastern brown snake", "song thrush", "australian pipit", "painted honeyeater",
    "southern emu wren", "weebill", "white fronted chat", "rose robin", "jacky winter"
    "swift parrot" "lathams snipe", "blue winged parrot", "white footed dunnart"
    "eastern pygmy possum", "new holland mouse", "southern brown bandicoot", 
    "eurasian skylark", "lesser long eared bat", "haswell's frog", "haswells frog",
    "south eastern free tailed bat", "hooded robin", "chocolate wattled bat",
    "southern forest bat", "european starling"
    
]

# Force specific conservation statuses (Overrides DEECA and iNat)
STATUS_OVERRIDES = {
    "Glossy Black-Cockatoo": "Critically Endangered",
    "Swamp Wallaby": "Least Concern",
    "Red Fox": "Introduced", 
    "Koala": "Vulnerable",
    "European Rabbit": "Introduced",
    "European Greenfinch": "Introduced",
    "Common Blackbird": "Introduced",
    "Common Myna": "Introduced",
    "European Rabbit": "Introduced",
    "Common Starling": "Introduced",
    "European Goldfinch": "Introduced",
    "House Sparrow": "Introduced",
    "House Mouse": "Introduced",
    "Black Rat": "Introduced",
    "Brown Rat": "Introduced",
    "Feral Pigeon": "Introduced",
    "Freckled Duck": "Vulnerable",
    "Domestic Mallard": "Introduced",
    "Magpie Goose": "Vulnerable",
    "Grey headed Flying fox": "Vulnerable",
    "Australasian Bittern": "Critically Endangered"
}

def normalise_species_name(name):
    safe_name = str(name).replace("-", " ") 
    clean_name = safe_name.strip().lower()
    if clean_name in SPECIES_MAP: 
        return SPECIES_MAP[clean_name]
        
    title_name = safe_name.strip().title()
    lowercase_suffixes = [
        'tailed', 'rumped', 'eared', 'breasted', 'winged', 'naped', 
        'bellied', 'capped', 'crowned', 'throated', 'backed', 'billed', 
        'faced', 'headed', 'necked', 'eyed', 'legged', 'footed', 'browed',
        'wren', 'shrike', 'cuckoo', 'quail', 'knee', 'beaked'
    ]
    for suffix in lowercase_suffixes:
        title_name = title_name.replace(f"-{suffix.title()}", f"-{suffix}")
        
    return title_name.replace("'S", "'s")

def parse_vba_summary(filepath):
    with open(filepath, 'r', encoding='latin1') as f:
        lines = f.readlines()

    reserve_name = "Unknown Reserve"
    header_idx = -1

    for i, line in enumerate(lines):
        safe_line = str(line)
        if "Name:" in safe_line and reserve_name == "Unknown Reserve":
            parts = safe_line.split("Name:")
            if len(parts) > 1:
                reserve_name = str(parts[-1]).strip()
                
        if safe_line.startswith('Taxon ID'):
            header_idx = i
            break
            
    if header_idx == -1:
        print(f"   ⚠️ Could not find 'Taxon ID' header in {os.path.basename(filepath)}. Skipping.")
        return pd.DataFrame(), reserve_name

    clean_lines = []
    for line in lines[header_idx:]:
        safe_line = str(line)
        if safe_line.startswith('"Copyright') or safe_line.startswith('Copyright'):
            break 
        if safe_line.strip(): 
            clean_lines.append(safe_line)

    csv_data = "".join(clean_lines)
    return pd.read_csv(io.StringIO(csv_data)), reserve_name

def inject_inaturalist_data(species_dict):
    print("   🌐 Fetching modern iNaturalist sightings...")
    TARGET_TAXA = "3,40151,26036,20978"
    
    for reserve_name, coords in RESERVES.items():
        lat_min, lat_max, lon_min, lon_max = coords
        url = f"https://api.inaturalist.org/v1/observations/species_counts?swlat={lat_min}&swlng={lon_min}&nelat={lat_max}&nelng={lon_max}&quality_grade=research&taxon_id={TARGET_TAXA}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                for result in response.json().get('results', []):
                    taxon = result.get('taxon', {})
                    raw_name = taxon.get('preferred_common_name') or taxon.get('name')
                    if not raw_name: continue
                        
                    name = normalise_species_name(raw_name)
                    if any(bad in name.lower() for bad in EXCLUDE_LIST): continue
                    
                    if name not in species_dict:
                        species_dict[name] = {
                            "scientific_name": taxon.get('name', 'Unknown'),
                            "threat_status": "Least Concern", 
                            "status": "unrecorded",
                            "reserves": [reserve_name]
                        }
                    elif reserve_name not in species_dict[name]["reserves"]:
                        species_dict[name]["reserves"].append(reserve_name)
            time.sleep(1) 
        except Exception as e:
            print(f"   ❌ iNat Error for {reserve_name}: {e}")
    return species_dict

def build_master_list():
    print("🧬 Scanning repository for VBA Summary Files...")
    
    # Recursively search the entire repository for CSV files
    all_csvs = glob.glob("**/*.csv", recursive=True) + glob.glob("**/*.CSV", recursive=True)
    
    # Filter to only grab your specific VBA reports
    vba_files = [f for f in all_csvs if "report_" in str(f).lower()]
    
    if not vba_files:
        print("   ⚠️ No VBA reports found! Make sure your CSVs are uploaded to GitHub.")
        return {}

    master_df = pd.DataFrame()
    for file in vba_files:
        try:
            print(f"   📥 Parsing {os.path.basename(file)}...")
            df, reserve_name = parse_vba_summary(file)
            if not df.empty:
                df['Reserve'] = reserve_name 
                master_df = pd.concat([master_df, df], ignore_index=True)
        except Exception as e:
            print(f"   ❌ Error reading {os.path.basename(file)}: {e}")

    if master_df.empty: return {}

    master_df['Normalised Name'] = master_df['Common Name'].apply(normalise_species_name)
    species_dict = {}
    
    for _, row in master_df.iterrows():
        name = row['Normalised Name']
        reserve = row['Reserve']
        
        if not name or str(name).lower() == "nan": continue
        if any(bad in name.lower().replace("-", " ") for bad in EXCLUDE_LIST): continue

        final_status = str(row.get('FFG Status', 'Least Concern')).strip()
        if final_status == "Not Listed": final_status = "Least Concern"
        if name in STATUS_OVERRIDES: final_status = STATUS_OVERRIDES[name]

        if name not in species_dict:
            species_dict[name] = {
                "scientific_name": row.get('Scientific Name', 'Unknown'),
                "threat_status": final_status,
                "status": "unrecorded",
                "reserves": [reserve]
            }
        elif reserve not in species_dict[name]["reserves"]:
            species_dict[name]["reserves"].append(reserve)

    species_dict = inject_inaturalist_data(species_dict)
    print(f"✅ Success! Extracted {len(species_dict)} expected species.")
    return species_dict

# OFFICIAL RESERVES
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

def normalise_zone_name(zone_raw):
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

def calculate_acoustic_prominence(observations):
    """Calculates Vocal Dependency: % of a species' own records that are audio."""
    species_counts = {}
    
    for obs in observations:
        species = str(obs.get('Common Name', '')).strip()
        # Make it lowercase for safe searching
        media_type = str(obs.get('Media Type', '')).strip().lower() 
        
        if not species:
            continue
            
        if species not in species_counts:
            species_counts[species] = {'audio_hits': 0, 'total_hits': 0}
            
        # Add to total encounters
        species_counts[species]['total_hits'] += 1
        
        # If the word 'audio' is anywhere in the Media Type column, count it!
        if 'audio' in media_type:
            species_counts[species]['audio_hits'] += 1
            
    # Calculate the 0-100 score for each species
    acoustic_scores = {}
    for species, counts in species_counts.items():
        total = counts['total_hits']
        audio = counts['audio_hits']
        
        if total > 0:
            score = (audio / total) * 100
            acoustic_scores[species] = int(score)
        else:
            acoustic_scores[species] = 0
            
    return acoustic_scores

def calculate_sociality(observations):
    import re 
    
    species_max_qty = {}
    
    for obs in observations:
        species = str(obs.get('Common Name', '')).strip()
        raw_qty = obs.get('Qty')
        
        if not species:
            continue
            
        if isinstance(raw_qty, (int, float)):
            qty = int(raw_qty)
        else:
            qty_str = str(raw_qty).strip()
            try:
                numbers = re.findall(r'\d+', qty_str)
                qty = int(numbers.pop(0)) if numbers else 1
            except Exception as e:
                qty = 1
                
        qty = max(1, qty)
        
        # Track the LARGEST group ever seen
        if species not in species_max_qty:
            species_max_qty[species] = 1
            
        if qty > species_max_qty[species]:
            species_max_qty[species] = qty

    # Calculate the scores
    sociality_scores = {}
    SOCIAL_CAP = 5.0 
    
    for species, max_qty in species_max_qty.items():
        if max_qty <= 1:
            score = 0
        elif max_qty >= SOCIAL_CAP:
            score = 100
        else:
            score = ((max_qty - 1) / (SOCIAL_CAP - 1)) * 100
            
        sociality_scores[species] = int(score)
        
    return sociality_scores

def calculate_moisture_affinity(observations):
    import math 
    """Calculates a 0-100 Moisture score based on VPD from Temp and Humidity."""
    
    # ==========================================
    # 💧 THE OBLIGATE MOISTURE VIP LIST
    # ==========================================
    OBLIGATE_WATER_SPECIES = [
        "Chestnut Teal", "Pacific Black Duck", "Domestic Mallard",
        "Eurasian Coot", "Australasian Swamphen", "Dusky Moorhen",
        "Little Pied Cormorant", "Great Cormorant",
        "Hoary-headed Grebe", "Australasian Grebe",
        "White-faced Heron", "Silver Gull",
        "Short-finned Eel", "Australian Wood Duck"
    ]

    species_vpds = {}
    global_vpds = []
    all_seen_species = set()
    
    # 1. Calculate VPD for every valid row
    for obs in observations:
        species = str(obs.get('Common Name', '')).strip()
        if not species:
            continue
            
        all_seen_species.add(species) 
        
        temp_str = str(obs.get('Temp. (°C)', '')).strip()
        humid_str = str(obs.get('Humid. (%)', '')).strip()
        
        # Skip VPD math if missing core data
        if not temp_str or not humid_str:
            continue
            
        try:
            T = float(temp_str)
            RH = float(humid_str)
            
            # Calculate Saturation Vapor Pressure (SVP) in kPa
            svp = 0.61078 * math.exp((17.27 * T) / (T + 237.3))
            
            # Calculate actual Vapor Pressure Deficit (VPD) in kPa
            vpd = svp * (1 - (RH / 100.0))
            
            # Log the data
            if species not in species_vpds:
                species_vpds[species] = []
                
            species_vpds[species].append(vpd)
            global_vpds.append(vpd) # Keep a master list to find the baseline
            
        except ValueError:
            # Silently catch rows where weather data might be "N/A" or corrupted
            pass

    affinity_scores = {}

    # 2. Establish the Regional Baseline & Run Terrestrial Math
    if global_vpds:
        global_min_vpd = min(global_vpds) # The wettest condition recorded
        global_max_vpd = max(global_vpds) # The driest condition recorded
        
        print(f"\n--- Moisture Baseline Established ---")
        print(f"Wettest (Max Affinity): {global_min_vpd:.2f} kPa")
        print(f"Driest (Min Affinity): {global_max_vpd:.2f} kPa")

        for species, vpds in species_vpds.items():
            avg_vpd = sum(vpds) / len(vpds)
            
            # Prevent division by zero if all data comes from a single weather moment
            if global_max_vpd == global_min_vpd:
                affinity_scores[species] = 50 
                continue
                
            # Calculate percentage along the scale
            scale_pos = (avg_vpd - global_min_vpd) / (global_max_vpd - global_min_vpd)
            
            # Invert the scale: 100 = Wet (Min VPD), 0 = Dry (Max VPD)
            score = (1.0 - scale_pos) * 100
            
            affinity_scores[species] = int(max(0, min(100, score))) # Clamp between 0 and 100

    for species in all_seen_species:
        species_lower = species.lower()
        
        # If it's a waterbird or amphibian, bypass the math and force it to 100
        if species in OBLIGATE_WATER_SPECIES or "frog" in species_lower or "toad" in species_lower:
            affinity_scores[species] = 100
            
        # Safety net: If a terrestrial bird had NO weather data logged at all, give it a neutral 50
        elif species not in affinity_scores:
            affinity_scores[species] = 50

    return affinity_scores

def generate_radar_payload(observations, traits_dict):
    """Compiles empirical data and LUT traits into the final radar chart JSON."""
    
    # 1. Run the empirical calculators once
    acoustic_data = calculate_acoustic_prominence(observations)
    sociality_data = calculate_sociality(observations)
    moisture_data = calculate_moisture_affinity(observations)
    
    # 2. Get a unique list of all species recorded so far
    recorded_species = set(str(obs.get('Common Name', '')).strip() for obs in observations if obs.get('Common Name'))
    
    radar_payload = {}
    
    # 3. Assemble the 5 stats per species
    for species in recorded_species:
        # A. Pull Empirical Scores (with safe defaults if missing)
        ac_score = acoustic_data.get(species, 0)
        soc_score = sociality_data.get(species, 20)
        moist_score = moisture_data.get(species, 50) 
        
        # B. Pull Static Traits from the LUT
        trait_info = traits_dict.get(species, {"habitats": [], "stratum": 50})
        
        hab_score = (len(trait_info['habitats']) / 4.0) * 100
        
        # C. Build the final dictionary for this species
        radar_payload[species] = {
            "Acoustic_Prominence": ac_score,
            "Sociality": soc_score,
            "Moisture_Affinity": moist_score,
            "Vertical_Stratum": trait_info['stratum'],
            "Habitat_Breadth": int(min(100, hab_score)) # Cap at 100
        }
        
    return radar_payload

# ==========================================
# --- MAIN RADAR SYSTEM ---
# ==========================================

def run_radar_system():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    print("\n📡 INITIALISING DUNKLEY BIODIVERSITY RADAR (V4.5 - CLOUD EDITION)...")
    
    try:
        # 1. Pull the secret from the GitHub Cloud Environment
        creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
        
        # 2. Authenticate the Bot
        client = gspread.service_account_from_dict(creds_dict)
        
        # 3. Open the main sheet safely and load into Pandas
        sheet = client.open_by_key(SHEET_KEY).sheet1
        df = pd.DataFrame(sheet.get_all_records())
        print(f"   📊 Successfully loaded {len(df)} observations from Google Sheets.")

        # ==========================================
        # 1. COLUMN MAPPING (Do this FIRST so Pandas knows the names!)
        # ==========================================
        cols = {k.lower(): k for k in df.columns}
        name_col = cols.get('common name', cols.get('species', 'Common Name'))
        dist_col = next((c for c in df.columns if 'distance' in c.lower()), 'Distance')
        dur_col = next((c for c in df.columns if 'duration' in c.lower()), 'Duration')
        date_col = next((c for c in df.columns if 'date' in c.lower()), 'Date/Time')
        zone_col = next((c for c in df.columns if 'zone' in c.lower()), 'Zone')
        notes_col = next((c for c in df.columns if 'note' in c.lower()), 'Notes')
        media_col = next((c for c in df.columns if 'media' in c.lower()), 'Media Type')
        
        # Original Weather columns
        temp_col = next((c for c in df.columns if 'temp' in c.lower() and 'local' not in c.lower()), 'Temp. (°C)')
        hum_col = next((c for c in df.columns if 'humid' in c.lower() and 'local' not in c.lower()), 'Humid. (%)')
        loc_t_col = next((c for c in df.columns if 'local t' in c.lower()), 'Local T.')
        loc_h_col = next((c for c in df.columns if 'local h' in c.lower()), 'Local H.')

        # NEW: Map the 5 new covariates
        wspd_col = next((c for c in df.columns if 'speed' in c.lower()), 'W. Speed (Km/h)')
        wgust_col = next((c for c in df.columns if 'gust' in c.lower()), 'W. Gust (Km/h)')
        precip_col = next((c for c in df.columns if 'precip' in c.lower()), 'Precip.')
        press_col = next((c for c in df.columns if 'press' in c.lower()), 'Press.')
        cloud_col = next((c for c in df.columns if 'cloud' in c.lower()), 'Cloud')

        df.rename(columns={
            name_col: 'Common Name', 
            dist_col: 'Distance', 
            dur_col: 'Duration', 
            date_col: 'Date/Time', 
            zone_col: 'Zone',
            notes_col: 'Notes',
            media_col: 'Media Type',
            temp_col: 'Temp. (°C)',
            hum_col: 'Humid. (%)',
            wspd_col: 'W. Speed (Km/h)',
            wgust_col: 'W. Gust (Km/h)',
            precip_col: 'Precip.',
            press_col: 'Press.',
            cloud_col: 'Cloud',
            loc_t_col: 'Local T.',
            loc_h_col: 'Local H.'
        }, inplace=True)

        # ==========================================
        # 2. GLOBAL DATA SCRUBBER (Site-wide Exclusions)
        # ==========================================
        print("   🧹 Scrubbing excluded species...")

        tier_col_name = df.columns 
        initial_count = len(df)
        df = df[~df.iloc[:, 1].astype(str).str.lower().str.contains('historical', na=False)]
        print(f"   🧹 Purged {initial_count - len(df)} Historical observations. {len(df)} Active Audit records remain.")

        EXCLUDE_LIST = [
            "fur seal", "little penguin", "red junglefowl", 
            "undetermined", "dingo", "dog", "domestic", "unidentified", "kangaroo", 
            " and ", "possums", "unknown", "×", " sp.", "birds", "cattle", 
            "pardalotes", "black faced cuckoo shrike", "scarlet myzomela",
            "blue spotted hawker", "ferret", "common froglet", "domestic cat", "hawker",
            "eastern brown snake", "song thrush", "australian pipit", "painted honeyeater",
            "southern emu wren", "weebill", "white fronted chat", "rose robin", "jacky winter"
            "swift parrot" "lathams snipe", "blue winged parrot", "white footed dunnart"
            "eastern pygmy possum", "new holland mouse", "southern brown bandicoot", 
            "eurasian skylark", "lesser long eared bat", "haswell's frog", "haswells frog",
            "south eastern free tailed bat", "hooded robin", "chocolate wattled bat",
            "southern forest bat", "european starling"

        ]
         
        if 'Common Name' in df.columns:
            # 1. Escape special characters (so " sp." is treated as text)
            import re # Ensure regex is imported
            escaped_excludes = [re.escape(word.lower()) for word in EXCLUDE_LIST]
            
            # 2. Join them into one massive OR statement (e.g., "dog|cat|ferret")
            exclude_pattern = '|'.join(escaped_excludes)
            
            # 3. Filter the DataFrame: Keep rows where Common Name DOES NOT (~) contain the pattern
            original_count = len(df)
            df = df[~df['Common Name'].astype(str).str.lower().str.contains(exclude_pattern, regex=True, na=False)]
            
            print(f"   [✅] Scrubber removed {original_count - len(df)} invalid rows.")
        else:
            print("   [⚠️] 'Common Name' column still not found. Scrubber skipped.")

        # ==========================================
        # 3. DOWNLOAD EFFORT MATRIX
        # ==========================================
        try:
            effort_sheet = client.open_by_key(SHEET_KEY).worksheet("Junk Drawer")
            matrix_data = effort_sheet.get("CH:CM")
            
            if len(matrix_data) > 0:
                # 1. Load into Pandas
                df_effort = pd.DataFrame(matrix_data)
                
                # 2. Force exactly 6 columns (pads short rows, trims long rows)
                df_effort = df_effort.reindex(columns=range(6))
                df_effort.columns = ['Session_Date', 'Zone', 'Cell_ID', 'Active_Seconds', 'Cell_Lat', 'Cell_Lon']
                
                # 3. Drop the text header row if it exists
                df_effort = df_effort[df_effort['Active_Seconds'] != 'Active_Seconds']
                
                # 4. Convert math columns to pure numbers
                df_effort['Active_Seconds'] = pd.to_numeric(df_effort['Active_Seconds'], errors='coerce').fillna(0)
                df_effort['Cell_Lat'] = pd.to_numeric(df_effort['Cell_Lat'], errors='coerce')
                df_effort['Cell_Lon'] = pd.to_numeric(df_effort['Cell_Lon'], errors='coerce')
                
                # 5. Drop any empty/corrupted rows
                df_effort = df_effort.dropna(subset=['Active_Seconds', 'Cell_Lat', 'Cell_Lon'])
                
                # ==========================================
                # 6. 25m -> 50m TILES
                # ==========================================
                lat_step = 0.000450
                lon_step = 0.000572
                
                # Snap the micro-coordinates to the new macro-grid
                df_effort['Cell_Lat'] = (df_effort['Cell_Lat'] // lat_step) * lat_step
                df_effort['Cell_Lon'] = (df_effort['Cell_Lon'] // lon_step) * lon_step
                
                # Overwrite the Cell_ID so the 4 grouped tiles now share the exact same ID
                df_effort['Cell_ID'] = df_effort['Cell_Lat'].round(6).astype(str) + "_" + df_effort['Cell_Lon'].round(6).astype(str)
                
                # Squash the dataframe: Sum the Active Seconds for the new, larger Macro-Tiles
                df_effort = df_effort.groupby(['Session_Date', 'Zone', 'Cell_ID', 'Cell_Lat', 'Cell_Lon'])['Active_Seconds'].sum().reset_index()
                # ==========================================

                print(f"   🗺️ Successfully loaded and grouped into {len(df_effort)} macro effort grid cells.")
                
                print(f"   🗺️ Successfully loaded {len(df_effort)} effort grid cells.")
            else:
                print("   ⚠️ Junk Drawer matrix is empty.")
                df_effort = pd.DataFrame()
                
        except Exception as e:
            print(f"   ⚠️ Could not load Junk Drawer: {e}")
            df_effort = pd.DataFrame()
            
    except KeyError:
        print("❌ Error: GOOGLE_CREDENTIALS secret not found in environment.")
        return
    except Exception as e:
        print(f"❌ Error connecting to Google Sheets: {e}")
        return

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

    total_km = round(float(daily_stats['Distance'].sum()), 1)
    total_hours = float(round(daily_stats['Duration'].sum() / 60, 1))
    print(f"   📊 MATH CHECK: {total_hours} Hours across {len(daily_stats)} unique field days.")

   # =========================================================
    # VPD SCATTER PLOT ENGINE (UPGRADED WITH LOCAL WEATHER)
    # =========================================================
    print("   📊 Calculating Vapor Pressure Deficit (VPD)...")

    # 1. Ensure all potential weather columns are numeric
    df['Temp. (°C)'] = pd.to_numeric(df.get('Temp. (°C)', np.nan), errors='coerce')
    df['Humid. (%)'] = pd.to_numeric(df.get('Humid. (%)', np.nan), errors='coerce')
    df['Local T.'] = pd.to_numeric(df.get('Local T.', np.nan), errors='coerce')
    df['Local H.'] = pd.to_numeric(df.get('Local H.', np.nan), errors='coerce')

    # 2. Prioritise Local Weather, fallback to API Weather
    def compute_best_vpd(row):
        # Try Local Data First
        t = row.get('Local T.')
        h = row.get('Local H.')
        
        # Fall back to the regional Visual Crossing data
        if pd.isnull(t) or pd.isnull(h):
            t = row.get('Temp. (°C)')
            h = row.get('Humid. (%)') # FIXED: Matches your CSV perfectly
            
        # Valid numbers from either source, calculate VPD
        if pd.notnull(t) and pd.notnull(h):
            return calculate_vpd(t, h)
        return None

    # 3. Apply VPD math row by row
    df['VPD_kPa'] = df.apply(compute_best_vpd, axis=1)

    # 4. Filter missing data
    vpd_df = df.dropna(subset=['VPD_kPa', 'Zone'])
    
    # 5. Extract only what the scatter plot needs
    vpd_export = vpd_df[['Date/Time', 'Zone', 'Common Name', 'VPD_kPa']].copy()
    vpd_export['Taxonomy'] = vpd_df.get('Taxonomy', 'Unknown')
    
    vpd_export_data = vpd_export.to_dict(orient='records')
    
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
    optimised_heatmap = []  # For the heatmap layer

    for _, row in df.iterrows():
        # --- INTEGRITY BYPASS ---
        row_notes = str(row.get('Notes', '')).upper()
        if "[CONTENDED]" in row_notes:
            continue
        # ------------------------

        # Clean Inputs
        species_name = str(row.get('Common Name', 'Unknown')).strip()
        raw_zone = str(row.get('Zone', ''))
        clean_zone = normalise_zone_name(raw_zone)
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
                    optimised_heatmap.append([s_lat, s_lon, 0.5])
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
    
    # Initialise everything with None (translates to null in JSON)
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
    # --- 1. LIVE STATS ENGINE ---
    # ==========================================
    print("   📊 Crunching live statistics from spreadsheet...")
    
    pokedex_stats = {}
    rejection_log = []
    
    # Strip invisible spaces
    df.columns = df.columns.str.strip()
    df['DateObj'] = pd.to_datetime(df['Date/Time'], dayfirst=True, errors='coerce')

    if 'Species' in df.columns:
        df = df.rename(columns={'Species': 'Common Name'})
        
    # Drop the "CONTENDED" rows safely
    if 'Notes' in df.columns:
        df = df[~df['Notes'].astype(str).str.lower().str.contains('contended', na=False)]

    # Define the official boundaries once
    valid_reserves = ["The Pines Flora and Fauna Reserve", "Langwarrin Flora and Fauna Reserve", "Kananook Creek", "Frankston Nature Conservation Reserve", "Obscured"]

    for species, group in df.groupby('Common Name'):
        raw_name = str(species).strip()
        clean_species_name = normalise_species_name(raw_name)

        # 1. Apply the master Exclude List
        if any(bad in clean_species_name.lower() for bad in EXCLUDE_LIST):
            continue
            
        # 2. Zone Boundary Check
        zone_col = next((c for c in group.columns if str(c).strip().lower() == 'zone'), None)
        if zone_col:
            group_zones = group[zone_col].dropna().astype(str).str.strip().tolist()
            # If the animal was NEVER seen inside a valid reserve, block it from the Library
            if not any(z in valid_reserves for z in group_zones):
                rejection_log.append(f"Historical (Live),{clean_species_name},Outside Reserve,Out of Bounds Zone")
                continue
            
        # 2. Safely pull and normalise Taxonomy WITHOUT dropping anything
        taxonomy = "Unknown"
        if 'Taxonomy' in group.columns and not group['Taxonomy'].dropna().empty:
            raw_tax = str(group['Taxonomy'].mode().iloc).lower()
            
            if "bird" in raw_tax or "aves" in raw_tax: 
                taxonomy = "Bird"
            elif "mammal" in raw_tax: 
                taxonomy = "Mammal"
            elif "reptile" in raw_tax: 
                taxonomy = "Reptile"
            elif "amphibian" in raw_tax or "frog" in raw_tax: 
                taxonomy = "Amphibian"
            elif "insect" in raw_tax or "arachnid" in raw_tax: 
                taxonomy = "Insect"
            elif "fish" in raw_tax:
                taxonomy = "Fish"
            elif raw_tax != "nan":
                # Fallback: Just capitalise whatever it is, removing brackets
                taxonomy = raw_tax.replace("[", "").replace("]", "").replace("'", "").title()

        # A. Basic Counts & Dates
        encounters = int(len(group))
        latest_date = group['DateObj'].max()
        latest_str = "Unknown" if pd.isna(latest_date) else latest_date.strftime('%d/%m/%y')

        # B. Detection Profile
        media_counts = group['Media Type'].astype(str).str.lower().value_counts()
        audio_c, visual_c = 0, 0
        for val, count in media_counts.items():
            if 'audio' in val: audio_c += count
            if 'visual' in val: visual_c += count
        
        total_av = audio_c + visual_c
        if total_av > 0:
            a_pct = (audio_c / total_av) * 100
            detection = "Audio" if a_pct >= 75 else "Visual" if a_pct <= 25 else "Mixed"
        else:
            detection = "Unknown"

       # C. Security & Hotspot Logic
        threat_keywords = ["vulnerable", "endangered", "threatened", "critically"]
        
        raw_status = "unknown"
        # Case-insensitive column search for Conservation Status
        status_col = next((c for c in group.columns if str(c).strip().lower() == 'conservation status'), None)
        if status_col:
            raw_status = str(group[status_col].to_list()).lower()
            
        is_sensitive = any(k in raw_status for k in threat_keywords) or \
                       any(s in clean_species_name.lower() for s in ["glossy black-cockatoo", "powerful owl"])

        if is_sensitive:
            hotspot = "Hidden"
        else:
            hotspot = "Unknown"
            
            zone_col = next((c for c in group.columns if str(c).strip().lower() == 'zone'), None)
            
            if zone_col:
                valid_zones = group[zone_col].dropna().astype(str).str.strip()
                valid_zones = valid_zones[valid_zones != ""]
                valid_zones = valid_zones[valid_zones.str.lower() != "nan"]
                
                if not valid_zones.empty:
                    raw_hotspot = str(valid_zones.mode().tolist())
                    clean_hotspot = raw_hotspot.replace("[", "").replace("]", "").replace("'", "").replace('"', "").strip()

                    if "Frankston" in clean_hotspot and "Nature" in clean_hotspot:
                        hotspot = "Frankston NCR"
                    elif "Langwarrin" in clean_hotspot:
                        hotspot = "Langwarrin FFR"
                    elif "Pines" in clean_hotspot:
                        hotspot = "The Pines FFR"
                    elif "Kananook" in clean_hotspot:
                        hotspot = "Kananook Creek"
                    else:
                        hotspot = clean_hotspot

        if "gull" in clean_species_name.lower() or "echidna" in clean_species_name.lower():
            print(f"      📍 Hotspot Calculated: '{hotspot}'")

        # Store results
        pokedex_stats[clean_species_name] = {
            "count": encounters,
            "latest_date": latest_str,
            "detection": detection, 
            "hotspot": hotspot,
            "taxonomy": taxonomy
        }
        
        if "gull" in clean_species_name.lower():
            print("      ✅ Added to Pokedex Stats successfully!")
    # ========================
    # --- 2. MASTER MERGE ---
    # ========================
    print("    🧬 Building Expected Master List from VBA & iNat...")
    library_payload = build_master_list()

    js_omit_list = ['bee', 'wasp', 'ant', 'butterfly', 'moth', 'spider', 'insect', 'fish', 'eel', 'gambusia', 'dragonfly', 'crustacean', 'invertebrate']
    safe_keywords = ['fantail', 'cormorant', 'kingfisher', 'antechinus', 'frogmouth', 'bee-eater', 'fly-catcher']
    
    global_exclude_list = ["blue spotted hawker", "domestic cat", "ferret", "domestic dog", "cattle"]

    # 1. Scrub the historical VBA/iNat data
    keys_to_delete = [
        sp for sp in library_payload.keys() 
        if (any(omit in str(sp).lower() for omit in js_omit_list) and not any(safe in str(sp).lower() for safe in safe_keywords))
        or any(banned in str(sp).lower() for banned in global_exclude_list) # Added global exclude check
    ]
    for k in keys_to_delete:
        rejection_log.append(f"Historical (VBA),{k},N/A,Taxonomy Exclusion")
        del library_payload[k]

    print("    🔗 Merging Live Spreadsheet Data...")
    
    norm_library_keys = {normalise_species_name(lib_key).lower(): lib_key for lib_key in library_payload}

    for sp_name, stats in pokedex_stats.items():
        
        # Normalise incoming spreadsheet species name
        obs_norm = normalise_species_name(sp_name).lower()
        
        # 🚨 THE INTERCEPTOR: Kills the row if it's on the global exclude list
        if any(banned in obs_norm for banned in global_exclude_list):
            rejection_log.append(f"Historical (Live),{sp_name},N/A,Hard Exclusion")
            continue
        
        # 1. Exclusion check (use normalised name as well for consistency)
        if any(omit in obs_norm for omit in js_omit_list) and not any(safe in obs_norm for safe in safe_keywords):
            rejection_log.append(f"Historical (Live),{sp_name},N/A,Taxonomy Exclusion")
            continue
        
        # 2. Try exact normalised match
        matched_key = norm_library_keys.get(obs_norm, None)
        
        # 3. Fuzzy match (normalised), if exact not found
        if not matched_key:
            import difflib # Ensure this is imported!
            close_matches = difflib.get_close_matches(
                obs_norm,
                norm_library_keys.keys(),
                n=1, cutoff=0.85  # a little more forgiving
            )
            if close_matches:
                matched_key = norm_library_keys[close_matches[0]] 
                print(f"      🪄 Fuzzy Matched: '{sp_name}' -> '{matched_key}'")
                
                df.loc[df['Common Name'] == sp_name, 'Common Name'] = matched_key

        # 4. Apply (still using original/unnormalised library key)
        if matched_key:
            entry = library_payload[matched_key]
            entry['status'] = "recorded"
            
            entry['liveCount'] = entry.get('liveCount', 0) + stats['count']
            
            # Safely grab the most recent date between the correct spelling and the typo
            current_latest = entry.get('liveLastSighted', "")
            new_latest = stats['latest_date']
            if new_latest > current_latest:
                entry['liveLastSighted'] = new_latest
                
            entry['liveDetection'] = stats['detection']
            entry['liveHotspot'] = stats['hotspot']
            entry['liveTaxonomy'] = stats['taxonomy']
        else:
            # 5. New discovery (store normalised name for consistency)
            clean_new_name = normalise_species_name(sp_name)
            library_payload[clean_new_name] = {
                "scientific_name": "Unknown (New Discovery)", 
                "threat_status": STATUS_OVERRIDES.get(sp_name, "Unknown"), 
                "status": "recorded",
                "liveCount": stats['count'],
                "liveLastSighted": stats['latest_date'],
                "liveDetection": stats['detection'],
                "liveHotspot": stats['hotspot'],
                "liveTaxonomy": stats['taxonomy']
            }
            norm_library_keys[clean_new_name.lower()] = clean_new_name
            print(f"      [NEW] Could not find a match for '{sp_name}', added as new discovery")

    print(f"    ✅ Library Complete: {len(library_payload)} total species cards ready.")

    # ==========================================
    # --- FINAL PAYLOAD SPLIT & LOCAL EXPORT ---
    # ==========================================
    print("    📦 Assembling and writing final JSON payloads...")

    # 1. Enhanced atomic_write function with verbose logging
    def atomic_write(payload_data, filename):
        final_path = os.path.join(OUTPUT_DIR, filename)
        temp_path = final_path + ".tmp"
        print(f"    🔍 Writing to: {final_path}")
        print(f"    📦 Payload size: {len(json.dumps(payload_data))} bytes")
        
        try:
            with open(temp_path, 'w') as f:
                json.dump(payload_data, f, separators=(',', ':'), default=str)
            print(f"    ✓ Temp file created: {temp_path}")
            
            # Verify temp file was created
            if os.path.exists(temp_path):
                shutil.move(temp_path, final_path)
                print(f"    ✅ {filename} Written Successfully.")
            else:
                print(f"    ❌ Temp file not found at {temp_path}")
        except Exception as e:
            print(f"    ❌ Error writing {filename}: {e}")
            import traceback
            traceback.print_exc()

    # 2. THE PERFECT MATCH ALGORITHM
    
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
        
        # Safe extraction without brackets
        sp_idx = row.__getitem__(2)
        zn_idx = row.__getitem__(3)
        st_idx = row.__getitem__(4)
        
        sp_name = species_legend.__getitem__(sp_idx)
        zn_name = zone_legend.__getitem__(zn_idx)
        st_name = status_legend.__getitem__(st_idx)
        
        # Javascript Exclusion Rule & Global Exclude List
        name_lower = str(sp_name).lower()
        
        if any(banned in name_lower for banned in global_exclude_list):
            rejection_log.append(f"Live Data,{sp_name},{zn_name},Hard Exclusion")
            continue

        if any(omit in name_lower for omit in js_omit_list) and not any(safe in name_lower for safe in safe_keywords):
            rejection_log.append(f"Live Data,{sp_name},{zn_name},Taxonomy Exclusion")
            continue
            
        # Zone Exclusion Rule
        if zn_name not in valid_zones:
            rejection_log.append(f"Live Data,{sp_name},{zn_name},Out of Bounds Zone")
            continue
            
        # Add to Final Counts
        if zn_name != "Unknown":
            strict_obs_count += 1
            strict_species_set.add(sp_name)
            
            if not any(b in str(st_name).lower() for b in js_threat_blacklist):
                strict_threatened_set.add(sp_name)

            # Add to Zone Badges (tracks unique species per zone)
            if zn_name in zone_species_sets:
                # Bracket-safe dictionary update
                zone_species_sets.get(zn_name).add(sp_name)

    # Calculate final zone badges directly from the tracker
    final_zone_badges = {z: len(sp_set) for z, sp_set in zone_species_sets.items()}

    # 3. BUILD ALL PAYLOADS
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
        "heatmap_data": optimised_heatmap 
    }

    dashboard_payload = {
        "meta": {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")},
        "summary": landing_payload.get("summary"), # Bracket-safe dictionary grab
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

    # ==========================================
    # 🚨 SPATIAL EFFORT & GEOJSON GENERATOR 🚨
    # ==========================================
    if not df_effort.empty:
        print("\n   🗺️ Building Effort-Corrected GeoJSON Heatmap...")
        try:
            # 🚨 THE FIX: Doubled the step sizes to match the 50x50m (2x2) Macro-Tiles
            LAT_STEP = 0.000450  
            LON_STEP = 0.000572  
            
            # 1. Aggregate historical effort per cell (Sum the seconds!)
            effort_grouped = df_effort.groupby('Cell_ID').agg({
                'Active_Seconds': 'sum',
                'Cell_Lat': 'first',
                'Cell_Lon': 'first',
                'Zone': 'first'
            }).reset_index()

            # 2. Find Lat/Lon columns in your main observation dataframe
            lat_col = next((c for c in df.columns if 'lat' in c.lower()), 'Latitude')
            lon_col = next((c for c in df.columns if 'lon' in c.lower()), 'Longitude')
            
            # 3. Snap observations to the NEW 50x50m grid
            df_geo = df.dropna(subset=[lat_col, lon_col]).copy()
            
            def get_cell_id(row):
                try:
                    c_lat = math.floor(float(row[lat_col]) / LAT_STEP) * LAT_STEP
                    c_lon = math.floor(float(row[lon_col]) / LON_STEP) * LON_STEP
                    # 🚨 THE FIX: Ensured the rounding matches the 6-decimal string format from df_effort
                    return f"{round(c_lat, 6)}_{round(c_lon, 6)}"
                except:
                    return "Invalid"
                    
            df_geo['Cell_ID'] = df_geo.apply(get_cell_id, axis=1)
            
            # 4. Count sightings per cell
            sighting_counts = df_geo[df_geo['Cell_ID'] != "Invalid"].groupby('Cell_ID').size().reset_index(name='Sightings')
            
            # 5. Merge Effort with Sightings and Calculate Density
            matrix = pd.merge(effort_grouped, sighting_counts, on='Cell_ID', how='left')
            matrix['Sightings'] = matrix['Sightings'].fillna(0)
            
            # Density Math: Sightings per Active Hour
            matrix['Active_Hours'] = matrix['Active_Seconds'] / 3600.0
            matrix['Density'] = matrix.apply(
                lambda r: round(r['Sightings'] / r['Active_Hours'], 2) if r['Active_Hours'] > 0 else 0, axis=1
            )
            
            # 6. Build the GeoJSON Polygons (using the new 50m steps)
            features = []
            for _, row in matrix.iterrows():
                c_lat = float(row['Cell_Lat'])
                c_lon = float(row['Cell_Lon'])
                
                # GeoJSON expects coordinates in [Longitude, Latitude] format
                poly = [
                    [c_lon, c_lat], 
                    [c_lon + LON_STEP, c_lat], 
                    [c_lon + LON_STEP, c_lat + LAT_STEP], 
                    [c_lon, c_lat + LAT_STEP], 
                    [c_lon, c_lat] # Close the loop
                ]
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [poly]
                    },
                    "properties": {
                        "cell_id": row['Cell_ID'],
                        "zone": row['Zone'],
                        "active_minutes": round(row['Active_Seconds'] / 60, 1),
                        "sightings": int(row['Sightings']),
                        "density": row['Density']
                    }
                })
                
            geojson_data = {
                "type": "FeatureCollection",
                "features": features
            }
            
            # 7. Save it to your output folder
            geojson_path = os.path.join(OUTPUT_DIR, "effort_heatmap.geojson")
            with open(geojson_path, "w") as f:
                json.dump(geojson_data, f)
                
            print(f"      [✅] GeoJSON Generated: {len(features)} spatial macro-cells mapped.")

        except Exception as e:
            print(f"      [❌] GeoJSON Generation Error: {e}")

    # ==========================================
    # 🚨 FINAL STATUS OVERRIDE ENFORCER
    # ==========================================
    print("\n   🛡️ Enforcing manual conservation statuses...")
    
    # 1. Create a "bulletproof" version of your override list (lowercase, no hyphens)
    safe_overrides = {
        k.lower().replace('-', ' ').replace('  ', ' '): v 
        for k, v in STATUS_OVERRIDES.items()
    }

    # 2. Scan every single animal going to the website
    override_count = 0
    for sp_name, data in library_payload.items():
        # Strip the incoming database name down to the same bulletproof format
        safe_db_name = sp_name.lower().replace('-', ' ').replace('  ', ' ')
        
        # If it matches, ruthlessly overwrite whatever DEECA/iNat said
        if safe_db_name in safe_overrides:
            data['threat_status'] = safe_overrides[safe_db_name]
            override_count += 1
            
    print(f"      [✅] Successfully forced {override_count} custom conservation statuses.")
    
    # ==========================================
    # GENERATE REJECTION RECEIPT
    # ==========================================

    print("\n--- Species in landing_data.json (strict_species_set) ---")
    print(sorted(strict_species_set))
    print(f"Count: {len(strict_species_set)}")

    print("\n--- Species in library_stats.json (library_payload.keys()) ---")
    print(sorted(library_payload.keys()))
    print(f"Count: {len(library_payload)}")

    # Diff sets
    missing_from_library = set(strict_species_set) - set(library_payload.keys())
    print("\nSpecies in landing, but NOT in library:", sorted(missing_from_library))

    missing_from_landing = set(library_payload.keys()) - set(strict_species_set)
    print("\nSpecies in library, but NOT in landing:", sorted(missing_from_landing))

    if rejection_log:
        print(f"\n🗑️ Generating Rejection Log ({len(rejection_log)} items blocked)...")
        log_path = os.path.join(OUTPUT_DIR, "Rejection_Log.csv")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("Data Source,Species,Zone,Reason for Rejection\n")
            for row in rejection_log:
                f.write(row + "\n")
        print(f"   [✅] Saved to {log_path}. Check GitHub repo for this file!")

    # ==========================================
    # GENERATE RADAR CHARTS
    # ==========================================
    print("\n🕸️ Generating Radar Chart Payload...")
    try:
        # 1. Load the biological traits dictionary (LUT)
        lut_path = os.path.join(os.path.dirname(__file__), "species_traits_reference.json")
        with open(lut_path, "r", encoding="utf-8") as f:
            species_traits_lut = json.load(f)
            
        # 2. Sanitise and Filter the DataFrame
        df.fillna('', inplace=True)
        
        # --- ENFORCE TAXONOMY BLACKLIST ---
        if 'Taxonomy' in df.columns:
            tax_blacklist = ["insect", "spider", "fish", "aquatic", "invertebrate", "crustacean"]
            radar_df = df[~df['Taxonomy'].astype(str).str.lower().str.contains('|'.join(tax_blacklist))]
        else:
            radar_df = df # Fallback if column is missing
            
        # 3. Run the assembler on the FILTERED data
        observations_list = radar_df.to_dict('records')
        radar_payload = generate_radar_payload(observations_list, species_traits_lut)
        
        if len(radar_payload) == 0:
            print("   [⚠️] WARNING: Radar payload is empty! Check column names.")
        else:
            print(f"   [✅] Radar Payload Generated for {len(radar_payload)} species.")
        
    except FileNotFoundError:
        print("   [❌] Radar Error: Could not find 'species_traits_reference.json'.")
        radar_payload = {}
    except Exception as e:
        print(f"   [❌] Radar Generation Error: {e}")
        radar_payload = {}

    # 4. EXPORT EVERYTHING
    print("\n   📝 Starting file exports...\n")
    atomic_write(library_payload, "library_stats.json")
    atomic_write(landing_payload, "landing_data.json")
    atomic_write(dashboard_payload, "dashboard_data.json")
    if radar_payload:
        atomic_write(radar_payload, "radar_stats.json")
    print("\n🚀 Pipeline Complete!")

if __name__ == "__main__":
    run_radar_system()
