# Generated by Django 2.2.3 on 2019-07-15 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='visible',
            field=models.BooleanField(default=True),
        ),
    ]