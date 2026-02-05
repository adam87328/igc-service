#!/bin/bash

# kill running session if exists
tmux kill-session -t igcservice

# Start a new named tmux session in detached mode. To attach, run
# $ tmux attach -t igcservice

tmux new-session -d -s igcservice
# Create three more horizontal panes for a total of four
tmux split-window -h -t igcservice:0.0
tmux split-window -h -t igcservice:0.1
tmux split-window -h -t igcservice:0.2

# xcmetrics 8081
tmux send-keys -t igcservice:0.0 'cd service/xcmetrics' C-m
tmux send-keys -t igcservice:0.0 'source .venv/bin/activate' C-m
tmux send-keys -t igcservice:0.0 'cd app' C-m
tmux send-keys -t igcservice:0.0 'uvicorn main:app --reload --port 8081 ' C-m

# geolookup 8082
tmux send-keys -t igcservice:0.1 'cd service/geolookup' C-m
tmux send-keys -t igcservice:0.1 'source .venv/bin/activate' C-m
tmux send-keys -t igcservice:0.1 'cd app' C-m
tmux send-keys -t igcservice:0.1 'uvicorn main:app --reload --port 8082 ' C-m

# xcscore   8083 
tmux send-keys -t igcservice:0.2 'cd service/xcscore' C-m
tmux send-keys -t igcservice:0.2 'source .venv/bin/activate' C-m
tmux send-keys -t igcservice:0.2 'cd app' C-m
tmux send-keys -t igcservice:0.2 'uvicorn main:app --reload --port 8083 ' C-m

# dem       8084
tmux send-keys -t igcservice:0.3 'cd service/dem' C-m
tmux send-keys -t igcservice:0.3 'source .venv/bin/activate' C-m
tmux send-keys -t igcservice:0.3 'cd app' C-m
tmux send-keys -t igcservice:0.3 'uvicorn main:app --reload --port 8084 ' C-m
