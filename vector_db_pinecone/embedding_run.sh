#!/bin/bash
REPOPATH=/home/ec2-user/Dev-jobis/vector_db_pinecone
cd $REPOPATH
echo $(pwd)

echo $(date) ... Start Embedding
sudo docker run --rm -e AWS_ACCESS_KEY_ID=`cat $REPOPATH/.accesskeyid` -e AWS_SECRET_ACCESS_KEY=`cat $REPOPATH/.accesskey` embedding:20240107 2>&1 >> test.log
echo $(date) ... Finish.