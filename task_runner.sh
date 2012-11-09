#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$DIR/py2.7/bin/activate"
python -m task_manager.posting_task_runner <&0
