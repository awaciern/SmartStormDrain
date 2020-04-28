# smart-storm-drain

This is the code used to generate the web application for the Smart Storm Drain project. It was built using the Django Python web framework and was hosted via Microsoft Azure Cloud Hosting services. 

## smart_storm_drain folder

This folder contains files vital to the setup of the overall website, such as `settings.py` which specifies site settings and `urls.py` which registers the different URLs of the site.

## webapp folder

This folder contains files that specify how the Smart Storm Drain web application is set up and functions.
* `views.py` contains the core functionality of the web application
* `models.py` specifies the database objects and their fields
* `forms.py` creates the forms the users intract with on the website
* `admin.py` configres what Admin users see in the Django Admin
* `templates` contains the html webpage code that users see
  * `index.html` contains all the code for the Webpage GUI, including the code for the JavaScript apps
* `static` contains all CSS stylings, images, and JavaScript libraries used on the site

## sim_data folder

This folder contains the Python scripts used to generate simulated data for Test Devices on the website.

## requirements.txt

This file specifies all the Python libraries that need to be installed for the web application to function.
