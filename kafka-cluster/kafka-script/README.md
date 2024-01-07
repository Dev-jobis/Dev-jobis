# 파이프라인 구축 스크립트
## 설치 순서
1. 주키퍼 설치
2. 카프카 설치
3. Fluentd 설치
--------------------
환경 설정
-------------------

# 자바 설치

	sudo yum install java-17-amazon-corretto -y

# etc/hosts 파일에 해당 정보 입력

	sudo vi /etc/hosts

	<PRIVATE-IP1> kafka1
	<PRIVATE-IP2> kafka2
	<PRIVATE-IP1> kafka3


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
## 첫번째 서버에서 
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
---------------------
카프카 설치
---------------------
# kafka download
	mkdir download
	cd download
	wget https://archive.apache.org/dist/kafka/2.8.2/kafka_2.13-2.8.2.tgz

	sudo tar xvf kafka_2.13-2.8.2.tgz -C /usr/local

# 링크 생성

	cd /usr/local
	sudo ln -s kafka_2.13-2.8.2 kafka

# 카프카 서버 설정

	sudo mkdir -p /usr/local/kafka/logs
	sudo chown -R ec2-user: /usr/local/kafka_2.13-2.8.2
	vi /usr/local/kafka/config/server.properties



	
	broker.id=<your broker id>	
	isteners=PLAINTEXT://:9092
	<-- 주석해제
	# listeners
	- 카프카 브로커가 내부적으로 바인딩하는 주소.
	# advertised.listeners
	- 카프카 프로듀서, 컨슈머에게 노출할 주소 이며 설정하지 않을 경우 디폴트로 listners 설정이 적용됩니다.
	- listeners 포트와 advertised.listeners 포트를 다르게 사용하지 않을 경우 listeners 옵션만 주석해제를 	해도 됩니다.
	## 토픽의 파티션 세그먼트가 저장될 로그 디렉토리 위치 경로를 입력 합니다.
	## 포스팅에서는 해당 경로를 위에서 생성 하였습니다.
	log.dirs=/usr/local/kafka/logs
	## 주키퍼 정보를 입력하면 되며, 주키퍼 앙상블로 구성하였기 때문에 3개의 주키퍼 정보를 모두 입력 해야 합	니다.
	## 3개의 클러스터인 만큼 그 다음 클러스터들을 다 쓴다음 맨 뒤에
	## /kafka-test-1 라고 포스팅에서는 추가하도록 하겠습니다.
	## 사용하는 이유는 znode 의 디렉토리를 루트노드가 아닌 하위 디렉토리로 설정해 주는 의미로 하나의 주키퍼	에서 여러 클러스터를 구동할 수 있게 하기 위해서 입니다.
	## 명칭은 kafka-test-1 로 하지않아도 되며 포스팅에서의 예시 입니다.
	## 그래서 아래와 같이 작성 하면 됩니다
	zookeeper.connect=kafka1:2181,kafka2:2181,kafka3:2181/kafka-test-1

# 카프카 서비스 생성

	sudo vi /etc/systemd/system/kafka.service

	[Unit]
	Description=Apache Kafka server (broker)
	Requires=network.target remote-fs.target zookeeper.service
	After=network.target remote-fs.target zookeeper.service
	[Service]
	Type=forking
	User=root
	Group=root
	Environment='KAFKA_HEAP_OPTS=-Xms500m -Xmx500m'
	ExecStart=/usr/local/kafka/bin/kafka-server-start.sh -daemon 	/usr/local/kafka/config/server.properties
	ExecStop=/usr/local/kafka/bin/kafka-server-stop.sh
	LimitNOFILE=16384:163840
	Restart=on-abnormal
	[Install]
	WantedBy=multi-user.target

# 서비스 실행

	sudo systemctl daemon-reload
	sudo systemctl enable kafka
	sudo systemctl start kafka
-----------------
Fluentd 설치
-----------------

# fluentd 환경 설정

	ulimit -n

	65536

	sudo vi /etc/sysctl.conf

	net.core.somaxconn = 1024
	net.core.netdev_max_backlog = 5000
	net.core.rmem_max = 16777216
	net.core.wmem_max = 16777216
	net.ipv4.tcp_wmem = 4096 12582912 16777216
	net.ipv4.tcp_rmem = 4096 12582912 16777216
	net.ipv4.tcp_max_syn_backlog = 8096
	net.ipv4.tcp_slow_start_after_idle = 0
	net.ipv4.tcp_tw_reuse = 1
	net.ipv4.ip_local_port_range = 10240 65535
	# If forward uses port 24224, reserve that port number for use as an ephemeral port.
	# If another port, e.g., monitor_agent uses port 24220, add a comma-separated list of port 	numbers.
	# net.ipv4.ip_local_reserved_ports = 24220,24224
	net.ipv4.ip_local_reserved_ports = 24224

# fluentd 다운로드 및 설치

	$ curl -fsSL https://toolbelt.treasuredata.com/sh/install-amazon2023-fluent-package5-lts.sh | sh
	fluentd 환경설정

	$ sudo vi /etc/fluent/fluentd.conf

# fluentd 서비스 실행
	sudo systemctl start fluentd.service

# fluentd 정상 동작 확인
	curl -X POST -d 'json={"json":"message"}' http://localhost:8001/debug.test
	tail -n 1 /var/log/fluent/fluentd.log

'json={"json":"message"}을 볼수 있음