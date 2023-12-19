zookeeper 설치
--------------------

# zookeeper file download
	mkdir ~/download
	cd ~/download
	wget https://dlcdn.apache.org/zookeeper/zookeeper-3.8.3/apache-zookeeper-3.8.3-bin.tar.gz
	sudo tar zxvf apache-zookeeper-3.8.3-bin.tar.gz -C /usr/local

# 링크 생성

	cd /usr/local
	sudo chown -R root:root apache-zookeeper-3.8.3-bin
	sudo ln -s apache-zookeeper-3.8.3-bin zookeeper

# 환경변수 정보 파일에 입력
	echo "export PATH=\$PATH:/usr/local/zookeeper/bin:/usr/local/kafka/bin" |
	tee -a ~/.bash_profile > /dev/null
	source ~/.bash_profile

	sudo chown -R ec2-user: /usr/local/apache-zookeeper-3.8.3/


# zookeeper id 각 노드에 입력
## 첫번재 서버에서 
	mkdir -p /usr/local/zookeeper/data
	sudo chown -R ec2-user: /usr/local/zookeeper/
	echo 1 > /usr/local/zookeeper/data/myid
## 두번째 서버에서
	mkdir -p /usr/local/zookeeper/data
	sudo chown -R ec2-user: /usr/local/zookeeper/
	echo 2 > /usr/local/zookeeper/data/myid
## 세번째 서버에서
	mkdir -p /usr/local/zookeeper/data
	sudo chown -R ec2-user: /usr/local/zookeeper/
	echo 3 > /usr/local/zookeeper/data/myid

# zookeeper config 설정

	cd /usr/local/zookeeper/conf
	cp zoo_sample.cfg zoo.cfg

# vi zoo.cfg

# zookeeper 데이터 디렉토리
	dataDir=/usr/local/zookeeper/data
# zookeeper끼리 서로 통신하기 위한 포트
	server.1=kafka1:2888:3888
	server.2=kafka2:2888:3888
	server.3=kafka3:2888:3888

	admin.serverPort=8080

# zookeeper 서비스 생성

	sudo vi /etc/systemd/system/zookeeper.service


	[Unit]
	Description=Zookeeper Daemon
	Documentation=https://zookeeper.apache.org
	Requires=network.target
	After=network.target

	[Service]    
	Type=forking
	WorkingDirectory=/usr/local/zookeeper
	User=root
	Group=root
	ExecStart=/usr/local/zookeeper/bin/zkServer.sh start /usr/local/zookeeper/conf/zoo.cfg
	ExecStop=/usr/local/zookeeper/bin/zkServer.sh stop /usr/local/zookeeper/conf/zoo.cfg
	ExecReload=/usr/local/zookeeper/bin/zkServer.sh restart /usr/local/zookeeper/conf/zoo.cfg
	TimeoutSec=10
	Restart=on-abnormal

	[Install]
	WantedBy=default.target



# zookeeper 실행

	sudo systemctl daemon-reload
	sudo systemctl enable zookeeper
	sudo systemctl start zookeeper

# zookeeper 확인

	zkServer.sh status
