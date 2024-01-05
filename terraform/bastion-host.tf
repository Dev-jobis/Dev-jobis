# 배스천 호스트 생성
resource "aws_instance" "bastion-host" {
  ami = var.ec2_ami_id
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.bastion.id]
  subnet_id = aws_subnet.public_subnet1.id
  associate_public_ip_address = true
#known_hosts 삭제
  user_data = <<-EOF
  #!/bin/bash
  sudo dnf install python3.11 -y
  sudo dnf install python3.11-pip -y
  cd /usr/bin
  ln -s /usr/bin/python3.11 python
  python -m pip install --user ansible
  EOF

  tags = {
   Name = "bastion-host"
}
}
