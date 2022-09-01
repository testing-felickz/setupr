#!/bin/bash
# -*- coding: utf-8 -*-
if [ -t 0 ]; then
    echo "There is a tty thus we have colour…"
    error=$(tput setaf 9) # bright red.
    success=$(tput setaf 2) # normal green.
    warning=$(tput setaf 214) # orange.
    info=$(tput setaf 99) # purple.
    header=$(tput setaf 69) # light blue.
    reset=$(tput sgr0)
else
    echo "There is no tty thus we do not have colour…"
    error="(error) "
    success="(success) "
    warning="(warning) "
    info="(info) "
    header="(header) "
    reset=""
fi
allMessages=(
    "${success}√ good"
    "${error}✗ bad${reset}"
    "${warning} warn${reset}"
    "${header}隻狼${reset}"
    "${info}elden ring${reset}"
"no formating" )
for ((i=0; i<=5; i++)); do
    sleep 0.6
    echo "${allMessages[$i]}"
done
exit "${1-0}"
