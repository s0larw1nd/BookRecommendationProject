# Generated by Django 5.2 on 2025-05-01 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_remove_book_id_alter_book_isbn'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='author',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='image_l',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='image_m',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='image_s',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='publication_year',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='publisher',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='book',
            name='title',
            field=models.TextField(null=True),
        ),
    ]
