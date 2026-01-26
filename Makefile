.PHONY: install run-nx3

install:
	python -m pip install -r requirements.txt
	python -m pip install -e .


run-nx3: install
	@EXP_COUNT=$${EXPERIMENTS:-$$(python -c 'import configparser; c=configparser.ConfigParser(); c.read("config.ini"); print(c.get("training","experiments", fallback="10"))')}; \
	for exp in $$(seq 1 $$EXP_COUNT); do \
		echo "Experiment $$exp/$$EXP_COUNT"; \
		EXPERIMENT_ID=$$exp python train/test_time_learning.py; \
	done
