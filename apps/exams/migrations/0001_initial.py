# Generated by Django 5.1 on 2024-11-29 00:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("main", "0001_initial"),
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MarksData",
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
                ("cat_mark", models.FloatField()),
                ("exam_mark", models.FloatField()),
                ("total_score", models.FloatField(editable=False)),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="students.student",
                    ),
                ),
                (
                    "student_subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="students.studentsubject",
                    ),
                ),
                (
                    "term",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="main.term",
                    ),
                ),
            ],
            options={
                "unique_together": {("student", "student_subject", "term")},
            },
        ),
    ]
