# Generated by Django 3.2.6 on 2021-09-08 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0002_auto_20210904_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='entries',
            field=models.ManyToManyField(to='carts.Entry', verbose_name='entries'),
        ),
        migrations.AlterField(
            model_name='entry',
            name='quantity',
            field=models.PositiveIntegerField(default=0, verbose_name='quantity'),
        ),
    ]
