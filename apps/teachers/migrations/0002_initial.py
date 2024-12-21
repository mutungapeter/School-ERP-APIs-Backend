# Generated by Django 5.1 on 2024-12-21 09:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('main', '0001_initial'),
        ('teachers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='user',
            field=models.OneToOneField(limit_choices_to={'role': 'Teacher'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='teachersubject',
            name='class_level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.classlevel'),
        ),
        migrations.AddField(
            model_name='teachersubject',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.subject'),
        ),
        migrations.AddField(
            model_name='teachersubject',
            name='teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachersubject_set', to='teachers.teacher'),
        ),
        migrations.AlterUniqueTogether(
            name='teachersubject',
            unique_together={('teacher', 'subject', 'class_level')},
        ),
    ]
