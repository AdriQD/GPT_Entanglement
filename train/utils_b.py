

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import logging
from src.metric import MeyerWallach, generateCircuitListB




#=====================================================================
# Memory Logger Class, FUTURE DEVELOPMENT

class MemoryLogger:
    """
    Research-grade memory lake logger for LLM-driven experiments.
    Creates structured run folders, logs prompts/responses/circuits,
    and adds cryptographic hashes for reproducibility.
    """

    def __init__(self, experiment_name: str, base_dir: str = "runs"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.experiment_name = experiment_name
        self.run_root = Path(base_dir) / experiment_name / timestamp
        self.run_root.mkdir(parents=True, exist_ok=True)

        # Save metadata file
        meta = {
            "experiment_name": experiment_name,
            "timestamp": timestamp,
            "base_dir": str(self.run_root),
        }
        self._save_json(self.run_root / "meta.json", meta)

    # -----------------------
    # Hashing utilities
    # -----------------------
    @staticmethod
    def compute_hash(data: Any) -> str:
        """Compute SHA256 hash of any JSON-serializable object or string."""
        if isinstance(data, (dict, list)):
            data = json.dumps(data, sort_keys=True)
        if not isinstance(data, str):
            data = str(data)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    # -----------------------
    # Logging
    # -----------------------
    def log_iteration(
        self,
        run_id: int,
        iteration: int,
        prompt: str,
        raw_response: str,
        initial_circuit: Any,
        generated_circuit: Any,
        metrics: Dict[str, Any],
    ):
        """
        Save all artifacts + hashes for one iteration.
        """

        iter_dir = self.run_root / f"run_{run_id:02d}" / f"iter_{iteration:04d}"
        iter_dir.mkdir(parents=True, exist_ok=True)

        # Save raw artifacts
        self._save_text(iter_dir / "prompt.txt", prompt)
        self._save_text(iter_dir / "response.txt", raw_response)
        self._save_json(iter_dir / "initial_circuit.json", initial_circuit)
        self._save_json(iter_dir / "generated_circuit.json", generated_circuit)

        # Compute hashes
        record = {
            "run_id": run_id,
            "iteration": iteration,
            "experiment_name": self.experiment_name,
            "metrics": metrics,
            "prompt_hash": self.compute_hash(prompt),
            "raw_response_hash": self.compute_hash(raw_response),
            "initial_circuit_hash": self.compute_hash(initial_circuit),
            "generated_circuit_hash": self.compute_hash(generated_circuit),
        }

        # Hash the full record itself (tamper-evident)
        record["record_hash"] = self.compute_hash(record)

        # Save record
        self._save_json(iter_dir / "record.json", record)

    # -----------------------
    # Helpers
    # -----------------------
    def _save_json(self, path: Path, data: Any):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def _save_text(self, path: Path, text: str):
        with open(path, "w") as f:
            f.write(text)


def generate_initial_circuit(seed_:int = 1):

    #=====================================================================
    # Generating initial random low-entanglement circuit with MW between 0.2 and 0.4
    #====================================================================

    logging.info("Generating initial random low-entanglement circuit...")
    best_Q = 0.0
    while True:
        initial_gates = generateCircuitListB(seed=seed_)
        best_gates = initial_gates
        initial_Q = MeyerWallach(initial_gates)
        best_Q = initial_Q
        seed_+=7
        print(best_Q)
        if best_Q>0.2 and best_Q<0.4: 
            logging.info(f'best Q_value obtained from random circuit is {best_Q}')
            break
    return best_gates, best_Q