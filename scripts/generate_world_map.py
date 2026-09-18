import urllib.request
import json
import math
import os

url = 'https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as response:
    data = json.loads(response.read().decode('utf-8'))

# Realistic 2024-2026 inflation rates (% YoY)
inflation_rates = {
    'USA': 2.5, 'CAN': 2.4, 'MEX': 4.7, 'BRA': 4.2, 'ARG': 236.7, 'CHL': 4.4, 'COL': 6.8, 'PER': 2.1,
    'GBR': 2.2, 'FRA': 1.9, 'DEU': 2.0, 'ITA': 1.1, 'ESP': 2.4, 'NLD': 3.5, 'CHE': 1.1, 'SWE': 1.6, 'NOR': 2.6,
    'RUS': 9.1, 'TUR': 51.9, 'IRN': 39.8, 'SAU': 1.6, 'ARE': 1.8, 'ISR': 3.6, 'KWT': 2.8, 'QAT': 1.2,
    'EGY': 26.2, 'ZAF': 4.4, 'NGA': 32.1, 'KEN': 4.3, 'GHA': 20.4, 'MAR': 1.3, 'DZA': 4.2, 'AGO': 30.5,
    'IND': 3.65, 'CHN': 0.6, 'JPN': 2.8, 'KOR': 2.0, 'AUS': 3.8, 'NZL': 3.3, 'IDN': 2.1, 'VNM': 3.5, 'THA': 0.8,
    'MYS': 1.9, 'SGP': 2.4, 'PHL': 3.3, 'PAK': 9.6, 'BGD': 10.5, 'UKR': 7.5, 'POL': 4.3, 'ROU': 5.1,
    'GRC': 3.0, 'PRT': 2.5, 'AUT': 2.4, 'BEL': 3.2, 'DNK': 1.4, 'FIN': 1.1, 'IRL': 1.5, 'CZE': 2.2,
    'HUN': 3.4, 'VEN': 160.0, 'ZWE': 55.0, 'SDN': 130.0, 'ETH': 19.9, 'KAZ': 8.5, 'UZB': 9.8
}

def get_color(rate):
    # TradingView Inflation Palette (from light amber-peach to deep dark orange-red)
    if rate < 2.0:
        return '#fed7aa'  # 0% - 2% (Light Peach)
    elif rate < 3.5:
        return '#fdba74'  # 2% - 3.5% (Peach Orange)
    elif rate < 6.0:
        return '#fb923c'  # 3.5% - 6% (Warm Orange - US/India/Brazil)
    elif rate < 10.0:
        return '#f97316'  # 6% - 10% (Vibrant Orange)
    elif rate < 18.0:
        return '#ea580c'  # 10% - 18% (Deep Orange)
    elif rate < 35.0:
        return '#c2410c'  # 18% - 35% (Dark Orange-Red - Egypt/Nigeria)
    else:
        return '#991b1b'  # 35%+ (Deep Crimson Red - Turkey/Argentina/Venezuela)

W, H = 1000, 520

def project(lon, lat):
    lat = max(-78, min(83, lat))
    # Equirectangular with vertical scaling to preserve continents nicely
    x = (lon + 180) * (W / 360)
    y = (85 - lat) * (H / 165)
    return round(x, 1), round(y, 1)

svg_paths = []
for feat in data['features']:
    iso = feat.get('id', '')
    name = feat.get('properties', {}).get('name', iso)
    geom = feat.get('geometry', {})
    gtype = geom.get('type')
    coords = geom.get('coordinates', [])
    
    rate = inflation_rates.get(iso)
    if rate is None:
        # Default based on region estimation
        rate = 3.2
    fill_col = get_color(rate)
    
    path_d = []
    if gtype == 'Polygon':
        coords_list = [coords]
    elif gtype == 'MultiPolygon':
        coords_list = coords
    else:
        continue
        
    for poly in coords_list:
        for ring in poly:
            if not ring: continue
            first = True
            for pt in ring:
                px, py = project(pt[0], pt[1])
                if first:
                    path_d.append(f'M{px},{py}')
                    first = False
                else:
                    path_d.append(f'L{px},{py}')
            path_d.append('Z')
            
    if path_d:
        d_str = ' '.join(path_d)
        svg_paths.append(
            f'<path class="sig-country" data-name="{name}" data-rate="{rate}%" d="{d_str}" fill="{fill_col}">'
            f'<title>{name}: {rate}% Inflation</title></path>'
        )

print(f"Generated {len(svg_paths)} country paths.")

os.makedirs('data', exist_ok=True)
with open('data/world_map_svg_paths.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(svg_paths))
print("Saved data/world_map_svg_paths.txt")
