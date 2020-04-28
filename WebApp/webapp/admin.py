from django.contrib import admin
from .models import Device, Transmission, UplinkLog, DownlinkLog


class DeviceAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(Device, DeviceAdmin)


class TransmissionAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'device', 'depth', 'flowrate', 'voltage']

admin.site.register(Transmission, TransmissionAdmin)


class UplinkLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'message', 'raw_data']

admin.site.register(UplinkLog, UplinkLogAdmin)


class DownlinkLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'http_response', 'raw_data']

admin.site.register(DownlinkLog, DownlinkLogAdmin)
