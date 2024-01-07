#!/bin/bash
REPOPATH=/home/ec2-user/Dev-jobis/crawler
PYENV_ROOT=/home/ec2-user/.pyenv
echo "PYENV_ROOT : $PYENV_ROOT"

cd $REPOPATH
echo $(pwd)

echo $(date) ... Start Crawling 
${PYENV_ROOT}/versions/pythoncrawling/bin/python wanted_crawler.py > test.log
echo $(date) ... Finish.