# RQS-SVG Python Bindings

This repository contains the Python bindings and Qiskit circuit runner for the
[RQS-SVG](https://github.com/naoto-aoki-fy/rqs-svg) simulator. The CUDA C/C++
simulator source lives in the separate RQS-SVG repository; this package loads
that simulator's `libqcs.so` shared library with Python's standard `ctypes`
module.

## Installation

Install directly from GitHub with `pip`:

```sh
pip install git+https://github.com/naoto-aoki-fy/rqs-svg-py.git
```

Alternatively, after cloning this repository, install it:

```sh
pip install .
```

The package depends on Qiskit for loading and executing `QuantumCircuit` inputs.

## Shared library

Build `libqcs.so` from the separate RQS-SVG repository and make it discoverable
before using these bindings:

```sh
source /path/to/rqs-svg/env.bash
```

## Running Qiskit circuits

The primary interface accepts a Qiskit `QuantumCircuit` and executes it with the
RQS-SVG simulator:

```python
from qiskit import QuantumCircuit
from rqs_svg_py import run_circuit

qc = QuantumCircuit(1, 1)
qc.h(0)
qc.measure(0, 0)

result = run_circuit(qc, shots=10)
print(result.counts)
```

## Python API

For lower-level control, the package also provides a `Simulator` class that
directly exposes the RQS-SVG simulator API:

```python
from rqs_svg_py import Simulator

with Simulator(2) as sim:
    sim.h(0)
    sim.x(1, controls=[0])
    sim.measure_to_clbit(0, 0)
    sim.measure_to_clbit(1, 1)
    print(sim.clbits_string())
```

## CLI

Installing the package exposes the circuit-execution CLI as `rqs-svg`:

```sh
rqs-svg --shots 10 path/to/circuit.py
```

The input may be a Python file that defines a `QuantumCircuit` named `qc` or
`circuit`, a QPY file, or an OpenQASM file. Use `--library /path/to/libqcs.so`
to select a specific RQS-SVG shared library.

## Examples

Python examples live under `examples/`.

## Acknowledgments

This repository is based on results obtained from a project, JPNP20017,
commissioned by the New Energy and Industrial Technology Development
Organization (NEDO).
