REPOPATH=/home/ec2-user/Dev-jobis/crawler
cd $REPOPATH
echo $(pwd)
pyenv activate pythoncrawling

echo $(date) ... Start Crawling 
python wanted_crawler.py > test.log
echo $(date) ... Finish.