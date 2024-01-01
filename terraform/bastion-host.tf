# 배스천 호스트 생성
resource "aws_instance" "bastion-host" {
  ami = "ami-0f2061304b4ee7111"
  instance_type = var.ec2_instance_type
  key_name = "project0key"
  vpc_security_group_ids = [aws_security_group.bastion.id]
  subnet_id = aws_subnet.public_subnet1.id
  associate_public_ip_address = true
  tags = {
   Name = "bastion-host"
}
}
