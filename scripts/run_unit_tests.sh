#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
python -m pytest backend/tests
