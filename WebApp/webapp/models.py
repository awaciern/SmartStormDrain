from django.db import models
from django.utils import timezone


class Device(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    RATES = [(6, '6 minutes'),
             (12, '12 minutes'),
             (30, '30 minutes'),
             (60, '60 minutes')]
    transmission_rate = models.IntegerField(choices=RATES)

    def __str__(self):
        return self.name


class Transmission(models.Model):
    LEVELS = (
        (0, 'Posible Clog'),
        (1, 'Normal'),
        (2, 'High'),
    )
    timestamp = models.DateTimeField()
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    depth = models.FloatField()
    flowrate = models.IntegerField(choices=LEVELS)
    voltage = models.FloatField()

    def __str__(self):
        return '{0} at {1}'.format(self.device, self.timestamp)


class UplinkLog(models.Model):
    raw_data = models.TextField()
    message = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)


class DownlinkLog(models.Model):
    raw_data = models.TextField()
    http_response = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
