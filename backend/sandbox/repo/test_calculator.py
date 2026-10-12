import unittest
from calculator import calculate_discount, calculate_tax

class TestCalculator(unittest.TestCase):
    def test_calculate_tax(self):
        self.assertEqual(calculate_tax(100.0, 0.08), 8.0)

    def test_calculate_discount_standard(self):
        # 20% discount on $100 should be $80.0
        # Bug produces 100 - (100 * 20) = -1900.0
        result = calculate_discount(100.0, 20.0)
        self.assertEqual(result, 80.0)

    def test_calculate_discount_zero(self):
        self.assertEqual(calculate_discount(50.0, 0.0), 50.0)

    def test_calculate_discount_invalid(self):
        with self.assertRaises(ValueError):
            calculate_discount(-10.0, 10.0)

if __name__ == "__main__":
    unittest.main()
