from rest_framework.test import APITestCase

from adventures.models import Collection, CollectionItineraryItem, Location
from users.models import CustomUser


class ItineraryAPITestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='itinerary-user',
            email='itinerary-user@example.com',
            password='testpassword123',
        )
        self.collection = Collection.objects.create(user=self.user, name='Test Trip')
        self.location = Location.objects.create(user=self.user, name='Test Location', is_public=True)
        self.client.force_authenticate(user=self.user)

    def test_create_global_itinerary_item_without_date(self):
        response = self.client.post(
            '/api/itineraries/',
            {
                'collection': str(self.collection.id),
                'content_type': 'location',
                'object_id': str(self.location.id),
                'is_global': True,
                'order': 0,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(CollectionItineraryItem.objects.count(), 1)

        item = CollectionItineraryItem.objects.get()
        self.assertTrue(item.is_global)
        self.assertIsNone(item.date)
        self.assertEqual(item.collection, self.collection)

        payload = response.json()
        self.assertTrue(payload['is_global'])
        self.assertIsNone(payload['date'])
        self.assertEqual(payload['content_type'], 'location')
        self.assertEqual(payload['object_name'], 'location')
        self.assertEqual(payload['item']['type'], 'location')

    def test_collection_retrieve_serializes_itinerary_content_type_as_model_name(self):
        self.collection.locations.add(self.location)
        create_response = self.client.post(
            '/api/itineraries/',
            {
                'collection': str(self.collection.id),
                'content_type': 'location',
                'object_id': str(self.location.id),
                'is_global': True,
                'order': 0,
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, 201)

        response = self.client.get(f'/api/collections/{self.collection.id}/')
        self.assertEqual(response.status_code, 200)

        itinerary = response.json()['itinerary']
        self.assertEqual(len(itinerary), 1)
        self.assertEqual(itinerary[0]['content_type'], 'location')
        self.assertEqual(itinerary[0]['object_name'], 'location')
        self.assertEqual(itinerary[0]['object_id'], str(self.location.id))
    def test_adding_inferred_visit_to_day_uses_matching_photo_time(self):
        from django.contrib.contenttypes.models import ContentType
        from adventures.models import ContentImage
        from adventures.utils.geo import make_point
        from adventures.services.images.capture_time import resolve_capture_time, sync_photo_visit
        from datetime import datetime, timezone
        self.location.coordinates = make_point(-74.006,40.7128)
        self.location.save()
        image = ContentImage.objects.create(user=self.user,content_type=ContentType.objects.get_for_model(Location),object_id=self.location.pk,immich_id='asset',source='immich',**resolve_capture_time('2024-07-10T10:00:00',point=self.location.coordinates))
        sync_photo_visit(image)
        visit = self.location.visits.get()
        response = self.client.post('/api/itineraries/', {'collection':str(self.collection.pk),'content_type':'location','object_id':str(self.location.pk),'date':'2024-07-10','is_global':False,'order':0,'update_item_date':True,'source_visit_id':str(visit.pk)},format='json')
        self.assertEqual(response.status_code,201,response.data)
        visit.refresh_from_db()
        self.assertEqual(visit.start_date,datetime(2024,7,10,14,tzinfo=timezone.utc))
        self.assertFalse(visit.date_only)
        self.assertEqual(visit.itinerary_date.isoformat(),'2024-07-10')
        self.assertEqual(response.data['updated_object']['visits'][0]['start_date'],'2024-07-10T14:00:00Z')
        self.assertEqual(self.location.visits.count(),1)
