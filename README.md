#README

##PROJECT GENERAL GOAL

This is the GPT_Entanglement git. In this project, we study the extent to which it is possible to synthesize entangling quantum circuits starting from a random one, and use it in an uphill-climbing process, where the circuit is represented now as a list of gates, passed to the LLM, and the output used to feed the circuit again in the next query. In this way, we implement a simple -one step - memory scheme during the resampling, in ML terms. Plus, we also add feedback that provides a criticism or a reward in the form of "you did better/worst of this amount X".

##REPO STRUCTURE

The basic codes used for running the experiments provided in the curretn draft can be found in the **article data** folder. Inside this folder also the experiments output for Table 3 and Table 4 can be found, to provide evidence. 

##PROJECT STRUCTURE

The current repo contains the full structure for running the start-from-best-outcomes experiments, with memory lake, as described in teh article draft. This is still underway -- an overlap of deadlines slowed down the testing -- but the structure of the project is finalised, and will be tested soon. 

For small, one round tests, the old basic code is provided. 

1.In **src** three files are stored: metric, model and utils. Inside metric, the Meyer-Wallach and the random circuit generation can be found. In model the API call to the GPT model and the chat pipe that handle the tags <python>...</python> where the output list must be inserted.

2.In **train** the test_time_learning file contains all the training procedure. The utils_b file contains the generate_initial_circuit function, used in the main() to produce the initial random circuit seed for the LLM.

3.The hill_climbing_random_benchmark is the model basleine, where the same logic of gate replacing is here used with a random sampler. 

4.Makefile contains instruction to run the test/test_time_learning.py file 3 times in a row, while the config sets up the metaparameters.
