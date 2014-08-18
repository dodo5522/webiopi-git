#!/usr/bin/env python3

import unittest
from mpl115a2 import *
from htu21d import *

class MP1115A2_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.obj = MPL115A2(reset_pin_bcm=22)

    def test_read_coef_value_a0(self):
        result = self.obj._getRegValueAsFloat(
                0x04,
                16,
                1,
                12,
                3,
                0,
                (0x3e, 0xce))
        self.assertEqual(result, 2009.75)

    def test_read_coef_value_b1(self):
        result = self.obj._getRegValueAsFloat(
                0x06,
                16,
                1,
                2,
                13,
                0,
                (0xb3, 0xf9))
        self.assertEqual(result, -1.6241455078125)

    def test_read_coef_value_b2(self):
        result = self.obj._getRegValueAsFloat(
                0x08,
                16,
                1,
                1,
                14,
                0,
                (0xc5, 0x17))
        self.assertEqual(result, -1.07952880859375)

    def test_read_coef_value_c12(self):
        result = self.obj._getRegValueAsFloat(
                0x0a,
                14,
                1,
                0,
                13,
                9,
                (0x33, 0xc8))
        self.assertEqual(result, 0.0007901191711425781)

    def test_Adc2Pcomp(self):
        self.obj._coef_a0 = 2009.75
        self.obj._coef_b1 = -2.37585
        self.obj._coef_b2 = -0.92047
        self.obj._coef_c12 = 0.000790
        result = self.obj._Adc2Pcomp((410, 507))
        self.assertEqual(result, 733.1905100000001)

class HTU21D_test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.obj = HTU21D()

    def test_dummy(self):
        pass

if __name__ == '__main__':
    unittest.main()

