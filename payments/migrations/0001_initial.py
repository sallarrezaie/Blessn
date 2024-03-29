# Generated by Django 2.2.28 on 2024-02-12 09:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('consumers', '0002_consumer_stripe_account'),
        ('djstripe', '0008_2_5'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('charge_id', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('refunded', models.BooleanField(default=False)),
                ('consumer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='consumers.Consumer')),
                ('consumer_payment_intent', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='djstripe.PaymentIntent')),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='orders.Order')),
                ('payment_method', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='djstripe.PaymentMethod')),
            ],
        ),
    ]
