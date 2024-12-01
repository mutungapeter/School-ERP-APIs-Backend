# Generated by Django 5.1 on 2024-11-30 04:34

import django.db.models.deletion
import django.db.models.query
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_remove_term_class_levels_term_class_level"),
        ("students", "0004_alter_studentsubject_class_level"),
    ]

    operations = [
        migrations.AlterField(
            model_name="studentsubject",
            name="class_level",
            field=models.ForeignKey(
                default=django.db.models.query.QuerySet.first,
                on_delete=django.db.models.deletion.CASCADE,
                to="main.classlevel",
            ),
        ),
    ]
