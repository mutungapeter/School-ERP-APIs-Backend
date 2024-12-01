# Generated by Django 5.1 on 2024-11-29 22:45

import django.db.models.deletion
import django.db.models.query
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0003_alter_term_end_date_alter_term_start_date"),
        ("students", "0002_alter_studentsubject_class_level"),
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
