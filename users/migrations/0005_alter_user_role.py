# Generated by Django 5.0.1 on 2025-02-21 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_role_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('ADMIN', 'Administrator'), ('DOCTOR', 'Doctor'), ('PATIENT', 'Patient'), ('STAFF', 'Staff'), ('RECEPTIONIST', 'Receptionist')], default='PATIENT', max_length=20),
        ),
    ]
