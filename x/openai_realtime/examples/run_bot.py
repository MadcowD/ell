#!/bin/bash

# Configure logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

run_discord_gpt4o() {
    while true; do
        log "INFO - Starting discord_gpt4o script..."
        python3 discord_gpt4o.py 2>&1 | while IFS= read -r line; do
            echo "$line"
            if echo "$line" | grep -qE "Unknown ssrc|error|Traceback \(most recent call last\):"; then
                log "WARNING - Detected 'Unknown ssrc', error, or error trace in output. Restarting..."
                pkill -f "python3 discord_gpt4o.py"
                break
            fi
        done

        if [ $? -ne 0 ]; then
            log "ERROR - discord_gpt4o encountered an error or needs restart. Restarting..."
        else
            log "INFO - discord_gpt4o finished successfully. Restarting..."
        fi

        log "INFO - Waiting for 5 seconds before restarting..."
        sleep 5
    done
}

log "INFO - Starting run_discord_gpt4o script"
run_discord_gpt4o
