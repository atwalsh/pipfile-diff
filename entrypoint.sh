#!/bin/sh
printf "Using $(python -V)\n"
pip install -r requirements.txt
python main.py
