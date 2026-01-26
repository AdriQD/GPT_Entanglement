def _flatten_single(x):
    """
    Riduci annidamenti banali:
      [[0]]        → 0
      [0]          → 0
      (0,)         → 0
      [[7.0, 0]]   → [7.0, 0]
    """
    while isinstance(x, (list, tuple)) and len(x) == 1:
        x = x[0]
    return x

def _load_config_angles():
    """
    Load allowed RY angles from config.ini.
    Falls back to an empty set if config is missing or malformed.
    """
    try:
        from configparser import ConfigParser
        config = ConfigParser()
        config.read("config.ini")
        angles_raw = config.get("quantum", "angles", fallback="")
        angles = []
        for a in angles_raw.split(","):
            a = a.strip()
            if not a:
                continue
            angles.append(float(a))
        return set(angles)
    except Exception:
        return set()


def normalize_gates_list(gates, nqubits, allowed_angles=None):
    """
    Normalizza i gate in un formato consistente:

      - ("H", 0)            → ("H", [0])
      - ("H", [0])          → ("H", [0])
      - ("H", [[0]])        → ("H", [0])

      - ("RY", 7.0, 0)      → ("RY", [7.0, 0])
      - ("RY", 0, 7.0)      → ("RY", [7.0, 0])  # usa euristica (angolo, wire)
      - ("RY", [7.0, 0])    → ("RY", [7.0, 0])
      - ("RY", [[7.0, 0]])  → ("RY", [7.0, 0])

      - ("CNOT", 0, 1)      → ("CNOT", [0, 1])
      - ("CNOT", [0, 1])    → ("CNOT", [0, 1])
      - ("CNOT", [[0, 1]])  → ("CNOT", [0, 1])
    """
    if allowed_angles is None:
        allowed_angles = _load_config_angles()
    allowed_angles = set(allowed_angles) if allowed_angles else set()
    fixed = []

    for item in gates:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            raise ValueError(f"Gate must be at least (name, ...), got: {item}")

        name = str(item[0])
        raw_params = list(item[1:])  # tutto ciò che viene dopo il nome

        # Se c'è un solo parametro ed è una lista/tupla, aprila:
        # es. ("RY", [7.0, 0]) → params = [7.0, 0]
        if len(raw_params) == 1 and isinstance(raw_params[0], (list, tuple)):
            params = list(raw_params[0])
        else:
            params = raw_params

        # flattiamo eventuali annidamenti tipo [[0]] o [[7.0, 0]]
        params = [_flatten_single(p) for p in params]

        # ---------------------------
        # 1-qubit gates: H, Z
        # ---------------------------
        if name in ("H", "Z"):
            if len(params) == 0:
                raise ValueError(f"{name} gate needs one wire, got: {item}")
            wire = int(_flatten_single(params[0]))
            fixed.append((name, [wire]))

        # ---------------------------
        # RY: angolo + wire
        # ---------------------------
        elif name == "RY":
            if len(params) < 2:
                raise ValueError(f"RY gate needs (angle, wire), got: {item}")

            a = _flatten_single(params[0])
            b = _flatten_single(params[1])

            angle = None
            wire = None

            try:
                fa = float(a)
            except Exception:
                fa = None
            try:
                fb = float(b)
            except Exception:
                fb = None

            # euristica: angolo tra quelli permessi, wire tra 0 e nqubits-1
            if fa in allowed_angles and isinstance(b, int) and 0 <= b < nqubits:
                angle, wire = fa, b
            elif fb in allowed_angles and isinstance(a, int) and 0 <= a < nqubits:
                angle, wire = fb, a
            else:
                # fallback: assumo (angle, wire)
                angle = float(a)
                wire = int(b)

            fixed.append(("RY", [angle, wire]))

        # ---------------------------
        # 2-qubit gates: CNOT, SWAP
        # ---------------------------
        elif name in ("CNOT", "SWAP"):
            if len(params) < 2:
                raise ValueError(f"{name} gate needs two wires, got: {item}")
            w0 = int(_flatten_single(params[0]))
            w1 = int(_flatten_single(params[1]))
            fixed.append((name, [w0, w1]))

        else:
            raise ValueError(f"Unsupported gate from model: {name}")

    return fixed

def format_duration(seconds):
    """
    Formatta una durata in secondi in una stringa leggibile,
    es. 3661 → "1h 1m 1s"
    """
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)
