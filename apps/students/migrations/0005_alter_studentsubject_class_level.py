# Generated by Django 5.1 on 2024-12-26 23:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_rename_max_mean_marks_meangradeconfig_max_mean_points_and_more'),
        ('students', '0004_alter_studentsubject_class_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentsubject',
            name='class_level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.classlevel'),
        ),
    ]
