# Generated by Django 2.2.28 on 2024-02-12 09:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('consumers', '0002_consumer_stripe_account'),
        ('dropdowns', '0001_initial'),
        ('contributors', '0002_auto_20240212_0904'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_for', models.CharField(blank=True, max_length=255)),
                ('introduce_yourself', models.TextField(blank=True)),
                ('video_to_say', models.TextField(blank=True)),
                ('turnaround_selected', models.CharField(choices=[('Normal', 'Normal'), ('Fast', 'Fast'), ('Same Day', 'Same Day')], default='Normal', max_length=255)),
                ('video_fee', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('booking_fee', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Delivered', 'Delivered'), ('Redo Requested', 'Redo Requested'), ('Redone', 'Redone'), ('Refund Requested', 'Refund Requested'), ('Refunded', 'Refunded'), ('Cancel Requested', 'Cancel Requested'), ('Cancelled', 'Cancelled')], default='Pending', max_length=255)),
                ('consumer_charge_id', models.CharField(blank=True, max_length=255, null=True)),
                ('blessn', models.FileField(blank=True, null=True, upload_to='blessn_files/videos')),
                ('cancel_requested_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('redo_requested_at', models.DateTimeField(blank=True, null=True)),
                ('redone_at', models.DateTimeField(blank=True, null=True)),
                ('refund_requested_at', models.DateTimeField(blank=True, null=True)),
                ('refunded_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('archived', models.BooleanField(default=False)),
                ('reviewed', models.BooleanField(default=False)),
                ('rating', models.IntegerField(default=0)),
                ('consumer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='consumers.Consumer')),
                ('contributor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='contributors.Contributor')),
                ('occasion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='dropdowns.Occasion')),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('consumer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews', to='consumers.Consumer')),
                ('contributor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews', to='contributors.Contributor')),
                ('order', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review', to='orders.Order')),
            ],
        ),
    ]
