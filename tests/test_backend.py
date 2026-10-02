import unittest
from unittest.mock import patch

from qiskit import QuantumCircuit, transpile
from qiskit.primitives import BackendSamplerV2
from qiskit.providers import JobStatus

from rqs_svg_py import RqsSvgBackend
from rqs_svg_py.runner import ShotRunResult


class RqsSvgBackendTests(unittest.TestCase):
    def setUp(self):
        self.backend = RqsSvgBackend()

    def test_transpile_level_zero_preserves_native_gates(self):
        circuit = QuantumCircuit(3, 3)
        circuit.h(0)
        circuit.rx(0.123, 1)
        circuit.cz(0, 1)
        circuit.ccx(0, 1, 2)
        circuit.measure([0, 1, 2], [0, 1, 2])

        compiled = transpile(circuit, self.backend, optimization_level=0)

        self.assertEqual(
            [instruction.operation.name for instruction in compiled.data],
            [instruction.operation.name for instruction in circuit.data],
        )

    def test_transpile_level_zero_preserves_variable_width_mcx(self):
        circuit = QuantumCircuit(4, 1)
        circuit.mcx([0, 1, 2], 3)
        circuit.measure(3, 0)

        compiled = transpile(circuit, self.backend, optimization_level=0)

        self.assertEqual(
            [instruction.operation.name for instruction in compiled.data],
            ["mcx", "measure"],
        )

    @patch("rqs_svg_py.backend.iter_circuit_shots")
    def test_run_builds_qiskit_counts_memory_and_timing(self, iter_shots):
        iter_shots.return_value = iter(
            [
                ShotRunResult(0, "00", 0.1, 0),
                ShotRunResult(1, "11", 0.2, 0),
                ShotRunResult(2, "11", 0.3, 0),
            ]
        )
        circuit = QuantumCircuit(2, 2, name="bell")
        circuit.metadata = {"purpose": "test"}

        job = self.backend.run(circuit, shots=3)
        result = job.result()

        self.assertEqual(job.status(), JobStatus.DONE)
        self.assertEqual(result.get_counts(), {"00": 1, "11": 2})
        self.assertEqual(result.get_memory(), ["00", "11", "11"])
        self.assertAlmostEqual(result.results[0].time_taken, 0.6)
        self.assertEqual(result.results[0].header["metadata"], {"purpose": "test"})
        self.assertEqual(
            result.results[0].rqs_svg["shot_times_seconds"], [0.1, 0.2, 0.3]
        )
        iter_shots.assert_called_once_with(
            circuit, shots=3, max_while_iterations=1_000_000
        )

    @patch("rqs_svg_py.backend.iter_circuit_shots")
    def test_run_multiple_circuits_without_memory(self, iter_shots):
        iter_shots.side_effect = [
            iter([ShotRunResult(0, "0", 0.1, 0)]),
            iter([ShotRunResult(0, "1", 0.2, 0)]),
        ]
        first = QuantumCircuit(1, 1, name="first")
        second = QuantumCircuit(1, 1, name="second")

        result = self.backend.run([first, second], shots=1, memory=False).result()

        self.assertEqual(result.get_counts(0), {"0": 1})
        self.assertEqual(result.get_counts(1), {"1": 1})
        self.assertNotIn("memory", result.results[0].data.to_dict())

    @patch("rqs_svg_py.backend.iter_circuit_shots")
    def test_backend_sampler_v2_uses_shot_memory(self, iter_shots):
        iter_shots.return_value = iter(
            [ShotRunResult(0, "0", 0.1, 0), ShotRunResult(1, "1", 0.1, 0)]
        )
        circuit = QuantumCircuit(1, 1)
        circuit.measure(0, 0)

        result = BackendSamplerV2(backend=self.backend).run(
            [circuit], shots=2
        ).result()

        self.assertEqual(result[0].data.c.get_counts(), {"0": 1, "1": 1})

    def test_run_rejects_invalid_or_empty_input(self):
        with self.assertRaises(ValueError):
            self.backend.run([])
        with self.assertRaises(TypeError):
            self.backend.run([object()])


if __name__ == "__main__":
    unittest.main()
