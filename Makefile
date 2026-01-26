.PHONY: install run-3 run-10x3 run-nx3

install:
	python -m pip install -r requirements.txt

run-3: install
	@for i in 1 2 3; do \
		echo "Run $$i/3"; \
		ITERATION=$$i python train/test_time_learning.py; \
	done


run-nx3: install
	@EXP_COUNT=$${EXPERIMENTS:-10}; \
	for exp in $$(seq 1 $$EXP_COUNT); do \
		echo "Experiment $$exp/$$EXP_COUNT"; \
			EXPERIMENT_ID=$$exp python train/test_time_learning.py; \
		done; \
	done
