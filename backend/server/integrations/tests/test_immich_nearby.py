from types import SimpleNamespace
from unittest.mock import patch
from django.core.cache import cache
from django.test import TestCase, SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from adventures.models import Location
from adventures.utils.geo import make_point
from integrations.models import ImmichIntegration
from integrations.immich_nearby import nearby_assets, distance_meters
from integrations.views.immich_view import ImmichIntegrationView
from users.models import CustomUser

class NearbyIndexTests(SimpleTestCase):
    def test_haversine_crosses_dateline_correctly(self):
        self.assertLess(distance_meters(0, 179.999, 0, -179.999), 225)

    @patch('integrations.immich_nearby.requests.post')
    @patch('integrations.immich_nearby.requests.get')
    def test_index_cached_and_results_recheck_visibility(self, get, post):
        cache.clear()
        integration = SimpleNamespace(pk='test-integration', server_url='https://photos.invalid/api', api_key='test')
        get.return_value.__enter__.return_value.iter_content.return_value = [b'[{"id":"near", "lat":0.0001,"lon":0},{"id":"far","lat":1,"lon":1}]']
        post.return_value.json.return_value = {'assets': {'items':[{'id':'near','localDateTime':'2024-01-01T12:00:00Z'}]}}
        results, more = nearby_assets(integration, 0, 0, 500, 1)
        self.assertEqual([x['id'] for x in results], ['near']);self.assertFalse(more)
        self.assertLess(results[0]['distance_meters'], 20)
        # A cached GPS marker can have moved to trash/locked since the last search.
        post.return_value.json.return_value = {'assets': {'items':[]}}
        self.assertEqual(nearby_assets(integration, 0, 0, 500, 1)[0], [])
        self.assertEqual(get.call_count, 1)
        filters = post.call_args.kwargs['json']['filter']
        self.assertEqual(filters['visibility']['in'], ['timeline','archive'])
        self.assertEqual(filters['trashedAt'], {'eq':None})
        self.assertEqual(filters['type'], {'eq':'IMAGE'})

class NearbyPermissionTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(username='nearby-owner')
        self.other = CustomUser.objects.create_user(username='nearby-other')
        self.location = Location.objects.create(user=self.owner, name='Private place', coordinates=make_point(0,0))
        ImmichIntegration.objects.create(user=self.other, server_url='https://photos.invalid/api', api_key='test')
        self.factory = APIRequestFactory()
        self.view = ImmichIntegrationView.as_view({'get':'nearby'})

    @patch('integrations.immich_nearby.nearby_assets')
    def test_other_users_location_is_denied_before_immich_request(self, search):
        request = self.factory.get('/nearby/', {'object_id':str(self.location.pk)})
        force_authenticate(request,self.other)
        self.assertEqual(self.view(request).status_code,403)
        search.assert_not_called()

    @patch('integrations.immich_nearby.nearby_assets')
    def test_invalid_radius_is_denied_before_immich_request(self, search):
        ImmichIntegration.objects.create(user=self.owner,server_url='https://photos.invalid/api',api_key='test')
        for radius in ['nan','inf','0','10000','bad']:
            request=self.factory.get('/nearby/',{'object_id':str(self.location.pk),'radius':radius})
            force_authenticate(request,self.owner)
            self.assertEqual(self.view(request).status_code,400)
        search.assert_not_called()
