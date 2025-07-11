# Generated by Django 5.2.3 on 2025-06-29 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offers_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='offerdetail',
            name='delivery_time_in_days',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='offerdetail',
            name='features',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='offerdetail',
            name='offer_type',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='offerdetail',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='offerdetail',
            name='revisions',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='offerdetail',
            name='title',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='offer',
            name='min_delivery_time',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='offer',
            name='min_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='offerdetail',
            name='url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
