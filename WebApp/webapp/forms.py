from django import forms
from .models import Device, Transmission


class SelectionForm(forms.ModelForm):
    # Dropdown menu listing devices
    device = forms.ModelChoiceField(queryset=Device.objects.all(),
                                    empty_label=None)

    # Select button for display metrics
    METRICS = [('depth', 'Water Depth'),
               ('flowrate', 'Flow Rate'),
               ('voltage', 'Battery Voltage')]
    metric = forms.ChoiceField(choices=METRICS, widget=forms.Select)

    class Meta:
        model = Device
        fields = ()


class DeviceControllerForm(forms.Form):
    # Choose between ON and OFF
    power = forms.ChoiceField(choices=[('ON', 'ON'), ('OFF', 'OFF')])

    # Choose between the four available transmission rates
    RATES = [(6, '6 minutes'),
             (12, '12 minutes'),
             (30, '30 minutes'),
             (60, '1 hour')]
    rate = forms.ChoiceField(choices=RATES)
