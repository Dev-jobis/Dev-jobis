# 인터넷 게이트웨이 생성
resource "aws_internet_gateway" "IGW" {
  vpc_id = aws_vpc.project_vpc.id

  tags = {
    Name = "project_vpc_IGW"
  }
}
# 퍼블릭 서브넷 라우팅 테이블 생성
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.project_vpc.id
# 인터넷 게이트 웨이 라우팅 테이블 설정
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.IGW.id
  }
  tags = {
   Name = "public_rt"
  }
}
# 퍼블릭 서브넷과 라우팅 테이블 연결
resource "aws_route_table_association" "public_rt_association_1" {
  subnet_id  =  aws_subnet.public_subnet1.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_rt_association_2" {
  subnet_id      = aws_subnet.public_subnet2.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_rt_association_3" {
  subnet_id      = aws_subnet.public_subnet3.id
  route_table_id = aws_route_table.public_rt.id
}