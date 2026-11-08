from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('adventures', '0077_photo_visits_and_manual_ratings')]
    operations = [migrations.AddField('visit', 'itinerary_date', models.DateField(null=True, blank=True))]
