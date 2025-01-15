# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Waveshare team, 2023 Mikko Pitkänen
#
# SPDX-License-Identifier: MIT
"""
`epd_2in13_b`
================================================================================

Circuitpython library to use Waveshare 2.13B V4 inch ePaper display with Raspberry Pico W


* Author(s): Waveshare team, Mikko Pitkänen

Implementation Notes
--------------------

This is a Circuitpython version of Waveshare 2.13" epaper display lib for Raspberry Pi Pico based on Waveshare team's micropython class/example.


**Hardware:**

* `Waveshare 2.13inch E-Paper E-Ink Display Module (B) for Raspberry Pi Pico https://www.waveshare.com/pico-epaper-2.13-b.htm`_
* `Waveshare 2.13inch E-Paper wiki https://www.waveshare.com/wiki/Pico-ePaper-2.13-B`_
* `Display module specification sheet https://www.waveshare.com/w/upload/d/d8/2.13inch_e-Paper_%28B%29_V3_Specification.pdf`_
* `Waveshare ePaper github pages https://github.com/waveshare/Pico_ePaper_Code`_


**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads




"""

# imports

__version__ = "0.0.1+auto.0"
__repo__ = "https://github.com/e-marco/CircuitPython_EPD_2in13_B_V4.git"

import time

import digitalio
import busio
import adafruit_framebuf
import board


#define constant pins for pico
RST_PIN         = board.GP12 
DC_PIN          = board.GP8 
CS_PIN          = board.GP9 
BUSY_PIN        = board.GP13 

EPD_WIDTH       = 122
EPD_HEIGHT      = 250

class EPD_2in13_B_V4:
    def __init__(self, rotation):
        # create the spi device and pins we will need
        self.spi = busio.SPI(clock=board.GP10, MOSI=board.GP11)

        self.cs = digitalio.DigitalInOut(CS_PIN)
        self.cs.direction = digitalio.Direction.OUTPUT
        self.dc = digitalio.DigitalInOut(DC_PIN)
        self.dc.direction = digitalio.Direction.OUTPUT
        self.rst = digitalio.DigitalInOut(RST_PIN)
        self.rst.direction = digitalio.Direction.OUTPUT
        
        self.busy = digitalio.DigitalInOut(BUSY_PIN)
        self.busy.direction = digitalio.Direction.INPUT
        self.busy.pull = digitalio.Pull.UP

        if EPD_WIDTH % 8 == 0:
            self.width = EPD_WIDTH
        else :
            self.width = (EPD_WIDTH // 8) * 8 + 8

        self.height = EPD_HEIGHT

        self.framebuffer_black_array = bytearray(self.height * self.width // 8)
        self.framebuffer_red_array = bytearray(self.height * self.width // 8)
        self.framebuffer_black = adafruit_framebuf.FrameBuffer(self.framebuffer_black_array, self.width, self.height, adafruit_framebuf.MHMSB)
        self.framebuffer_red = adafruit_framebuf.FrameBuffer(self.framebuffer_red_array, self.width, self.height, adafruit_framebuf.MHMSB)

        self.framebuffer_black.rotation=rotation
        self.framebuffer_red.rotation=rotation

        self.init()

    def init(self):
        self.reset()
        self.ReadBusy()  # waiting for the electronic paper IC to release the idle signal
        self.send_command(0x12)  #SWRESET
        self.ReadBusy()   

        self.send_command(0x01) #Driver output control      
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11) #data entry mode       
        self.send_data(0x03)
        
        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)

	self.send_command(0x3C) #BorderWaveform
        self.send_data(0x05)

        self.send_command(0x18) #Read built-in temperature sensor
        self.send_data(0x80)

        self.send_command(0x21) #  Display update control
        self.send_data(0x80)
        self.send_data(0x80)

        self.ReadBusy()

        print('Display initialized')

        return 0

    # Hardware reset
    def reset(self):
        self.digital_write(self.rst, True)
        self.delay_ms(50)
        self.digital_write(self.rst, False)
        self.delay_ms(2)
        self.digital_write(self.rst, True)
        self.delay_ms(50)

    def send_command(self, command):
        self.digital_write(self.dc, False)
        self.digital_write(self.cs, False)
        self.spi_writebyte([command])
        self.digital_write(self.cs, True)

    def digital_write(self, pin, value):
        pin.value = value

    def digital_read(self, pin):
        return pin.value
        
   	
    def module_exit(self):
        self.digital_write(self.rst, False)

    def delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        while not self.spi.try_lock():
            pass
        try:
            self.spi.configure(baudrate=4000000, phase=0, polarity=0)
            self.cs.value = False
            self.spi.write(bytearray(data))
            self.cs.value = True
        finally:
            self.spi.unlock()

    def ReadBusy(self):
        print('Display busy')
        self.send_command(0x71)
        
        while (self.digital_read(self.busy)):
            self.send_command(0x71)
            self.delay_ms(10)
        print('Display free')

    def send_data(self, data):
        self.digital_write(self.dc, True )
        self.digital_write(self.cs, False)
        self.spi_writebyte([data])
        self.digital_write(self.cs, True)

    def Clear(self, colorblack, colorred):
        self.send_command(0x24)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(colorblack)
        self.send_command(0x26)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(colorred)

        self.TurnOnDisplay()

    def TurnOnDisplay(self):
        self.send_command(0x20)
        self.ReadBusy()
        
    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.send_command(0x44) # SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((Xstart>>3) & 0xFF)
        self.send_data((Xend>>3) & 0xFF)

        self.send_command(0x45) # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)
        self.send_data(Yend & 0xFF)
        self.send_data((Yend >> 8) & 0xFF)
        
    def SetCursor(self, Xstart, Ystart):
        self.send_command(0x4E) # SET_RAM_X_ADDRESS_COUNTER
        self.send_data(Xstart & 0xFF)

        self.send_command(0x4F) # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)

    def sleep(self):
        self.send_command(0x10) 
        self.send_data(0x01)
        
        self.delay_ms(2000)
        self.module_exit()

    def display(self):
        self.send_command(0x24)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(self.framebuffer_black_array[i + j * int(self.width / 8)])

        self.send_command(0x26)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(self.framebuffer_red_array[i + j * int(self.width / 8)])

        self.TurnOnDisplay()

