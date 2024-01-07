# 프라이빗 서브넷 라우팅 테이블 생성
resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.ansible_vpc.id

  tags = {
    Name = "private_rt"
  }
}

# 라우팅 테이블 연결
resource "aws_route_table_association" "private_rt_association1" {
  subnet_id      = aws_subnet.private_subnet1.id
  route_table_id = aws_route_table.private_rt.id
}

resource "aws_route_table_association" "private_rt_association2" {
  subnet_id      = aws_subnet.private_subnet2.id
  route_table_id = aws_route_table.private_rt.id
}

resource "aws_route_table_association" "private_rt_association3" {
  subnet_id      = aws_subnet.private_subnet3.id
  route_table_id = aws_route_table.private_rt.id
}

# Nat게이트웨이 라우팅 테이블 추가
resource "aws_route" "private_rt_nat" {
  route_table_id              = aws_route_table.private_rt.id
  destination_cidr_block      = "0.0.0.0/0"
  nat_gateway_id              = aws_nat_gateway.nat_gateway.id
}                                                                                                                                                                                                                  