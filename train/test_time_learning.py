
import os
from  numpy import save, array, load, hstack
import re
from pathlib import Path
import json
import logging
from train.utils_b import generate_initial_circuit
import re
import unicodedata
from pathlib import Path

import ast

from src.utils import normalize_gates_list
from src.metric import MeyerWallach
from src.model import chat_with_oss_python_block, MODEL_NAME

from configparser import ConfigParser

#=====================================================================
# Load configuration adn time stamp
#=====================================================================

config = ConfigParser()
config.read('config.ini')

nqubits = config.getint('quantum', 'nqubits')
angles_ = config.get('quantum', 'angles').split(',')
seed_value = config.getint('quantum', 'seed_value')

experiment = config.get('training', 'experiment_name', fallback='default_experiment')
experiment_id = os.getenv("EXPERIMENT_ID", "").strip()
single_qubit_gates = config.get('quantum', 'single_qubit_gate_set').split(',')
two_qubit_gates = config.get('quantum', 'two_qubit_gate_set').split(',')
set_of_gates = set(single_qubit_gates + two_qubit_gates)

from datetime import datetime

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
print(timestamp)  # e.g., 2026-01-24_14-37-08
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')     


# ======================================================================
# Iterative optimization loop (unchanged)
# ======================================================================


max_iterations = config.getint('training', 'max_iterations', fallback=15)
num_gates = config.getint('quantum', 'num_gates', fallback=25)

#experiment_tag = f"{experiment}_id{experiment_id}" if experiment_id else experiment
experiment_folder = Path(f"exp_{experiment}_{experiment_id}")
Path(experiment_folder).mkdir(parents=True, exist_ok=True)


# ======================================================================
# Model prompting wrapper
# ======================================================================

def prompt_local_model(gates, feedback ,set_of_gates, angles):
    angles_str = ", ".join(angles)
    gates_str = ", ".join(set_of_gates)
    system_template = config.get(
        'prompt',
        'system_message',
        fallback=(
            "You are an expert in PennyLane circuits and entanglement. "
            "Modify each tuple using only gates from {set_of_gates}. "
            "Use angles from {angles} for the RY gate. "
            "Use ASCII only. "
            "The evaluation metric of the circuit's performance is {metric}."
        ),
    )
    system = system_template.format(
        set_of_gates=gates_str,
        angles=angles_str,
        nqubits=nqubits,
        metric="Meyer-Wallach global entanglement",
    )

    user_template = config.get(
        'prompt',
        'user_message',
        fallback=(
            "You are given a quantum circuit list of tuples. "
            "GOAL: Think step-by-step, you want to improve the Meyer_wallach "
            "entanglement of the new state you create by modifying the list "
            "{gates} obtaining an {feedback}. "
            "Allowed gates: {set_of_gates}. "
            "Transform the circuit substantially, not minimally. Do NOT "
            "produce minor edits to the previous version—aim for creative leaps. "
            "Think step-by-step, like an experimental quantum designer: search "
            "for surprising, high-entanglement patterns by creatively reshaping "
            "the circuit architecture. "
            "Do NOT add explanations, comments or code fences. "
            "Everything between <python> and </python> must be valid LIST. "
            "Each gate must be one of:\n"
            "  ['H', [wire]]\n"
            "  ['RY', [angle, wire]]\n"
            "  ['CNOT', [control_wire, target_wire]]\n"
            "Where wire is an integer from 0 to {nqubits_minus_one} and angle "
            "is one of {angles}. "
            "IMPORTANT: do not add or remove gates, only modify existing ones."
        ),
    )
    user_prompt = user_template.format(
        gates=gates,
        feedback=feedback,
        set_of_gates=gates_str,
        angles=angles_str,
        nqubits=nqubits,
        nqubits_minus_one=nqubits - 1,
    )
    # Save prompts for record-keeping
    prompts_path = experiment_folder / "prompts.json"
    if not prompts_path.exists():
        with open(prompts_path, "w", encoding="utf-8") as f:
            json.dump({"system_prompt": system, "user_prompt": user_prompt}, f, indent=2)
        logging.info("Using model: %s", MODEL_NAME)
    else:
        pass

    return chat_with_oss_python_block(system, user_prompt)


def the_experiment_main( file_iteration:int, max_iterations:int, file_run,experiment_folder):


    #=====================================================================
    # If resuming from a previous run, load the best circuit
    # from memory, otehrwise start from initial circuit
    #====================================================================

    feed = 'no improvement at the zero step'

    if file_iteration>1:
        with open(experiment_folder / f"run_{file_iteration-1}" / 'best_circuit.json','r') as f:
            data = json.load(f)
            best_gates = data["gates"]
            best_Q = data["Q"]
        logging.info(f"Resuming best circuit from previous iteration {file_iteration-1}")

    if file_iteration==1:
        logging.info("Starting from iteration 1 with initial circuit.")
        with open(file_run / 'initial_circ.json', 'r') as f:
            initial_circ = json.load(f)
            best_gates = initial_circ["gates"]
            best_Q = initial_circ["Q"]

    #=====================================================================
    # Starting iterative improvement ...
    #=====================================================================        
    Q_list =[]
    Q_relativeGains =[]

    for i in range(max_iterations):
        print(f"\nIteration {i+1}/{max_iterations}")
    
        response = prompt_local_model(gates = best_gates, 
                                      feedback= feed, 
                                      set_of_gates= set_of_gates,
                                      angles= angles_)
        
        if response:
            try:
                s = response.find("<python>")
                e = response.find("</python>")
                if s != -1 and e != -1:
                    content = response[s+8:e].strip()

                    #==============================================================================
                    #normalize unicode characters for cleaning eventual drift in the model output
                    #==============================================================================

                    content = unicodedata.normalize("NFKC", content)

                    #==============================================================================
                    #parse the proposed gates list
                    #==============================================================================

                    proposed = ast.literal_eval(content)
                    #normalize in the expected outcome for the list values inside gates
                    proposed = normalize_gates_list(proposed, nqubits)
                    #print("proposed:  ", proposed)
            
                    Qval = MeyerWallach(proposed)

                    #==============================================================================
                    #SAVE ITERATION DATA TO FILE
                    #============================================================================== 

                    iteration_data = {"proposed_gates": proposed}

                    Q_list.append(Qval)
                    Q_relativeGains.append(Qval-best_Q)
                    with open(file_run / f'circuitQuery_{i}.json', 'w') as f:
                        json.dump(iteration_data, f)

                    #==============================================================================
                    #compare with the best found so far and prepare feedback for the next iteration
                    #==============================================================================

                    if Qval < best_Q:
                        l = Qval-best_Q
                        feed = 'you performed lesser of an amount {}'.format(l)
                    if Qval > best_Q:
                        
                        g = Qval-best_Q
                        best_Q = Qval
                        best_gates = proposed
                        logging.info('NEW BEST Q: {}'.format(best_Q))
                        feed = 'you performed better of an amount {}'.format(g)
        
                    else:
                        print("No improvement.")

            except Exception as e:
                logging.error("  Error: %s", e)

    logging.info(f"Finished loop {file_iteration}.")
    print("Best Q:", best_Q)

    #=====================================================================
    # SAVING STATISTICS
    #====================================================================
    return Q_list, Q_relativeGains
    

#=====================================================================
# Main execution
#=====================================================================

if __name__ == "__main__":

    #file_iteration = int(os.getenv("ITERATION", "0"))
    file_iteration = 3  # For testing purposes, set iteration here
    logging.info(f"Starting experiment iteration {file_iteration}...")
    

    #=====================================================================
    # Starting iterative improvement (local OSS model)
    #====================================================================


    logging.info("\n Starting iterative improvement (GPT model)...")
    for i in range(1, file_iteration + 1):

        file_run = Path(experiment_folder / f"iteration_{i}")
        file_run.mkdir(parents=True, exist_ok=True)

        if i == 1:

            #=====================================================================
            # Generating initial random low-entanglement circuit with MW between 0.2 and 0.4
            #====================================================================

            logging.info("Generating initial circuit at file run 1...")
            best_gates, best_Q = generate_initial_circuit(seed_=seed_value)
            initial_circuit = {"gates": best_gates, "Q": best_Q}
            logging.info("\n Saving initial circuit")

            #===============================================
            # SAVING INITIAL CIRCUIT AT FILE RUN 0
            #===============================================
            with open(file_run / 'initial_circ.json', 'w') as f:
                json.dump(initial_circuit, f)

        logging.info(f"\n Starting experiment iteration {i}...")
        Qlist, QRelativeGain = the_experiment_main(i , max_iterations, file_run, experiment_folder)
        logging.info(f"Experiment {i} completed.")

        stats_folder = Path(f"./stats/ stats_from_iteration_{i}")
        stats_folder.mkdir(parents=True, exist_ok=True) 

        #=====================================================================
        # First we create the null files for easier data handling, then we save the actual data
        # stats from each experiment inside them
        #====================================================================


        if experiment_id == 1:  
            save(stats_folder / f'Q_values.npy', array([0]*max_iterations))
            save(stats_folder / f'Q_relativeGains.npy', array([0]*max_iterations))

        oldQlist = load(stats_folder / f'Q_values.npy')
        oldQRelativeGains = load(stats_folder / f'Q_relativeGains.npy')

        newQlist = hstack((oldQlist, array(Qlist)))
        newQRelativeGains = hstack((oldQRelativeGains, array(QRelativeGain)))

        save(stats_folder/ f'Q_values_{experiment_id}.npy', newQlist)
        save(stats_folder / f'Q_relativeGains_{experiment_id}.npy', newQRelativeGains)

