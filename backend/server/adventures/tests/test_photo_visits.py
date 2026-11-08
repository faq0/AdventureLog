import io
from datetime import datetime, timezone
from unittest.mock import patch
from PIL import Image
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.test import TestCase, SimpleTestCase
from rest_framework.test import APIRequestFactory
from adventures.models import Location, ContentImage, Visit
from adventures.serializers import LocationSerializer, LocationListSerializer, VisitSerializer
from adventures.services.images.capture_time import resolve_capture_time, capture_from_bytes, capture_from_immich, sync_photo_visit
from adventures.services.images.metadata import create_content_image
from adventures.utils.geo import make_point
from users.models import CustomUser


class CaptureTimeTests(SimpleTestCase):
    ny = make_point(-74.006, 40.7128)

    def test_historical_summer_and_winter_offsets(self):
        for date, hour in [('2024-07-10T12:00:00', 16), ('2024-01-10T12:00:00', 17)]:
            result = resolve_capture_time(date, point=self.ny)
            self.assertEqual(result['captured_timezone'], 'America/New_York')
            self.assertEqual(result['captured_at'].hour, hour)

    def test_fall_back_ambiguous_without_offset_keeps_date(self):
        result = resolve_capture_time('2024-11-03T01:30:00', point=self.ny)
        self.assertEqual(result['capture_time_status'], 'ambiguous')
        self.assertIsNone(result['captured_at'])

    def test_explicit_exif_offset_disambiguates_fall_back(self):
        early = resolve_capture_time('2024-11-03T01:30:00', offset='-04:00', point=self.ny)
        late = resolve_capture_time('2024-11-03T01:30:00', offset='-05:00', point=self.ny)
        self.assertEqual((late['captured_at'] - early['captured_at']).total_seconds(), 3600)

    def test_spring_forward_nonexistent_time_is_not_guessed(self):
        self.assertEqual(resolve_capture_time('2024-03-10T02:30:00', point=self.ny)['capture_time_status'], 'invalid_local_time')

    def test_exif_original_and_offset_from_uploaded_file(self):
        exif = Image.Exif(); exif[34665] = {36867: '2024:07:10 12:00:00', 36881: '-04:00'}
        data = io.BytesIO(); Image.new('RGB', (6, 9)).save(data, 'JPEG', exif=exif)
        result = capture_from_bytes(data.getvalue(), point=self.ny)
        self.assertEqual(result['captured_at'], datetime(2024, 7, 10, 16, tzinfo=timezone.utc))

    def test_immich_local_datetime_z_is_not_treated_as_utc(self):
        result = capture_from_immich({'localDateTime': '2024-07-10T12:00:00Z',
            'exifInfo': {'dateTimeOriginal': '2024-07-10T12:00:00Z', 'timeZone': None}}, point=self.ny)
        self.assertEqual(result['captured_at'].hour, 16)

    def test_immich_offset_metadata_preserves_instant(self):
        result = capture_from_immich({'localDateTime': '2024-07-10T12:00:00Z',
            'exifInfo': {'dateTimeOriginal': '2024-07-10T16:00:00+00:00', 'timeZone': 'UTC-4'}}, point=self.ny)
        self.assertEqual(result['captured_local'], '2024-07-10T12:00:00')

    def test_no_original_exif_does_not_use_filesystem_or_upload_date(self):
        self.assertIsNone(capture_from_immich({'fileCreatedAt': '2024-07-10T12:00:00Z'})['captured_at'])
        self.assertEqual(resolve_capture_time('garbage')['capture_time_status'], 'invalid')


class PhotoVisitTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='photo-test', password='unused-test-password')
        self.location = Location.objects.create(user=self.user, name='Photo place', coordinates=make_point(-74.006, 40.7128))
        self.content_type = ContentType.objects.get_for_model(Location)

    def attach(self, local, offset=None):
        image = ContentImage.objects.create(user=self.user, content_type=self.content_type,
            object_id=self.location.id, immich_id='asset', source='immich',
            **resolve_capture_time(local, offset=offset, point=self.location.coordinates))
        sync_photo_visit(image)
        return image

    def test_earliest_photo_updates_one_inferred_visit(self):
        self.attach('2024-07-10T12:00:00'); self.attach('2024-07-10T10:00:00')
        self.assertEqual(self.location.visits.count(), 1)
        visit = self.location.visits.get()
        self.assertEqual(visit.start_date.hour, 14)
        self.assertEqual(visit.start_date, visit.end_date)
        self.assertFalse(visit.date_only)
        self.assertTrue(visit.photo_derived)

    def test_earliest_photo_compares_instants_across_repeated_hour(self):
        self.attach('2024-11-03T01:15:00', offset='-05:00')
        self.attach('2024-11-03T01:45:00', offset='-04:00')
        visit = self.location.visits.get()
        self.assertEqual(visit.start_date, datetime(2024, 11, 3, 5, 45, tzinfo=timezone.utc))
        self.assertEqual(self.location.visits.count(), 1)

    def test_manual_edit_protects_visit_from_later_photos(self):
        self.attach('2024-07-10T12:00:00'); visit = self.location.visits.get()
        serializer = VisitSerializer(visit, data={'date_only': True, 'start_date': '2024-07-09T00:00:00Z', 'end_date': '2024-07-09T00:00:00Z'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors); serializer.save()
        self.attach('2024-07-08T12:00:00');visit.refresh_from_db()
        self.assertFalse(visit.photo_derived)
        self.assertEqual(visit.start_date.day, 9)
        self.assertEqual(self.location.visits.count(), 1)

    def test_ambiguous_photo_creates_only_day(self):
        self.attach('2024-11-03T01:30:00');visit = self.location.visits.get()
        self.assertTrue(visit.date_only);self.assertEqual(visit.start_date.day, 3)

    def test_google_photo_does_not_create_visit(self):
        image = self.attach('2024-07-10T12:00:00');self.location.visits.all().delete()
        image.source = 'google';image.save();sync_photo_visit(image)
        self.assertFalse(self.location.visits.exists())

    def test_copied_immich_preview_reads_original_metadata(self):
        data = io.BytesIO();Image.new('RGB', (6, 9)).save(data, 'JPEG')
        payload = {'localDateTime': '2024-07-10T12:00:00Z', 'exifInfo': {'dateTimeOriginal': '2024-07-10T16:00:00+00:00', 'timeZone': 'UTC-4'}}
        from types import SimpleNamespace
        integration = SimpleNamespace(server_url='https://photos.invalid/api', api_key='test')
        with patch('adventures.services.images.metadata.requests.get') as get:
            get.return_value.json.return_value = payload
            image = create_content_image(user=self.user, content_type=self.content_type, object_id=self.location.id,
                image_file=ContentFile(data.getvalue(), name='preview.jpg'), file_bytes=data.getvalue(),
                metadata_immich_id='asset-id', immich_integration=integration, explicit_source='immich')
        self.assertIsNone(image.immich_id)
        self.assertEqual(image.captured_at.hour, 16)
        self.assertEqual(self.location.visits.count(), 1)

    def test_hidden_imported_rating_and_explicit_manual_rating(self):
        self.location.rating = 4.3;self.location.save()
        self.assertIsNone(LocationListSerializer(self.location).data['rating'])
        request = APIRequestFactory().get('/');request.user = self.user
        self.assertIsNone(LocationSerializer(self.location, context={'request': request}).data['rating'])
        serializer = LocationSerializer(self.location, data={'rating': 4}, partial=True, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors);serializer.save()
        self.assertEqual(serializer.data['rating'], 4)
        serializer = LocationSerializer(self.location, data={'rating': None}, partial=True, context={'request': request})
        self.assertTrue(serializer.is_valid());serializer.save()
        self.assertIsNone(serializer.data['rating'])

    def test_timed_utc_midnight_is_not_normalized_to_all_day(self):
        serializer = VisitSerializer(data={'location': str(self.location.pk), 'start_date':'2024-07-10T00:00:00Z', 'date_only':False, 'timezone':'America/New_York'})
        self.assertTrue(serializer.is_valid(),serializer.errors)
        self.assertFalse(serializer.save().date_only)
