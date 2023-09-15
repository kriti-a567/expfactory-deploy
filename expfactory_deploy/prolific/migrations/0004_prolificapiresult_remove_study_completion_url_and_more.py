# Generated by Django 4.1.3 on 2023-09-01 13:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0038_remove_assignment_prolific_id"),
        ("prolific", "0003_study_rank"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProlificAPIResult",
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
                ("created", models.DateTimeField(auto_now_add=True)),
                ("request", models.TextField(blank=True)),
                ("response", models.JSONField()),
            ],
        ),
        migrations.RemoveField(
            model_name="study",
            name="completion_url",
        ),
        migrations.AddField(
            model_name="study",
            name="completion_code",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="study",
            name="remote_id",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="StudyCollectionSubject",
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
                (
                    "study_collection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="prolific.studycollection",
                    ),
                ),
                (
                    "subject",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="experiments.subject",
                    ),
                ),
            ],
        ),
    ]
