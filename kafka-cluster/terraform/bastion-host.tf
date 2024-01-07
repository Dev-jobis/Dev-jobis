# 배스천 호스트 생성
resource "aws_instance" "bastion-host" {
  ami = var.bastion_ami_id
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.bastion.id]
  subnet_id = aws_subnet.public_subnet1.id
  associate_public_ip_address = true
#known_hosts 삭제
  user_data = <<-EOF
  #!/bin/bash
  sudo rm -rf /home/ec2-user/.ssh/known_hosts
  EOF
  tags = {
   Name = "bastion-host"
}
}
