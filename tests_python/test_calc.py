import unittest
import sys
from pathlib import Path

# Add the project "python" directory to path
sys.path.append(str(Path(__file__).resolve().parents[1] / 'python'))
import calc

class CalcTest(unittest.TestCase):
    def test_basic_expression(self):
        self.assertAlmostEqual(calc.calc("1 + 2 * 3"), 7.0)
        self.assertAlmostEqual(calc.calc("5 * ( 10 - 9 )"), 5.0)

if __name__ == '__main__':
    unittest.main()
