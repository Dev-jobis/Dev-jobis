# 카프카 1번 서버 생성
resource "aws_instance" "kafka-1" {
  ami           = var.ec2_ami_id
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.kafka-cluster.id]
  associate_public_ip_address = false
  subnet_id = aws_subnet.private_subnet1.id
  private_ip = "175.0.0.139"
  iam_instance_profile = data.aws_iam_instance_profile.existing_role.role_name # Fluentd S3 접근 허용
  tags = {
    Name = "kafka-1"
  }
}

# 카프카 2번 서버 생성
resource "aws_instance" "kafka-2" {
  ami           = var.ec2_ami_id
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.kafka-cluster.id]
  associate_public_ip_address = false
  subnet_id = aws_subnet.private_subnet2.id
  private_ip = "175.0.0.155"
  tags = {
    Name = "kafka-2"
  }
}
# 카프카 3번 서버 생성
resource "aws_instance" "kafka-3" {
  ami           = var.ec2_ami_id
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.kafka-cluster.id]
  associate_public_ip_address = false
  subnet_id = aws_subnet.private_subnet3.id
  private_ip = "175.0.0.170"
  tags = {
    Name = "kafka-3"
  }
}