# SmartStormDrain

This is all the code used to developed the Smart Storm Drain project. It is broken down into the **EmbeddedCode** folder, which contains the code used to control operation of the LoPy microncontroller on the Smart Strom Drain devices, the **Communications** folder which contains the code used to transmit and receive data via LoRaWAN OTAA Protocols to the Webapp, and the **WebApp** folder, which contains the code used to generate the Smart Storm Drain web appilcation.

## Communications
The key files in this folder are located in the **lib** folder. Here you will find a main.py function which is the code you upload to your LoPy4 expansion board using the PyMakr applet via Atom. The files outside of **lib** are main codes you must copy into the main.py file based on what you want your device to do. LoPy_Ring and LoPy_No_Ring code are identical except for the lines where OTAA Authentication parameters are defined. These parameters vary for each LoPy node you use and are defined by our application on TheThingsNetwork.org.


## EmbeddedCode

The embedded code used for microcontroller and sensor operation in this project can be found under EmbeddedCode/Final Embedded Design/ Code. Embedded_Sensor_Ops_Code.py is the primary file that contains all sensor initializations and functions relating to interfacing and using the (2) JSN-SR04T ultrasonic distance sensors and the (1) Sparkfun Sound Detector. This file is accompanied by the tsl2591.py interface file, which enables the functionality of the (1) TSL2591 ambient light sensor. These files provide the ability to collect data for the system, but do not transmit any data. In order to transmit data, bring the functions and initializations from these files into the LoPy_Ring / LoPy_No_Ring code and integrate the sensing functions to fit the implementation of making the payload.

## WebApp

The web application was built using the Django Python web framework and was hosted via Microsoft Azure Cloud Hosting services. The README file in this folder gives more detail on the code in this folder. Note that this code is copied from another public GitHub repository that connects to the Microsoft Azure web application deployment, which is available at the following link: https://github.com/awaciern/smart-storm-drain.
