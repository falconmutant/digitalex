# Generated by Django 2.2.3 on 2019-08-06 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20190725_0926'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='created',
            field=models.DateField(auto_now_add=True),
        ),
    ]
