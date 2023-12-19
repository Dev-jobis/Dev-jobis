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

