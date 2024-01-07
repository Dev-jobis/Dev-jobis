## embedding docker image

1) .accesskeyid 파일에 AWS_ACCESS_KEY_ID 를, .accesskey 파일에 AWS_SECRET_ACCESS_KEY를 넣는다. 해당 파일이 git에 올라가지 않도록 주의한다. 
2) 아래 방법으로 docker를 실행한다. 
```
# 최초 1회 docker 생성
$ sudo docker build -t embedding . 

# shell script + crontab으로 주기적으로 돌리기
$ sudo docker run -it --rm \
  -e AWS_ACCESS_KEY_ID=`cat .accesskeyid` \
  -e AWS_SECRET_ACCESS_KEY=`cat .accesskey` \
  embedding
```