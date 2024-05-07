#!/bin/bash

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
	    echo "Usage: ./script.sh <interval_in_milliseconds> <total_count>"
	        exit 1
	fi

	# Get the interval and total count from the command-line arguments
	interval=$1
	total_count=$2

	# Convert interval from milliseconds to seconds for the 'sleep' command
	interval_in_seconds=$(echo "scale=3; $interval/1000" | bc)

	# Execute the tegrastats command for the specified number of times
	for (( i=1; i<=$total_count; i++ ))
	do
		    echo "$(date +%Y-%m-%d_%H:%M:%S) $(tegrastats --interval 1000)"
		        sleep $interval_in_seconds
		done
