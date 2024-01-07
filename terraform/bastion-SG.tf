# bastion-host 보안 그룹 
resource "aws_security_group" "bastion" {
  name = "bastion"
  description = "bastion"
  vpc_id =  aws_vpc.project_vpc.id

# SSH 허용
 ingress {
    description      = "allow SSH"
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