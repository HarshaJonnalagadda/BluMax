# Generated by Django 5.0.1 on 2025-02-25 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('ADMIN', 'Administrator'), ('DOCTOR', 'Doctor'), ('PATIENT', 'Patient'), ('STAFF', 'Staff'), ('RECEPTIONIST', 'Receptionist'), ('NURSE', 'Nurse'), ('LAB_TECHNICIAN', 'Lab Technician'), ('PHARMACIST', 'Pharmacist')], default='PATIENT', max_length=20),
        ),
    ]
