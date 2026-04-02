#!/bin/bash
# run_tests.sh - Test runner script with coverage reporting

echo "---------------------------------------------------------"
echo "AI Stock Screener - Automated Testing Suite"
echo "---------------------------------------------------------"

# 1. Activate virtual environment (if present)
if [ -d "venv" ]; then
    source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
fi

# 2. Run all tests with pytest
echo "[1/2] Running Core, API, Portfolio and Integration Tests..."
python -m pytest tests/ -v --tb=short

# 3. Show test coverage report
echo "[2/2] Generating Code Coverage Report..."
python -m pytest --cov=backend tests/

echo "---------------------------------------------------------"
echo "Done."
echo "---------------------------------------------------------"
