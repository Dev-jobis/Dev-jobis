#!/bin/bash
REPOPATH=/home/ec2-user/Dev-jobis/vector_db_pinecone
cd $REPOPATH
echo $(pwd)

echo $(date) ... Start Embedding
sudo docker run -it --rm -e AWS_ACCESS_KEY_ID=`cat .accesskeyid` -e AWS_SECRET_ACCESS_KEY=`cat .accesskey` embedding > test.log
echo $(date) ... Finish.