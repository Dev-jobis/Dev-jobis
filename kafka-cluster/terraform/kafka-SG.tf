# 카프카 클러스터 보안 그룹 생성
resource "aws_security_group" "kafka-cluster" {
  name        = "kafka-cluster"
  description = "Allow port for kafka-cluster"
  vpc_id      = aws_vpc.project_vpc.id

  ingress {
    description      = "inter Zookeeper Port" # 주키퍼간 통신 포트
    from_port        = 3888
    to_port          = 3888
    protocol         = "tcp"
    cidr_blocks      = [aws_vpc.project_vpc.cidr_block]
  }

   ingress {
    description      = "inter Zookeeper Port" # 주키퍼간 통신 포트
    from_port        = 2888
    to_port          = 2888
    protocol         = "tcp"
    cidr_blocks      = [aws_vpc.project_vpc.cidr_block]
  }


 ingress {
    description      = "broker to zookeeper port" # 브로커와 주키퍼 네트워크 포트
    from_port        = 2181
    to_port          = 2181
    protocol         = "tcp"
    cidr_blocks      = [aws_vpc.project_vpc.cidr_block]
  }


 ingress {
    description      = "ssh" # SSH 허용
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = [aws_vpc.project_vpc.cidr_block]
  }

 ingress {
    description      = "Access to Broker" # 브로커 접근 포트
    from_port        = 9092
    to_port          = 9092
    protocol         = "tcp"
    cidr_blocks      = [aws_vpc.project_vpc.cidr_block]
  }

ingress {
    description      = "To Prometheus" # 프로메테우스로 metric 전송 포트
    from_port        = 7071
    to_port          = 7071
    protocol         = "tcp"
    cidr_blocks      = [aws_vpc.project_vpc.cidr_block]
  }


  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}