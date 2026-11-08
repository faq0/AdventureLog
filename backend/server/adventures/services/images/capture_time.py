"""Capture time inference. Never use file modification/upload timestamps."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import io

from PIL import Image
from PIL.ExifTags import IFD
from django.db import transaction


def geographic_timezone(point):
    if point is None:
        return None
    from tzfpy import get_tz
    return get_tz(point.x, point.y) or None


def resolve_capture_time(local_value, *, offset=None, instant=None, point=None):
    result = {'captured_at': None, 'captured_local': None,
              'captured_timezone': None, 'capture_time_status': 'missing'}
    if not local_value:
        return result
    try:
        # EXIF uses colons in the calendar date, ISO/Immich uses hyphens.
        value = str(local_value).strip().strip('\x00')
        if len(value) >= 10 and value[4] == ':':
            value = value[:10].replace(':', '-') + value[10:]
        local = datetime.fromisoformat(value.replace('Z', '+00:00'))
        result['captured_local'] = local.replace(tzinfo=None).isoformat()
        zone_name = geographic_timezone(point)
        result['captured_timezone'] = zone_name
        zone = ZoneInfo(zone_name) if zone_name else None
        aware = None
        if instant:
            aware = datetime.fromisoformat(str(instant).replace('Z', '+00:00'))
            if aware.tzinfo is None:
                aware = None
        elif offset:
            aware = datetime.fromisoformat(local.replace(tzinfo=None).isoformat() + str(offset))
        elif local.tzinfo:
            aware = local
        if aware is not None:
            result['captured_at'] = aware.astimezone(timezone.utc)
            if zone:
                result['captured_local'] = aware.astimezone(zone).replace(tzinfo=None).isoformat()
            result['capture_time_status'] = 'known' if zone else 'missing_timezone'
            return result
        if not zone:
            result['capture_time_status'] = 'missing_timezone'
            return result
        # Check both folds and round-trip. Fall-back ambiguity and spring-forward
        # gaps cannot be resolved from a wall clock alone; retain only the day.
        naive = local.replace(tzinfo=None)
        candidates = set()
        for fold in (0, 1):
            candidate = naive.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
            if candidate.astimezone(zone).replace(tzinfo=None) == naive:
                candidates.add(candidate)
        if len(candidates) == 1:
            result['captured_at'] = candidates.pop()
            result['capture_time_status'] = 'known'
        else:
            result['capture_time_status'] = 'ambiguous' if candidates else 'invalid_local_time'
    except (ValueError, TypeError, ZoneInfoNotFoundError):
        result['capture_time_status'] = 'invalid'
    return result


def capture_from_bytes(content, *, point=None):
    try:
        with Image.open(io.BytesIO(content)) as image:
            exif = image.getexif()
            original = exif.get_ifd(IFD.Exif) if exif else {}
            return resolve_capture_time(original.get(36867) or exif.get(36867),
                                        offset=original.get(36881) or exif.get(36881), point=point)
    except Exception:
        return resolve_capture_time(None)


def capture_from_immich(payload, *, point=None):
    exif = payload.get('exifInfo') or {}
    if not exif.get('dateTimeOriginal'):
        return resolve_capture_time(None)
    # Immich's localDateTime is a wall clock serialized with Z, NOT a UTC instant.
    # fileCreatedAt/dateTimeOriginal are UTC-normalized. Without an EXIF timezone,
    # reinterpret the wall clock at the place rather than trusting a server zone.
    local_value = payload.get('localDateTime')
    if local_value:
        local_value = datetime.fromisoformat(local_value.replace('Z', '+00:00')).replace(tzinfo=None).isoformat()
    else:
        local_value = exif['dateTimeOriginal']
    return resolve_capture_time(local_value, instant=exif['dateTimeOriginal'] if exif.get('timeZone') else None,
                                point=point)


def sync_photo_visit(image):
    """Create/update one inferred visit, never replace a manually entered visit."""
    from adventures.models import Location, Visit
    if image.content_type.model != 'location' or image.source not in ('upload', 'immich'):
        return
    with transaction.atomic():
        location = Location.objects.select_for_update().get(pk=image.object_id)
        visits = location.visits.all()
        anchored = list(visits.filter(itinerary_date__isnull=False))
        if not anchored and visits.filter(photo_derived=False).exists():
            return
        # Resolve at the LOCATION (photo GPS may be just across a zone boundary).
        candidates = []
        for photo in location.images.filter(source__in=['upload', 'immich']).exclude(captured_local=None):
            point = location.coordinates or photo.coordinates
            metadata = resolve_capture_time(photo.captured_local,
                instant=photo.captured_at.isoformat() if photo.captured_at else None, point=point)
            if metadata['capture_time_status'] not in ('known', 'ambiguous', 'invalid_local_time'):
                continue
            local = datetime.fromisoformat(metadata['captured_local'])
            # Wall-clock ordering is wrong across a fall-back transition: 01:45
            # daylight time precedes 01:15 standard time. Compare known instants.
            # An unresolved time contributes only its day, never a guessed hour.
            order = metadata['captured_at']
            if order is None:
                order = local.replace(hour=0, minute=0, second=0, microsecond=0,
                    tzinfo=ZoneInfo(metadata['captured_timezone'])).astimezone(timezone.utc)
            candidates.append((order, metadata))
        if not candidates:
            return
        targets = anchored or [visits.filter(photo_derived=True, itinerary_date__isnull=True).first()]
        for inferred in targets:
            matching = candidates
            if inferred and inferred.itinerary_date:
                matching = [item for item in candidates
                    if datetime.fromisoformat(item[1]['captured_local']).date() == inferred.itinerary_date]
            if not matching:
                continue
            _, earliest = min(matching, key=lambda item: item[0])
            value = earliest['captured_at']
            date_only = value is None
            if date_only:
                value = datetime.fromisoformat(earliest['captured_local'][:10]).replace(tzinfo=timezone.utc)
            if inferred is None:
                inferred = Visit(location=location)
            inferred.start_date = inferred.end_date = value
            inferred.timezone = earliest['captured_timezone']
            inferred.date_only = date_only
            inferred.photo_derived = True
            inferred.save()


def ensure_itinerary_visit(location, target_date):
    """Keep the explicitly chosen local day, filling time only from matching photos."""
    from datetime import date
    from adventures.models import Location, Visit
    from adventures.utils.datetime_utils import is_all_day_bound
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)
    with transaction.atomic():
        location = Location.objects.select_for_update().get(pk=location.pk)
        zone_name = geographic_timezone(location.coordinates)
        zone = ZoneInfo(zone_name or 'UTC')
        visit = location.visits.filter(itinerary_date=target_date).first()
        if visit is None:
            for existing in location.visits.all():
                if not existing.start_date:
                    continue
                end = existing.end_date or existing.start_date
                all_day = existing.date_only if existing.date_only is not None else (
                    is_all_day_bound(existing.start_date) and is_all_day_bound(end))
                start_day = existing.start_date.date() if all_day else existing.start_date.astimezone(ZoneInfo(existing.timezone or zone.key)).date()
                end_day = end.date() if all_day else end.astimezone(ZoneInfo(existing.timezone or zone.key)).date()
                if start_day <= target_date <= end_day:
                    if not existing.photo_derived:
                        return existing
                    # This is already an inferred visit on the chosen local day.
                    existing.itinerary_date = target_date
                    existing.save(update_fields=['itinerary_date'])
                    visit = existing
                    break
        if visit is None:
            value = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
            visit = Visit.objects.create(location=location, start_date=value, end_date=value,
                date_only=True, timezone=zone_name, itinerary_date=target_date)
        photo = location.images.filter(source__in=['upload', 'immich']).first()
        if photo:
            sync_photo_visit(photo)
            visit.refresh_from_db()
        return visit
