"""Small cached GPS index; original photos are never downloaded for suggestions."""
import hashlib
import json
import math
import requests
from django.core.cache import cache

MAX_INDEX_BYTES = 16 * 1024 * 1024
MAX_MARKERS = 10000
PAGE_SIZE = 24


def distance_meters(lat, lon, other_lat, other_lon):
    lat, other_lat = math.radians(lat), math.radians(other_lat)
    dlat, dlon = other_lat - lat, math.radians(other_lon - lon)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat) * math.cos(other_lat) * math.sin(dlon / 2) ** 2
    return 6371008.8 * 2 * math.asin(min(1, math.sqrt(a)))


def nearby_assets(integration, latitude, longitude, radius, page):
    fingerprint = hashlib.sha256((integration.server_url + integration.api_key).encode()).hexdigest()[:20]
    key = f'immich-gps:{integration.pk}:{fingerprint}'
    markers = cache.get(key)
    if markers is None:
        with requests.get(integration.server_url.rstrip('/') + '/map/markers',
                          headers={'x-api-key': integration.api_key},
                          params={'withPartners': 'false', 'withSharedAlbums': 'false'},
                          timeout=(3, 10), stream=True) as response:
            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data) > MAX_INDEX_BYTES:
                    raise ValueError('This library is too large for lightweight nearby suggestions. Use date or album search.')
            markers = json.loads(data)
        if not isinstance(markers, list) or len(markers) > MAX_MARKERS:
            raise ValueError('This library is too large for lightweight nearby suggestions. Use date or album search.')
        markers = [(m['id'], float(m['lat']), float(m['lon'])) for m in markers]
        cache.set(key, markers, 900)
    matches = []
    for asset_id, lat, lon in markers:
        distance = distance_meters(latitude, longitude, lat, lon)
        if distance <= radius:
            matches.append((distance, asset_id))
    matches.sort()
    batch = matches[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
    if not batch:
        return [], False
    # Re-check current visibility/trash status when returning each page. The map
    # excludes locked assets; this additionally prevents cached IDs exposing any
    # asset moved to the locked folder or trash since the index was cached.
    response = requests.post(integration.server_url.rstrip('/') + '/search/metadata',
        headers={'x-api-key': integration.api_key}, timeout=(3, 10), json={
            'size': PAGE_SIZE, 'withExif': True,
            'filter': {'or': [{'id': {'eq': asset_id}} for _, asset_id in batch],
                       'visibility': {'in': ['timeline', 'archive']},
                       'trashedAt': {'eq': None}, 'type': {'eq': 'IMAGE'}}})
    response.raise_for_status()
    assets = {item['id']: item for item in response.json().get('assets', {}).get('items', [])}
    results = []
    for distance, asset_id in batch:
        if asset_id in assets:
            item = assets[asset_id]
            results.append({'id': asset_id, 'distance_meters': round(distance),
                            'localDateTime': item.get('localDateTime'),
                            'originalFileName': item.get('originalFileName', '')})
    return results, page * PAGE_SIZE < len(matches)
