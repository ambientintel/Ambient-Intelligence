import serial 

comport = input("Enter the COM port: ")

ser = serial.Serial(comport, 921600)

while True:
    bytecount = ser.inWaiting()
    s = ser.read(bytecount)
    print(s)

