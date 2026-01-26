

    #=====================================================================
    #checking the iteration filel number from environment variable
    #=====================================================================
import logging


file_iteration = int(os.getenv("ITERATION", "0"))

#=====================================================================
#create memory-folder for this experiment run, inside the experiment folder
#=====================================================================

file_run = Path(experiment_folder / f"run_{file_iteration}")
file_run.mkdir(parents=True, exist_ok=True)
#for k in range(3):  # Run 3 independent optimization runs

    if file_iteration == 0:

        logging.info("Generating initial circuit...")
        best_gates, best_Q = generate_initial_circuit()
        initial_circuit = {"gates": best_gates, "Q": best_Q}
        logging.info("Saving initial circuit")

        #===============================================
        # SAVING INITIL CIRCUIT AT FILE RUN 0
        #===============================================
        with open(file_run / f'query_{0}', 'w') as f:
            json.dump(initial_circuit, f)


    logging.info("Starting iterative improvement ...")

    #zero step feed, it is the same for every file iteration
    feed = 'no improvement at the zero step'


    #=======================================================
    # If resuming from a previous run, load the best circuit 
    # from memory 
    #=======================================================


        
    if file_iteration>0:
        logging.info(f"Resuming from previous iteration {file_iteration-1}, loading best from memory...")
        folder = experiment_folder / f"run_{file_iteration-1}"
        pattern = re.compile(r"query_(\d+)")
        candidates = []
        for path in folder.iterdir():
            if path.is_file():
                match = pattern.search(path.name)
                if match:
                    candidates.append((int(match.group(1)), path))
        if not candidates:
            raise FileNotFoundError("No files matching 'query_<n>' found")
        #pick the file with the highest query  iteration number
        _, newest = max(candidates, key=lambda item: item[0])

        with newest.open("r", encoding="utf-8") as f:
            data = f.read()

        #REPLACE THE CONTENTS OF best_gates WITH THE ONES LOADED FROM FILE    
        best_gates = json.loads(data)["gates"]

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
                        
                        with open(file_run / f'query_{i}','w') as f: 
                            
                            json.dump({"gates": best_gates, "Q": best_Q}, f)
                        
                    else:
                        print("No improvement.")

            except Exception as e:
                logging.error("  Error: ", e)

    logging.info(f"Finished loop {file_iteration}.")
    print("Best Q:", best_Q)
