# Generated by Django 5.2 on 2025-05-01 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0009_remove_userlocation_location_userlocation_city_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookModel',
            fields=[
                ('isbn', models.TextField(primary_key=True, serialize=False)),
                ('title', models.TextField(null=True)),
                ('author', models.TextField(null=True)),
                ('publication_year', models.TextField(null=True)),
                ('publisher', models.TextField(null=True)),
                ('image_s', models.TextField(null=True)),
                ('image_m', models.TextField(null=True)),
                ('image_l', models.TextField(null=True)),
            ],
        ),
        migrations.DeleteModel(
            name='Book',
        ),
    ]
