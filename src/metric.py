import os
import numpy as np
import pennylane as qml
from configparser import ConfigParser

# ======================================================================
# Configurazione
# ======================================================================
config = ConfigParser()
config.read('config.ini')
nqubits = config.getint('quantum', 'nqubits')
num_gates = config.getint('quantum', 'num_gates') 


single_qubit_gates = config.get('quantum', 'single_qubit_gate_set').split(',')
two_qubit_gates = config.get('quantum', 'two_qubit_gate_set').split(',')
angles = [float(a.strip()) for a in config.get('quantum', 'angles').split(',') if a.strip()]


def MeyerWallach(gates, n_wires=nqubits, n_qubits=nqubits):
    dev = qml.device("default.qubit", wires=n_wires)

    @qml.qnode(dev)
    def circuit():
        for name, params in gates:
            if name == "H": qml.H(wires=params[0])
            elif name == "RY": qml.RY(params[0], wires=params[1])
            elif name == "Z": qml.PauliZ(wires=params[0])
            elif name == "CNOT": qml.CNOT(wires=params)
            elif name == "SWAP": qml.SWAP(wires=params)
            else: raise ValueError(f"Unsupported gate: {name}")
        return qml.state()

    psi = np.asarray(circuit())
    n = int(np.log2(psi.size))
    psi_t = psi.reshape([2] * n)

    purities = []
    for k in range(n):
        axes = [k] + [i for i in range(n) if i != k]
        psi_k = np.transpose(psi_t, axes).reshape(2, -1)
        rho_k = psi_k @ psi_k.conj().T
        purities.append(np.real(np.trace(rho_k @ rho_k)))

    return float(2.0 * (1.0 - np.mean(purities)))

# ======================================================================
# Random circuit generator  
# ======================================================================

def generateCircuitListB(seed_:int = 232):
    gates = []
    rng = np.random.default_rng(seed=seed_)
    for _ in range(num_gates):
        g = rng.choice(single_qubit_gates + two_qubit_gates)
        if g in single_qubit_gates:
            wire = int(rng.integers(0, nqubits))
            if g == "H":
                gates.append(("H", [wire]))
            if g == "Z":
                gates.append(("Z", [wire]))
            elif g == "RY":
                angle = float(rng.choice(angles))
                gates.append(("RY", [angle, wire]))
        else:
            wires = [0, 0]
            while wires[0] == wires[1]:
                wires = rng.choice(nqubits, size=2, replace=False)
                wires = [int(el) for el in wires]
            gates.append((g.__str__(), wires))
    return gates

# ======================================================================
