# Generated by Django 3.0.7 on 2020-08-23 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puuid', models.CharField(max_length=100)),
                ('accountId', models.CharField(max_length=100)),
                ('summonerId', models.CharField(max_length=100)),
                ('summonerName', models.CharField(max_length=100)),
                ('inactive', models.BooleanField()),
                ('server', models.CharField(max_length=50)),
                ('tier', models.CharField(max_length=50)),
                ('rank', models.CharField(max_length=50)),
                ('last_time_searched', models.IntegerField()),
                ('zero_matches_number', models.IntegerField()),
                ('last_match_number', models.IntegerField()),
            ],
        ),
    ]
