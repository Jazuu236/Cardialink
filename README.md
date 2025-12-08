Cardialink Heart rate meter

Components used:
- Rasberry Pi Pico W
- Crowtail Pulse sensor (photoplethysmography - PPG)
- SSD1306 OLED Display
- Rotary encoder

![image0 (29)](https://github.com/user-attachments/assets/e54de8fd-adca-4440-b93c-01c61ee1594e)
![image1 (24)](https://github.com/user-attachments/assets/d22c501a-6f0d-4302-bc62-55147a9c2d9e)
![image3 (2)](https://github.com/user-attachments/assets/4e5dbe9f-e778-4276-950f-f0a60f4c5374)
![image4 (1)](https://github.com/user-attachments/assets/96151952-b220-4fc1-b6fb-a285127cb0e2)
![image5 (1)](https://github.com/user-attachments/assets/d621d639-bf0c-40bc-b962-f59c973583b9)









Operating principle

The Crowtail optical sensor is used to detect the heart rate as an analog signal and transmits it to the Raspberry Pico Pi W. The analog signal is then converted into digital by the AD-converter of the microcontroller and using peak-detection algorithms, the device is capable of measuring the peak-to-peak interval (PPI) of the heart signal.

Using the gathered data, the mean peak-to-peak interval (PPI), mean heart rate (HR), standard deviation of successive interval differences (SDNN), root mean square of successive differences (RMSSD) and Poincare plot shape parameters (SD1, SD2) are each analysised with their own algorithms.

The collected peak-to-peak interval data is also transmitted from the Rasberry Pi Pico W wirelessly to the Kubios Cloud Service, where the data is further analysed to for the recovery and stress indexes. The outcome of this analysis is then returned to the device and the results are shown through the OLED display for the user along with the locally calculated data.

During the measurement, the rotary knob functions as the controller for this operation, that provides the user interaction for the hardware. The user can choose the activity based on to the information displayed on the OLED, such as starting the measurment, checking users measurment history or accessing settings.


ASM chart:

<img width="1190" height="1280" alt="Cardialink ASM chart" src="https://github.com/user-attachments/assets/df14b0eb-840e-4c22-8279-d7826541e80c" />





