# Generated by Django 3.2.6 on 2021-09-03 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_alter_category_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='products', verbose_name='image'),
        ),
    ]
