import datastream
from datastream import UARTParser

class core:
    def __init__(self):

        self.parser = UARTParser(type="DoubleCOMPort")



if __name__=="__main__":

    cliCom = input("Enter the CLI COM port: ")
    dataCom = input("Enter the Data COM port: ")

    c = core()
    c.parser.connectComPorts(cliCom, dataCom)

    print(c.parser.dataCom)