#!/bin/bash

# Start a new named tmux session in detached mode. To attach, run
# $ tmux attach -t igcservice
# $ tmux kill-session -t igcservice
tmux new-session -d -s igcservice

# Split the first pane horizontally
tmux split-window -h

# Split the first pane vertically
tmux split-window -v

# Split the second pane vertically
tmux select-pane -t 1
tmux split-window -v

# xcmetrics 8081
tmux send-keys -t igcservice:0.0 'cd xcmetrics/app' C-m
tmux send-keys -t igcservice:0.0 'uvicorn main:app --reload --port 8081 ' C-m

# geolookup 8082
tmux send-keys -t igcservice:0.1 'cd geolookup/app' C-m
tmux send-keys -t igcservice:0.1 'uvicorn main:app --reload --port 8082 ' C-m

# xcscore   8083 
tmux send-keys -t igcservice:0.2 'cd xcscore/app' C-m
tmux send-keys -t igcservice:0.2 'uvicorn main:app --reload --port 8083 ' C-m
