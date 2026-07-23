# RQS-SVG Python Bindings

This repository contains the Python bindings and Qiskit circuit runner for the
[RQS-SVG](https://github.com/naoto-aoki-fy/rqs-svg) simulator. The CUDA C/C++
simulator source lives in the separate RQS-SVG repository; this package loads
that simulator's `libqcs.so` shared library with Python's standard `ctypes`
module.

## Installation

Install this package with `pip`:

```sh
pip install .
```

The package depends on Qiskit for loading and executing `QuantumCircuit` inputs.

## Shared library

Build `libqcs.so` from the separate RQS-SVG repository and make it discoverable
before using these bindings. Either place `libqcs.so` in the current working
directory when running Python, place it next to the installed package, pass an
explicit path to APIs that accept `library_path`, or set:

```sh
export QCS_LIBRARY_PATH=/path/to/libqcs.so
```

## Python API

```python
from rqs_svg_py import Simulator

with Simulator(2) as sim:
    sim.h(0)
    sim.x(1, controls=[0])
    sim.measure_to_clbit(0, 0)
    sim.measure_to_clbit(1, 1)
    print(sim.clbits_string())
```

For Qiskit circuits, use `run_circuit`:

```python
from qiskit import QuantumCircuit
from rqs_svg_py import run_circuit

qc = QuantumCircuit(1, 1)
qc.h(0)
qc.measure(0, 0)

result = run_circuit(qc, shots=10)
print(result.counts)
```

## CLI

Installing the package exposes the circuit-execution CLI as `rqs-svg-qcs`:

```sh
rqs-svg-qcs --shots 10 path/to/circuit.py
```

The input may be a Python file that defines a `QuantumCircuit` named `qc` or
`circuit`, a QPY file, or an OpenQASM file. Use `--library /path/to/libqcs.so` to
select a specific RQS-SVG shared library.

## Examples

Python examples live under `examples/python/`.
