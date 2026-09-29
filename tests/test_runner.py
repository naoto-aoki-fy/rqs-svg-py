import unittest
from unittest.mock import Mock

from qiskit import QuantumCircuit

from rqs_svg_py.runner import _execute_instructions


class BatchedMeasurementTests(unittest.TestCase):
    def test_adjacent_measurements_are_batched(self):
        circuit = QuantumCircuit(3, 3)
        circuit.measure([2, 0, 1], [0, 2, 1])
        simulator = Mock()

        _execute_instructions(circuit.data, circuit, simulator, max_while_iterations=10)

        simulator.measure_many_to_clbits.assert_called_once_with([2, 0, 1], [0, 2, 1])
        simulator.measure_to_clbit.assert_not_called()

    def test_gate_flushes_measurement_batch(self):
        circuit = QuantumCircuit(2, 2)
        circuit.measure(0, 0)
        circuit.x(1)
        circuit.measure(1, 1)
        simulator = Mock()

        _execute_instructions(circuit.data, circuit, simulator, max_while_iterations=10)

        self.assertEqual(
            simulator.method_calls,
            [
                unittest.mock.call.measure_many_to_clbits([0], [0]),
                unittest.mock.call.gate(
                    "x",
                    (1,),
                    [],
                    [],
                ),
                unittest.mock.call.measure_many_to_clbits([1], [1]),
            ],
        )

    def test_repeated_destination_starts_a_new_batch(self):
        circuit = QuantumCircuit(2, 1)
        circuit.measure(0, 0)
        circuit.measure(1, 0)
        simulator = Mock()

        _execute_instructions(circuit.data, circuit, simulator, max_while_iterations=10)

        self.assertEqual(
            simulator.measure_many_to_clbits.call_args_list,
            [unittest.mock.call([0], [0]), unittest.mock.call([1], [0])],
        )


if __name__ == "__main__":
    unittest.main()
