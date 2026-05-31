.PHONY: clean clean-results clean-all run help

# Default target
help:
	@echo "Available targets:"
	@echo "  make clean         
	@echo "  make clean-all     
	@echo "  make run           
	@echo "  make install       

# Clean results folder
clean clean-results:
	rm -rf results/*.csv results/*.png

# Clean all
clean-all:
	rm -rf results/*.csv results/*.png
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Run experiments
run:
	python main.py --alphas 1.0,1.2 --fpr_targets 0.01 --results_dir results

# Install dependencies
install:
	pip install numpy pandas matplotlib

