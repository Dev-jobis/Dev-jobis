# Nat gateway에서 사용할 Elastic IP
resource "aws_eip" "nat_ip" {
  domain   = "vpc"

  lifecycle {
    create_before_destroy = true
  }
}

# Nat gateway 생성
resource "aws_nat_gateway" "nat_gateway" {
  allocation_id = aws_eip.nat_ip.id

  subnet_id = aws_subnet.public_subnet1.id # 퍼블릭 서브넷에 생성

  tags = {
    Name = "NAT_gateway"
  }
}