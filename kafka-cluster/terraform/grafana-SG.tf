# 그라파나 프로메테우스 보안그룹 생성
resource "aws_security_group" "grafana" {
  name        = "kafka-cluster"
  description = "Allow port for grafana"
  vpc_id      = aws_vpc.project_vpc.id
# 그라파나 포트 허용
  ingress {
    description      = "grafana" 
    from_port        = 3000
    to_port          = 3000
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }
# 프로메테우스 포트 허용
   ingress {
    description      = "Prometheus"
    from_port        = 9090
    to_port          = 9090
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }


 ingress {
    description      = "ssh" 
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

 egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}