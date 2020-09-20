# Generated by Django 3.0.7 on 2020-08-23 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0006_auto_20200823_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='last_match_number',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='last_time_searched',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='zero_matches_number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]