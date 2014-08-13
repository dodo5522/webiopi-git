#   Copyright 2014 Takashi Ando <dodo5522@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import time
from webiopi.devices.i2c import I2C
from webiopi.devices.sensor import Pressure
from webiopi.devices.digital.gpio import NativeGPIO

class MPL115A2(I2C, NativeGPIO, Pressure):
    def __init__(self, altitude=0, external=None, reset_pin_bcm=None):
        NativeGPIO.__init__(self)

        self._reset_pin_bcm = reset_pin_bcm
        self.resetHardware()

        I2C.__init__(self, 0x60)
        Pressure.__init__(self, altitude, external)

        coef_values = self._getCoefValues()
        self._coef_a0 = coef_values[0]
        self._coef_b1 = coef_values[1]
        self._coef_b2 = coef_values[2]
        self._coef_c12 = coef_values[3]

    def __str__(self):
        return 'MPL115A2'

    def __family__(self):
        return [Pressure.__family__(self)]

    def __getPascal__(self):
        '''
        Return the pressure value with kPa.
        '''
        pcomp = self._Adc2Pcomp(self._getAdcValues())
        kPascal = pcomp * ((115 - 50) / 1023.0) + 50

        return kPascal * 1000

    def resetHardware(self):
        if self._reset_pin_bcm is None:
            return

        self.addGPIOSetup(self._reset_pin_bcm, "out 0")
        self.setup()

        # 5ms as max between leaving shutdown mode and communicating with the device.
        time.sleep(0.01)

        self.addGPIOSetup(self._reset_pin_bcm, "out 1")
        self.setup()

    def _getCoefValues(self):
        '''
        Return coeffient data read from MPL115A2 registers as the below tuple with float value.
        (a0, b1, b2, c12)
        '''
        table_coef_adr_and_bitwidth = \
                (
                    #addresses      total, sign, integer, fractional, zero pad
                    ((0x04, 0x05), (16,    1,    12,      3,          0)), # a0
                    ((0x06, 0x07), (16,    1,    2,       13,         0)), # b1
                    ((0x08, 0x09), (16,    1,    1,       14,         0)), # b2
                    ((0x0a, 0x0b), (14,    1,    0,       13,         9)), # c12
                )

        coef_values = []
        for coef_info in table_coef_adr_and_bitwidth:
            coef_values.append(
                    self._getRegValueAsFloat(
                        coef_info[0][0],    # adr
                        coef_info[1][0],    # total bits
                        coef_info[1][1],    # sign bit
                        coef_info[1][2],    # integer bits
                        coef_info[1][3],    # fractional bits
                        coef_info[1][4]))   # pad bits

        return coef_values

    def _getAdcValues(self):
        '''
        Return adc data read from MPL115A2 registers as the below tuple with float value.
        (Padc, Tadc)
        '''
        table_adc_adr_and_bitwidth = \
                (
                    #addresses      total, sign, integer, fractional, zero pad
                    ((0x00, 0x01), (10,    0,    10,      0,          0)), # Padc
                    ((0x02, 0x03), (10,    0,    10,      0,          0)), # Tadc
                )

        self._requestConvert()

        adc_values = []
        for adc_info in table_adc_adr_and_bitwidth:
            adc_values.append(
                    self._getRegValueAsFloat(
                        adc_info[0][0],    # adr
                        adc_info[1][0],    # total bits
                        adc_info[1][1],    # sign bit
                        adc_info[1][2],    # integer bits
                        adc_info[1][3],    # fractional bits
                        adc_info[1][4]))   # pad bits

        return adc_values

    def _getRegValueAsFloat(self, addr, totalbits, signbit, intbits, fracbits, padbits, regs=None):
        '''
        Read register and return float value as calculated result with spec of datasheet.
        '''
        if regs is None:
            regs = self.readRegisters(addr, 2)
        raw_reg_value = regs[0] << 8 | regs[1]

        sign = 1
        if signbit and raw_reg_value & 0x8000:
            raw_reg_value ^= 0x8000
            sign = -1

        # For values with less than 16 bits, the lower LSBs are zero.
        raw_reg_value &= 0xffff - (2**(16 - totalbits) - 1)

        return sign * float(raw_reg_value) / (1 << (16 - totalbits + fracbits + padbits))

    def _requestConvert(self):
        '''
        Request convertion to MPL115A2 due to spec of datasheet.
        This function need about 10ms to return.
        '''
        self.writeRegister(0x12, 0x00)

        # wait for the conversion time (tc) 3ms as max.
        time.sleep(0.01)

    def _Adc2Pcomp(self, adc_values):
        '''
        Calculate and return Pcomp value.
        '''

        # Pcomp = a0+(b1+c12⋅Tadc)⋅Padc+b2⋅Tadc
        pcomp = self._coef_a0 + \
                (self._coef_b1 + self._coef_c12 * adc_values[1]) * adc_values[0] + \
                self._coef_b2 * adc_values[1]
 
        return pcomp

