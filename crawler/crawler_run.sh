REPOPATH=/home/ec2-user/Dev-jobis/crawler
cd $REPOPATH
echo $(pwd)

echo $(date) ... Start Crawling 
${PYENV_ROOT}/versions/pythoncrawling/bin/python wanted_crawler.py > test.log
echo $(date) ... Finish.