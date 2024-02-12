# Generated by Django 2.2.28 on 2024-02-12 09:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('djstripe', '0008_2_5'),
        ('contributors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contributor',
            name='connect_account',
            field=models.ForeignKey(blank=True, help_text="The Contributor's Stripe Connect Account object, if it exists", null=True, on_delete=django.db.models.deletion.SET_NULL, to='djstripe.Account'),
        ),
        migrations.AddField(
            model_name='contributor',
            name='fast_delivery_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='contributor',
            name='normal_delivery_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='contributor',
            name='same_day_delivery_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
