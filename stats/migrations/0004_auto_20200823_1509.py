# Generated by Django 3.0.7 on 2020-08-23 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0003_auto_20200823_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ban',
            name='gameId',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='ban',
            name='timestamp',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='champdata',
            name='gameId',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='champdata',
            name='timestamp',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='champplaystyle',
            name='timestamp',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='firstbuy',
            name='timestamp',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='player',
            name='last_time_searched',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='skillup',
            name='timestamp',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='timeline',
            name='gameTimestamp',
            field=models.BigIntegerField(),
        ),
    ]
