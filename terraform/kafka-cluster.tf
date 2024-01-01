# 카프카 1번 서버 생성
resource "aws_instance" "kafka-1" {
  ami           = "ami-087047855f4baf28e" # 카프카가 설치된 AMI
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.kafka-cluster.id]
  associate_public_ip_address = false
  subnet_id = aws_subnet.private_subnet1.id
  private_ip = "175.0.0.139"
  iam_instance_profile = data.aws_iam_instance_profile.existing_role.role_name # Fluentd S3 접근 허용
# 카프카 재시작 및 fluentd 시작
  user_data = <<-EOF
        #!/bin/bash
        sleep 15
        sudo systemctl restart kafka.service
        sudo systemctl enable --now fluentd.service
        EOF

  tags = {
    Name = "kafka-1"
  }
}

# 카프카 2번 서버 생성
resource "aws_instance" "kafka-2" {
  ami           = "ami-0cb037b024f1c40fb"
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.kafka-cluster.id]
  associate_public_ip_address = false
  subnet_id = aws_subnet.private_subnet2.id
  private_ip = "175.0.0.155"
# 카프카 재시작
  user_data = <<-EOF
        #!/bin/bash
        sleep 15
        sudo systemctl restart kafka.service
        EOF

  tags = {
    Name = "kafka-2"
  }
}
# 카프카 3번 서버 생성
resource "aws_instance" "kafka-3" {
  ami           = "ami-01e105c031276010f"
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.kafka-cluster.id]
  associate_public_ip_address = false
  subnet_id = aws_subnet.private_subnet3.id
  private_ip = "175.0.0.170"
# 카프카 재시작
  user_data = <<-EOF
        #!/bin/bash
        sleep 16
        sudo systemctl restart kafka.service
        EOF

  tags = {
    Name = "kafka-3"
  }
}