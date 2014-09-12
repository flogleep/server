#!/bin/bash

while true; do
    scrapy crawl -L INFO ratp >> ./logs/ratp.log 2>&1 &
    scrapy crawl -L INFO sncf >> ./logs/sncf.log 2>&1 &
    python /root/chain/controller.py >> ./logs/chain.log 2>&1 &
    wait
    sleep 10
done
