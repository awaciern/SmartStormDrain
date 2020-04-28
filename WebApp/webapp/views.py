from django.shortcuts import render
from datetime import datetime, timedelta
from pytz import timezone
from .models import Device, Transmission, UplinkLog, DownlinkLog
from .forms import SelectionForm, DeviceControllerForm
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseNotFound,\
                        HttpResponseForbidden, HttpResponseServerError
from django.conf import settings
import json
from urllib.parse import unquote
import requests


# Homepage code
def index(request):
    # Create geological locations dict and health dict
    locations = {}
    health = {}

    # Initialize health dict counters
    health['overall'] = 2
    health['healthy'] = 0
    health['flowing'] = 0
    health['clogged'] = 0
    health['offline'] = 0

    for loc in Device.objects.all():
        loc_health = 0  # default health: healthy

        # If the device has no transmissions, it is offline
        if len(Transmission.objects.filter(device=loc)) == 0:
            loc_health = 4  # offline, never been online
            health['offline'] += 1

        # Eventually, there will be logic here to determine health from metrics
        # Right now, I am just assigning them
        if loc.pk == 1:
            loc_health = 0  # healthy
            health['healthy'] += 1
        elif loc.pk == 2:
            loc_health = 1  # collecting water
            health['flowing'] += 1
        elif loc.pk == 3 or loc.pk ==5:
            loc_health = 2  # possibly clogged
            health['clogged'] += 1
        elif loc.pk == 4:
            loc_health = 3  # offline, but has been online before
            health['offline'] += 1
        elif loc_health == 0:
            health['healthy'] += 1

        # Assign values to dict
        locations[loc] = {'latitude': loc.latitude, 'longitude': loc.longitude,
                          'health': loc_health}

    # Initialize empty date dict
    dates = {}

    # If user selects a device/metric/date range, display proper data
    if request.method == 'POST':
        # POST data from python form
        metric = request.POST.get('metric')
        device = Device.objects.get(pk=request.POST.get('device'))

        # If Device Controller was used, make specified changes
        if 'btn2' in request.POST:
            # Change transmission rate if it is different
            rate = request.POST.get('rate')
            if int(rate) != device.transmission_rate:
                # Change in db
                device.transmission_rate = rate
                device.save()

                # Send downlink message to gateway for the change
                if int(rate) == 6:
                    payload = "Ag=="  # 0x02
                elif int(rate) == 12:
                    payload = "Aw=="  # 0x03
                elif int(rate) == 30:
                    payload = "BA=="  # 0x04
                else:
                    payload = "BQ=="  # 0x05
                data = {
                  "dev_id": str(device),
                  "port": 1,
                  "confirmed": False,  # TODO: Ask Alex???
                  "payload_raw": payload
                }
                r = requests.post(settings.DL_URL + settings.DL_KEY, json=data)

                # Log the downlink
                log = DownlinkLog.objects.create(raw_data=data, http_response=r)

            # Turn the power OFF if the user selected it
            if request.POST.get('power') == 'OFF':
                # Send downlink message to gateway to turn power OFF
                data = {
                  "dev_id": str(device),
                  "port": 1,
                  "confirmed": False,  # TODO: Ask Alex???
                  "payload_raw": "AQ=="  # 0x01
                }
                r = requests.post(settings.DL_URL + settings.DL_KEY, json=data)

                # Log the downlink
                log = DownlinkLog.objects.create(raw_data=data, http_response=r)

        # Find the selected device health for display
        device_health = locations[device]['health']

        # If the device has never been online, no need to gather date info
        if device_health != 4:
            # If there is date data from user input
            if request.POST.get('datetimes'):
                # POST date data from JS form requiring processing
                date_list_raw = request.POST.get('datetimes').split('-')
                dates['start_day'] = datetime.strptime(date_list_raw[0],
                                                       '%m/%d/%y %I:%M %p ')\
                                             .replace(tzinfo=timezone('UTC'))\
                                             + timedelta(hours=4)
                dates['end_day'] = datetime.strptime(date_list_raw[1],
                                                     ' %m/%d/%y %I:%M %p')\
                                           .replace(tzinfo=timezone('UTC'))\
                                           + timedelta(hours=4)

                # Find max and min transmission dates based on device selected
                dates['max_day'] = Transmission.objects.filter(device=device)\
                                               .order_by('-timestamp')[0]\
                                               .timestamp
                dates['min_day'] = Transmission.objects.filter(device=device)\
                                               .order_by('timestamp')[0]\
                                               .timestamp

                # Start date is past last transission -> display most recent day data
                if dates['start_day'] > dates['max_day']:  # message???
                    dates['end_day'] = Transmission.objects\
                                                   .filter(device=device)\
                                                   .order_by('-timestamp')[0]\
                                                   .timestamp
                    eastern_date = dates['end_day'] - timedelta(hours=4)
                    dates['start_day'] = datetime(eastern_date.year,
                                                  eastern_date.month,
                                                  eastern_date.day,
                                                  tzinfo=timezone('UTC'))\
                                                  + timedelta(hours=4)

                # End date is before first transission -> display most recent day data
                if dates['end_day'] < dates['min_day']:  # message???
                    dates['end_day'] = Transmission.objects\
                                                   .filter(device=device)\
                                                   .order_by('-timestamp')[0]\
                                                   .timestamp
                    eastern_date = dates['end_day'] - timedelta(hours=4)
                    dates['start_day'] = datetime(eastern_date.year,
                                                  eastern_date.month,
                                                  eastern_date.day,
                                                  tzinfo=timezone('UTC'))\
                                                  + timedelta(hours=4)

            # If there is NOT date data from user input
            else:
                # Initially set date range of most recent day's data
                dates['end_day'] = Transmission.objects.filter(device=device)\
                                               .order_by('-timestamp')[0]\
                                               .timestamp
                eastern_date = dates['end_day'] - timedelta(hours=4)
                dates['start_day'] = datetime(eastern_date.year,
                                              eastern_date.month,
                                              eastern_date.day,
                                              tzinfo=timezone('UTC'))\
                                              + timedelta(hours=4)
                # Find min transmission dates based on device selected
                dates['max_day'] = Transmission.objects.filter(device=device)\
                                               .order_by('-timestamp')[0]\
                                               .timestamp
                dates['min_day'] = Transmission.objects.filter(device=device)\
                                               .order_by('timestamp')[0]\
                                               .timestamp

    # User has not yet submitted data; is initially visiting the page
    else:
        # Initially select water depth of first device in db
        metric = 'depth'
        device = Device.objects.first()

        # Find the selected device health for display
        device_health = locations[device]['health']

        # If the device has never been online, no need to gather date info
        if device_health != 4:
            # Initially set date range of most recent day's data
            dates['end_day'] = Transmission.objects.filter(device=device)\
                                                   .last().timestamp
            eastern_date = dates['end_day'] - timedelta(hours=4)
            dates['start_day'] = datetime(eastern_date.year,
                                          eastern_date.month,
                                          eastern_date.day,
                                          tzinfo=timezone('UTC'))\
                                          + timedelta(hours=4)

            # Find min transmission dates based on device selected
            dates['max_day'] = Transmission.objects.filter(device=device)\
                                           .order_by('-timestamp')[0].timestamp
            dates['min_day'] = Transmission.objects.filter(device=device)\
                                           .order_by('timestamp')[0].timestamp

    # Create the forms the user will see
    form1 = SelectionForm(initial = {'device': device, 'metric': metric})
    if device_health == 3 or device_health == 4:  # device is offline
        device_power = 'OFF'  # so its power is OFF
    else:  # device is online
        device_power = 'ON'  # so its power is ON
    form2 = DeviceControllerForm(initial = {'power': device_power,
                                            'rate': device.transmission_rate})

    # Get the transimssion (if any) data for display from db based on date range
    if device_health != 4:
        transmissions = Transmission.objects.filter(device=device,
                                                    timestamp__range=
                                                    (dates['start_day'],
                                                    dates['end_day']))
        # Change possible clog flowrate from 0 to -1 so it will show up on the graph
        for transmission in transmissions:
            if transmission.flowrate == 0:
                transmission.flowrate = -1
    else:
        transmissions = []

    print(dates)
    # Render the html template and pass in the required data
    return render(request, 'index.html', {'form1': form1,
                                          'form2': form2,
                                          'locations': locations,
                                          'health': health,
                                          'metric': metric,
                                          'device': device,
                                          'device_health': device_health,
                                          'dates': dates,
                                          'transmissions': transmissions,
                                          'authenticated': request.user.is_staff})


# Gateway Endpoint code
@csrf_exempt
def gateway(request):
    # This URL will be hit with POST data from the gateway and store it in db
    if request.method == 'POST':
        # Try, Except block to handle any Exceptions that might be raised here
        try:
            # Get the raw data from the request and log it
            raw_data = unquote(request.body.decode('utf-8'))
            #raw_data = raw_data.replace('+', '').replace('request=', '')
            log = UplinkLog.objects.create(raw_data=raw_data, message='')

            # Turn the raw data into JSON
            req_dict = json.loads(raw_data)

            # Check the downlink_url for the "password"
            if 'downlink_url' not in req_dict:
                # No authentication credentails provided
                log.message = 'Authentication Failure'
                log.save()
                return HttpResponseForbidden('Authentication Failure')
            if settings.DL_URL in req_dict['downlink_url']:
                # Get the device id if available
                if 'dev_id' not in req_dict:
                    # No device identified
                    log.message = 'ERROR: No device identified!'
                    log.save()
                    return HttpResponse('ERROR: No device identified!')

                # Check if the device id matches a device in the db
                device_list = []
                for device in Device.objects.all():
                    device_list.append(device.name)
                if req_dict['dev_id'] in device_list:
                    # Get the device from the database
                    device = Device.objects.get(name=req_dict['dev_id'])

                    # Check if the POST data has needed payload fields
                    if 'payload_fields' not in req_dict:
                        # No payload fields in the request
                        log.message = 'ERROR: Data has no payload fields!'
                        log.save()
                        return HttpResponse('ERROR: Data has no payload fields!')
                    payload_dict = req_dict['payload_fields']
                    if 'distance_inches' not in payload_dict or \
                       'flowrate' not in payload_dict or \
                       'voltage' not in payload_dict:
                        # Needed fields not present in payload fields
                        log.message = 'ERROR: Data lacks needed payload fields!'
                        log.save()
                        return HttpResponse('ERROR: Data lacks needed payload fields!')

                    # Check if the POST data has needed metadata
                    if 'metadata' not in req_dict:
                        # No metadata in the request
                        log.message = 'ERROR: Data has no metadata!'
                        log.save()
                        return HttpResponse('ERROR: Data has no metadata!')
                    metadata_dict = req_dict['metadata']
                    if 'time' not in metadata_dict:
                        # Needed time field not in metadata
                        log.message = 'ERROR: Data lacks needed metadata!'
                        log.save()
                        return HttpResponse('ERROR: Data lacks needed metadata!')

                    # POST data is good -> store transission in db
                    Transmission.objects.create(timestamp=metadata_dict['time'],
                                                device=device,
                                                depth=payload_dict['distance_inches'],
                                                flowrate=payload_dict['flowrate'],
                                                voltage=payload_dict['voltage'])

                    # Return success message
                    log.message = 'SUCCESS: Transmission recieved and stored'
                    log.save()
                    return HttpResponse('SUCCESS: Transmission recieved and stored')

                # If no device match stop and return error message
                else:
                    log.message = 'ERROR: Device ID is not recognized!'
                    log.save()
                    return HttpResponse('ERROR: Device ID is not recognized!')

            # If incorrect authentication stop and return error message
            else:
                log.message = 'Authentication Failure'
                log.save()
                return HttpResponseForbidden('Authentication Failure')

        # If Exception occurred during execution, log it and return server error
        except Exception as e:
            log.message = 'EXCEPTION THROWN:\n' + str(e)
            log.save()
            return HttpResponseServerError(str(e))

    # Only POST methods can hit this URL
    else:
        return HttpResponseNotFound()
