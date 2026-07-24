"""ctypes bindings for the RQS-SVG ``libqcs.so`` shared library."""

import ctypes
import os
from typing import Iterable, List, Optional, Sequence, Tuple, Union

_BIT_NUM = ctypes.c_int16
_EVENT_NUM = ctypes.c_int16
_BIT = ctypes.c_uint8
_BIT_NUM_P = ctypes.POINTER(_BIT_NUM)
_BIT_P = ctypes.POINTER(_BIT)
_NULL_BIT_NUM_P = ctypes.cast(None, _BIT_NUM_P)
_EXCEPTION_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_size_t)


class QcsError(RuntimeError):
    """Raised when the shared library cannot be loaded or initialized."""


def _int_array(
    values: Optional[Sequence[int]],
) -> Tuple[Optional[ctypes.Array], _BIT_NUM_P, int]:
    if values is None:
        return None, _NULL_BIT_NUM_P, 0
    array = (_BIT_NUM * len(values))(*values)
    return array, ctypes.cast(array, _BIT_NUM_P), len(values)


def _check(lib: ctypes.CDLL, status: int) -> None:
    if status == 0:
        return
    message = getattr(lib, "_qcs_last_error", "")
    if message:
        raise QcsError(message)
    raise QcsError(f"RQS-SVG call failed with status {status}")


def _configure_status_function(function, argtypes) -> None:
    function.argtypes = argtypes
    function.restype = ctypes.c_int


def _configure_library(lib: ctypes.CDLL) -> None:
    sim = ctypes.c_void_p
    sim_p = ctypes.POINTER(sim)

    def exception_callback(message: bytes, message_length: int) -> None:
        lib._qcs_last_error = ctypes.string_at(message, message_length).decode(
            "utf-8", errors="replace"
        )

    callback = _EXCEPTION_CALLBACK(exception_callback)
    lib._qcs_exception_callback = callback
    lib._qcs_last_error = ""
    _configure_status_function(lib.qcs_set_exception_callback, [_EXCEPTION_CALLBACK])
    _check(lib, lib.qcs_set_exception_callback(callback))

    _configure_status_function(lib.qcs_simulator_create, [sim_p])
    _configure_status_function(lib.qcs_simulator_destroy, [sim])
    _configure_status_function(lib.qcs_simulator_allocate_memory, [sim])
    _configure_status_function(lib.qcs_simulator_dispose, [sim])
    _configure_status_function(lib.qcs_simulator_set_num_qubits, [sim, _BIT_NUM])
    _configure_status_function(lib.qcs_simulator_set_num_clbits, [sim, _BIT_NUM])
    _configure_status_function(
        lib.qcs_simulator_set_mapping, [sim, _BIT_NUM_P, _BIT_NUM]
    )
    _configure_status_function(lib.qcs_simulator_get_proc_num, [sim, _BIT_P])
    _configure_status_function(lib.qcs_simulator_get_num_procs, [sim, _BIT_P])
    _configure_status_function(lib.qcs_simulator_get_num_qubits, [sim, _BIT_P])
    _configure_status_function(lib.qcs_simulator_get_num_clbits, [sim, _BIT_P])
    _configure_status_function(lib.qcs_simulator_get_clbits, [sim, _BIT_P])
    _configure_status_function(lib.qcs_simulator_measure, [sim, _BIT_NUM, _BIT_P])
    _configure_status_function(
        lib.qcs_simulator_measure_to_clbit, [sim, _BIT_NUM, _BIT_NUM, _BIT_P]
    )
    _configure_status_function(lib.qcs_simulator_read, [sim, _BIT_NUM, _BIT_P])
    _configure_status_function(
        lib.qcs_simulator_get_clbits_string, [sim, ctypes.c_char_p]
    )
    _configure_status_function(
        lib.qcs_simulator_save_statevector, [sim, ctypes.c_char_p]
    )
    _configure_status_function(lib.qcs_simulator_reset, [sim, _BIT_NUM])
    for name in (
        "set_zero_state",
        "set_sequential_state",
        "set_flat_state",
        "set_entangled_state",
        "set_random_state",
        "reset_clbits",
        "reset_measurement_state",
        "reinitialize_mapping",
    ):
        _configure_status_function(getattr(lib, f"qcs_simulator_{name}"), [sim])

    _configure_status_function(lib.qcs_simulator_event_create, [sim, _BIT_P])
    _configure_status_function(lib.qcs_simulator_event_record, [sim, ctypes.c_int])
    _configure_status_function(
        lib.qcs_simulator_event_get_elapsed_time,
        [sim, _EVENT_NUM, _EVENT_NUM, ctypes.POINTER(ctypes.c_double)],
    )

    gate_args = [sim, _BIT_NUM_P, _BIT_NUM, _BIT_NUM_P, _BIT_NUM, _BIT_NUM_P, _BIT_NUM]
    for name in (
        "h",
        "x",
        "y",
        "z",
        "s",
        "sdg",
        "t",
        "tdg",
        "sx",
        "sxdg",
        "swap",
        "iswap",
        "id",
        "dcx",
        "ecr",
        "rccx",
        "rcccx",
    ):
        _configure_status_function(
            getattr(lib, f"qcs_simulator_gate_{name}"), gate_args
        )

    _configure_status_function(
        lib.qcs_simulator_gate_global_phase,
        [sim, ctypes.c_double, _BIT_NUM_P, _BIT_NUM, _BIT_NUM_P, _BIT_NUM],
    )
    for name in ("rx", "ry", "rz", "u1", "p", "rxx", "ryy", "rzz", "rzx"):
        _configure_status_function(
            getattr(lib, f"qcs_simulator_gate_{name}"),
            [sim, ctypes.c_double, *gate_args[1:]],
        )
    for name in ("r", "xx_plus_yy", "xx_minus_yy"):
        _configure_status_function(
            getattr(lib, f"qcs_simulator_gate_{name}"),
            [sim, ctypes.c_double, ctypes.c_double, *gate_args[1:]],
        )
    for name in ("u", "u3"):
        _configure_status_function(
            getattr(lib, f"qcs_simulator_gate_{name}"),
            [sim, ctypes.c_double, ctypes.c_double, ctypes.c_double, *gate_args[1:]],
        )
    _configure_status_function(
        lib.qcs_simulator_gate_u2,
        [sim, ctypes.c_double, ctypes.c_double, *gate_args[1:]],
    )
    _configure_status_function(
        lib.qcs_simulator_gate_u4,
        [
            sim,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            *gate_args[1:],
        ],
    )


class Simulator:
    """Small Python wrapper around a ``qcs_simulator*`` from ``libqcs.so``."""

    def __init__(self, num_qubits: int, num_clbits: Optional[int] = None):
        try:
            self._lib = ctypes.CDLL("libqcs.so")
        except OSError as exc:
            raise QcsError(
                "Failed to load libqcs.so. Ensure that its directory is available "
                "to the dynamic linker, for example through LD_LIBRARY_PATH."
            ) from exc

        _configure_library(self._lib)
        sim = ctypes.c_void_p()
        _check(self._lib, self._lib.qcs_simulator_create(ctypes.byref(sim)))
        if not sim.value:
            raise QcsError("qcs_simulator_create returned NULL")
        self._sim = sim
        self._closed = False
        self._num_clbits = num_qubits if num_clbits is None else num_clbits
        _check(self._lib, self._lib.qcs_simulator_set_num_qubits(self._sim, num_qubits))
        _check(
            self._lib,
            self._lib.qcs_simulator_set_num_clbits(self._sim, self._num_clbits),
        )
        _check(self._lib, self._lib.qcs_simulator_allocate_memory(self._sim))

    def _get_bit_result(self, function) -> int:
        result = _BIT()
        _check(self._lib, function(self._sim, ctypes.byref(result)))
        return int(result.value)

    @property
    def proc_num(self) -> int:
        return self._get_bit_result(self._lib.qcs_simulator_get_proc_num)

    @property
    def num_procs(self) -> int:
        return self._get_bit_result(self._lib.qcs_simulator_get_num_procs)

    @property
    def num_qubits(self) -> int:
        return self._get_bit_result(self._lib.qcs_simulator_get_num_qubits)

    @property
    def num_clbits(self) -> int:
        return self._get_bit_result(self._lib.qcs_simulator_get_num_clbits)

    def init(self) -> None:
        """Retained for compatibility; initialization is handled by RQS-SVG."""

    def setup(self) -> None:
        """Retained for compatibility; setup is handled by RQS-SVG."""

    def allocate_memory(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_allocate_memory(self._sim))

    def dispose(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_dispose(self._sim))

    def set_mapping(self, perm_p2l: Sequence[int]) -> None:
        keepalive, ptr, count = _int_array(perm_p2l)
        _check(self._lib, self._lib.qcs_simulator_set_mapping(self._sim, ptr, count))
        _ = keepalive

    def gate(
        self,
        name: str,
        targets: Iterable[int],
        controls: Iterable[int] = (),
        negative_controls: Iterable[int] = (),
        *parameters: float,
    ) -> None:
        fn = getattr(self._lib, f"qcs_simulator_gate_{name}")
        target_keepalive, target_ptr, target_count = _int_array(list(targets))
        neg_keepalive, neg_ptr, neg_count = _int_array(list(negative_controls))
        ctrl_keepalive, ctrl_ptr, ctrl_count = _int_array(list(controls))
        _check(
            self._lib,
            fn(
                self._sim,
                *parameters,
                target_ptr,
                target_count,
                neg_ptr,
                neg_count,
                ctrl_ptr,
                ctrl_count,
            ),
        )
        _ = (target_keepalive, neg_keepalive, ctrl_keepalive)

    def global_phase(
        self,
        theta: float,
        controls: Iterable[int] = (),
        negative_controls: Iterable[int] = (),
    ) -> None:
        neg_keepalive, neg_ptr, neg_count = _int_array(list(negative_controls))
        ctrl_keepalive, ctrl_ptr, ctrl_count = _int_array(list(controls))
        _check(
            self._lib,
            self._lib.qcs_simulator_gate_global_phase(
                self._sim, theta, neg_ptr, neg_count, ctrl_ptr, ctrl_count
            ),
        )
        _ = (neg_keepalive, ctrl_keepalive)

    def h(self, qubit: int) -> None:
        self.gate("h", [qubit])

    def x(self, qubit: int, controls: Iterable[int] = ()) -> None:
        self.gate("x", [qubit], controls=controls)

    def measure_to_clbit(self, qubit: int, clbit: int) -> int:
        result = _BIT()
        _check(
            self._lib,
            self._lib.qcs_simulator_measure_to_clbit(
                self._sim, qubit, clbit, ctypes.byref(result)
            ),
        )
        return int(result.value)

    def measure(self, qubit: int) -> int:
        result = _BIT()
        _check(
            self._lib,
            self._lib.qcs_simulator_measure(self._sim, qubit, ctypes.byref(result)),
        )
        return int(result.value)

    def read(self, clbit: int) -> int:
        result = _BIT()
        _check(
            self._lib,
            self._lib.qcs_simulator_read(self._sim, clbit, ctypes.byref(result)),
        )
        return int(result.value)

    def reset(self, qubit: int) -> None:
        _check(self._lib, self._lib.qcs_simulator_reset(self._sim, qubit))

    def clbits(self) -> List[int]:
        buffer = (_BIT * self.num_clbits)()
        _check(self._lib, self._lib.qcs_simulator_get_clbits(self._sim, buffer))
        return [int(bit) for bit in buffer]

    def clbits_string(self) -> str:
        buffer = ctypes.create_string_buffer(self.num_clbits + 1)
        _check(self._lib, self._lib.qcs_simulator_get_clbits_string(self._sim, buffer))
        return buffer.value.decode("ascii")

    def save_statevector(self, filename: Union[str, os.PathLike]) -> None:
        _check(
            self._lib,
            self._lib.qcs_simulator_save_statevector(self._sim, os.fsencode(filename)),
        )

    def set_zero_state(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_set_zero_state(self._sim))

    def set_sequential_state(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_set_sequential_state(self._sim))

    def set_flat_state(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_set_flat_state(self._sim))

    def set_entangled_state(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_set_entangled_state(self._sim))

    def set_random_state(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_set_random_state(self._sim))

    def reset_clbits(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_reset_clbits(self._sim))

    def reset_measurement_state(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_reset_measurement_state(self._sim))

    def reinitialize_mapping(self) -> None:
        _check(self._lib, self._lib.qcs_simulator_reinitialize_mapping(self._sim))

    def reset_for_next_sample(self) -> None:
        self.reinitialize_mapping()
        self.set_zero_state()
        self.reset_clbits()
        self.reset_measurement_state()

    def event_create(self) -> int:
        result = _BIT()
        _check(
            self._lib,
            self._lib.qcs_simulator_event_create(self._sim, ctypes.byref(result)),
        )
        return int(result.value)

    def event_record(self, event_num: int) -> None:
        _check(self._lib, self._lib.qcs_simulator_event_record(self._sim, event_num))

    def event_get_elapsed_time(
        self, start_event_num: int, stop_event_num: int
    ) -> float:
        result = ctypes.c_double()
        _check(
            self._lib,
            self._lib.qcs_simulator_event_get_elapsed_time(
                self._sim, start_event_num, stop_event_num, ctypes.byref(result)
            ),
        )
        return float(result.value)

    def fflush_master(self, stream: Optional[int] = None) -> int:
        return 0

    def fflush_all(self, stream: Optional[int] = None) -> int:
        return 0

    def close(self) -> None:
        if not getattr(self, "_closed", True):
            _check(self._lib, self._lib.qcs_simulator_destroy(self._sim))
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
