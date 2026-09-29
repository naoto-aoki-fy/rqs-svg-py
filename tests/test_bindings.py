import ctypes
import unittest
from unittest.mock import Mock

from rqs_svg_py.bindings import Simulator


class SimulatorMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.sim = Simulator.__new__(Simulator)
        self.sim._sim = ctypes.c_void_p(123)
        self.sim._lib = Mock()
        self.sim._lib._qcs_last_error = ""

    def test_measure_many_preserves_result_order(self):
        def measure_many(_sim, qubits, count, results):
            self.assertEqual([qubits[i] for i in range(count)], [5, 1, 3])
            for index, value in enumerate((1, 0, 1)):
                results[index] = value
            return 0

        self.sim._lib.qcs_simulator_measure_many.side_effect = measure_many

        self.assertEqual(self.sim.measure_many([5, 1, 3]), [1, 0, 1])

    def test_measure_many_to_clbits_passes_corresponding_lists(self):
        def measure_many_to_clbits(
            _sim, qubits, qubit_count, clbits, clbit_count, results
        ):
            self.assertEqual([qubits[i] for i in range(qubit_count)], [2, 0])
            self.assertEqual([clbits[i] for i in range(clbit_count)], [1, 3])
            results[0], results[1] = 0, 1
            return 0

        function = self.sim._lib.qcs_simulator_measure_many_to_clbits
        function.side_effect = measure_many_to_clbits

        self.assertEqual(self.sim.measure_many_to_clbits([2, 0], [1, 3]), [0, 1])

    def test_empty_measurement_is_supported(self):
        self.sim._lib.qcs_simulator_measure_many.return_value = 0

        self.assertEqual(self.sim.measure_many([]), [])


if __name__ == "__main__":
    unittest.main()
