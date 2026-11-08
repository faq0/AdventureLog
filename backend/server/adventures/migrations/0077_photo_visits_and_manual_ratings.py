from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('adventures', '0076_normalize_all_day_visit_end_dates')]
    operations = [
        migrations.AddField('location', 'rating_is_manual', models.BooleanField(default=False)),
        migrations.AddField('visit', 'date_only', models.BooleanField(null=True, blank=True, default=None)),
        migrations.AddField('visit', 'photo_derived', models.BooleanField(default=False)),
        migrations.AddField('contentimage', 'captured_at', models.DateTimeField(null=True, blank=True)),
        migrations.AddField('contentimage', 'captured_local', models.CharField(max_length=40, null=True, blank=True)),
        migrations.AddField('contentimage', 'captured_timezone', models.CharField(max_length=64, null=True, blank=True)),
        migrations.AddField('contentimage', 'capture_time_status', models.CharField(max_length=24, blank=True, default='missing')),
    ]
