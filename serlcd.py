# Serial LCD library
import serial
from time import sleep
import timeit

# debug?
debug_active = False

# Init Commands
LCD_SEND_COMMAND = '\xFE'
LCD_SEND_SPECIAL = '\x7C'

# Commands
LCD_BACKLIGHT = '\x80'
LCD_CLEARDISPLAY = '\x01'
LCD_CURSORSHIFT = '\x10'
LCD_DISPLAYCONTROL = '\x08'
LCD_ENTRYMODESET = '\x04'
LCD_FUNCTIONSET = '\x20'
LCD_SETCGRAMADDR = '\x40'
LCD_SETDDRAMADDR = '\x80'
LCD_SETSPLASHSCREEN = '\x0A'
LCD_SPLASHTOGGLE = '\x09'
LCD_RETURNHOME = '\x02'

# Flags for display entry mode
LCD_ENTRYRIGHT = '\x00'
LCD_ENTRYLEFT = '\x02'

# Flags for display on/off control
LCD_BLINKON = '\x01'
LCD_CURSORON = '\x02'
LCD_DISPLAYON = '\x04'

# Flags for display size
LCD_2LINE = '\x02'
LCD_4LINE = '\x04'
LCD_16CHAR = '\x10'
LCD_20CHAR = '\x14'

#  Flags for setting display size
LCD_SET2LINE = '\x06'
LCD_SET4LINE = '\x05'
LCD_SET16CHAR = '\x04'
LCD_SET20CHAR = '\x03'

LCD_BAUD9600 = '\x0D'

def debug(msg):
    if debug_active:
        date = timeit.default_timer()
        print(str(date) + ": " + msg)


class SerLCD(object):

    def __init__(self):
        debug('Initializing Display')
        self.lcd = serial.Serial(port='/dev/ttyAMA0',baudrate=9600)

        # tell the display what it is...
        self.special(LCD_SET4LINE)
        sleep(0.01)
        self.special(LCD_SET20CHAR)
        sleep(0.01)

        # set default baud
        self.special(LCD_BAUD9600)
        sleep(0.01)

        self.clear()

    def write(self, msg):
        self.lcd.write(msg)

    def command(self, value):
        self.lcd.write(LCD_SEND_COMMAND)
        self.lcd.write(value)
        sleep(0.005)

    def special(self, value):
        self.lcd.write(LCD_SEND_SPECIAL)
        self.lcd.write(value)
        sleep(0.005)    

    def clear(self):
        debug('clear()')
        self.command(LCD_CLEARDISPLAY)

    def cursor(self, row, col):
        line_offset = [0,64,20,84]

        # calculate command (human readable - 1)
        pos_cmd = 128 + line_offset[row-1] + (col-1)

        self.command(chr(pos_cmd))

    def show_cursor(self,on=True):
        if on:
            self.command('\x0E')
        else:
            self.command('\x0C')
    
    def splash(self):
        # print (will be centerd on 20x4)
        self.write('    Pocket FM 2.0   ')
        self.write('                    ')

        # save in EEPROM
        sleep(0.1)
        self.special(LCD_SETSPLASHSCREEN)
        sleep(0.1)


    def __del__(self):
        debug('__del__()')
        self.lcd.close()
        sleep(0.005)