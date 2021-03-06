# Generated by Django 2.1.14 on 2020-01-14 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Transmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('depth', models.FloatField()),
                ('flowrate', models.IntegerField(choices=[(0, 'None'), (1, 'Low'), (2, 'Medium'), (3, 'High')])),
            ],
        ),
        migrations.DeleteModel(
            name='Message',
        ),
        migrations.AddField(
            model_name='device',
            name='transmissions',
            field=models.ManyToManyField(to='webapp.Transmission'),
        ),
    ]
