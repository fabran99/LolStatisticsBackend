# Generated by Django 3.0.7 on 2020-08-23 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0007_auto_20200823_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ban',
            name='tier',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='ban',
            name='timestamp',
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='champdata',
            name='tier',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='champdata',
            name='timestamp',
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='champplaystyle',
            name='tier',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='champplaystyle',
            name='timestamp',
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='firstbuy',
            name='tier',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='firstbuy',
            name='timestamp',
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='server',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='skillup',
            name='tier',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='skillup',
            name='timestamp',
            field=models.BigIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='timeline',
            name='gameTimestamp',
            field=models.BigIntegerField(db_index=True),
        ),
    ]
