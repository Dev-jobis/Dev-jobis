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

	$ curl -fsSL https://toolbelt.treasuredata.com/sh/install-redhat-fluent-package5-lts.sh | sh
	fluentd 환경설정

	$ sudo vi /etc/fluent/fluentd.conf

# fluentd 서비스 실행
	sudo systemctl start fluentd.service

# fluentd 정상 동작 확인
	curl -X POST -d 'json={"json":"message"}' http://localhost:8001/debug.test
	tail -n 1 /var/log/fluent/fluentd.log

'json={"json":"message"}을 볼수 있음