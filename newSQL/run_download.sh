#!/bin/bash

# Activate virtual environment and run the download script
cd "$(dirname "$0")/.."
source venv/bin/activate
python newSQL/download_data.py