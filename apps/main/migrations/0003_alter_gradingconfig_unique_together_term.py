# Generated by Django 5.1 on 2024-10-08 00:52

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_subject_class_levels"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="gradingconfig",
            unique_together={("grade", "subject_category")},
        ),
        migrations.CreateModel(
            name="Term",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "term",
                    models.CharField(
                        choices=[
                            ("Term 1", "Term 1"),
                            ("Term 2", "Term 2"),
                            ("Term 3", "Term 3"),
                        ],
                        max_length=10,
                    ),
                ),
                ("calendar_year", models.IntegerField()),
            ],
            options={
                "unique_together": {("term", "calendar_year")},
            },
        ),
    ]
