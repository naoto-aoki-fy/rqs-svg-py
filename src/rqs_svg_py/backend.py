"""Qiskit :class:`~qiskit.providers.BackendV2` adapter for RQS-SVG."""

from __future__ import annotations

import uuid
from collections import Counter
from collections.abc import Iterable

from qiskit.circuit import QuantumCircuit
from qiskit.circuit.controlflow import ForLoopOp, IfElseOp, WhileLoopOp
from qiskit.circuit.library.standard_gates import (
    MCPhaseGate,
    MCU1Gate,
    MCXGate,
    get_standard_gate_name_mapping,
)
from qiskit.providers import BackendV2, Options
from qiskit.result import Result
from qiskit.transpiler import Target

from .job import RqsSvgJob
from .runner import iter_circuit_shots


def _bitstring_to_hex(bitstring: str) -> str:
    """Convert a Qiskit display-order bit string to Result's hex format."""
    compact = bitstring.replace(" ", "")
    return hex(int(compact, 2)) if compact else "0x0"


class RqsSvgBackend(BackendV2):
    """A local Qiskit backend powered by the RQS-SVG simulator."""

    def __init__(self, provider=None, **fields) -> None:
        super().__init__(
            provider=provider,
            name="rqs_svg_simulator",
            description="RQS-SVG state-vector simulator",
            backend_version="0.1.0",
            **fields,
        )
        self._target = self._build_target()

    @classmethod
    def _default_options(cls) -> Options:
        return Options(shots=1024, memory=True, max_while_iterations=1_000_000)

    @property
    def target(self) -> Target:
        """Return the instructions directly supported by RQS-SVG."""
        return self._target

    @property
    def max_circuits(self):
        """Return no limit on the number of circuits in a job."""
        return None

    @staticmethod
    def _build_target() -> Target:
        target = Target(description="RQS-SVG simulator target", num_qubits=None)

        # The runner handles Qiskit's standard operations directly, so expose
        # them as the simulator's native ISA. Delay is omitted because it has
        # no corresponding runner implementation.
        for name, instruction in get_standard_gate_name_mapping().items():
            if name == "delay":
                continue
            target.add_instruction(instruction, properties=None, name=name)

        # These operations have a variable width and must be registered by
        # class rather than by a fixed-width instance.
        target.add_instruction(MCXGate, name="mcx")
        target.add_instruction(MCPhaseGate, name="mcphase")
        target.add_instruction(MCU1Gate, name="mcu1")

        # Control-flow operations are likewise interpreted directly by the
        # runner and may contain blocks of different widths.
        target.add_instruction(IfElseOp, name="if_else")
        target.add_instruction(WhileLoopOp, name="while_loop")
        target.add_instruction(ForLoopOp, name="for_loop")
        return target

    def run(self, run_input, **run_options) -> RqsSvgJob:
        """Synchronously execute one circuit or an iterable of circuits."""
        circuits = self._normalize_circuits(run_input)
        shots = run_options.get("shots", self.options.shots)
        memory = run_options.get("memory", self.options.memory)
        max_while_iterations = run_options.get(
            "max_while_iterations", self.options.max_while_iterations
        )

        job_id = str(uuid.uuid4())
        result = self._run_job(
            job_id,
            circuits,
            shots=shots,
            memory=memory,
            max_while_iterations=max_while_iterations,
        )
        return RqsSvgJob(self, job_id, result)

    @staticmethod
    def _normalize_circuits(run_input) -> list[QuantumCircuit]:
        if isinstance(run_input, QuantumCircuit):
            circuits = [run_input]
        elif isinstance(run_input, Iterable):
            circuits = list(run_input)
        else:
            raise TypeError("run_input must be a QuantumCircuit or an iterable of them")

        if not circuits:
            raise ValueError("run_input must contain at least one circuit")
        if not all(isinstance(circuit, QuantumCircuit) for circuit in circuits):
            raise TypeError("run_input must contain only QuantumCircuit instances")
        return circuits

    def _run_job(
        self, job_id, circuits, *, shots, memory, max_while_iterations
    ) -> Result:
        experiments = [
            self._run_one_circuit(
                circuit,
                shots=shots,
                memory=memory,
                max_while_iterations=max_while_iterations,
            )
            for circuit in circuits
        ]
        return Result.from_dict(
            {
                "backend_name": self.name,
                "backend_version": self.backend_version,
                "job_id": job_id,
                "success": True,
                "status": "COMPLETED",
                "results": experiments,
            }
        )

    @staticmethod
    def _run_one_circuit(
        circuit, *, shots, memory, max_while_iterations
    ) -> dict:
        counts: Counter[str] = Counter()
        shot_memory: list[str] = []
        shot_times: list[float] = []

        for shot in iter_circuit_shots(
            circuit,
            shots=shots,
            max_while_iterations=max_while_iterations,
        ):
            value = _bitstring_to_hex(shot.clbits)
            counts[value] += 1
            shot_memory.append(value)
            shot_times.append(shot.elapsed_time)

        data: dict[str, object] = {"counts": dict(counts)}
        if memory:
            data["memory"] = shot_memory

        return {
            "name": circuit.name,
            "shots": shots,
            "success": True,
            "status": "DONE",
            "data": data,
            "header": RqsSvgBackend._make_header(circuit),
            "time_taken": sum(shot_times),
            "rqs_svg": {"shot_times_seconds": shot_times},
        }

    @staticmethod
    def _make_header(circuit: QuantumCircuit) -> dict:
        return {
            "name": circuit.name,
            "n_qubits": circuit.num_qubits,
            "qreg_sizes": [
                [register.name, register.size] for register in circuit.qregs
            ],
            "creg_sizes": [
                [register.name, register.size] for register in circuit.cregs
            ],
            "qubit_labels": [
                [register.name, index]
                for register in circuit.qregs
                for index in range(register.size)
            ],
            "clbit_labels": [
                [register.name, index]
                for register in circuit.cregs
                for index in range(register.size)
            ],
            "memory_slots": circuit.num_clbits,
            "global_phase": float(circuit.global_phase),
            "metadata": circuit.metadata or {},
        }
