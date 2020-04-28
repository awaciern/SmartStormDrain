from datetime import datetime, timedelta
from random import random
from webapp.models import Device, Transmission


'''
To run this script, open the server shell and run the following command:
exec(open('sim_data/2_simulate.py').read())
NOTE: The simulated data will be associated with the device specified by pk
'''

# Device we are assigining this data to
device = Device.objects.get(pk=2)

# Starting date for simulated data
date = datetime(2020, 4, 13, 0, 0)
depth = 0.0
flowrate = 1
voltage = 3.95

# Loop until specified date
while date < datetime(2020, 4, 21):
    print('{0} - flowrate = {1}, depth = {2}, voltage={3}'
          .format(date, flowrate, depth, voltage))

    # Store the transmission in the database
    Transmission.objects.create(timestamp=date, device=device, depth=depth,
                                flowrate=flowrate, voltage=voltage)

    # Transission interval increment
    date = date + timedelta(minutes=12)

    # Decrease battery linearly
    voltage -= 0.0002

    # During the last hour, start raining
    if date > datetime(2020, 4, 20, 23):
        flowrate = 2
        depth += 1.0

    # Otherwise, normal weather progression
    else:
        # Generate random event for the weather
        rand = random()

        # 0.02 chance it starts raining
        if flowrate == 1 and rand > 0.99:
                flowrate = 2

        # 0.25 chance it stops raining if it is raining
        if flowrate == 2 and rand < 0.25:
            flowrate = 1

        # How water depth changes based on the flow rate (floods at 6 ft [72 inches])
        if depth < 72:
            if flowrate == 1 and depth > 0.1:
                depth -= 0.1
            if flowrate == 2:
                depth += 1.0
