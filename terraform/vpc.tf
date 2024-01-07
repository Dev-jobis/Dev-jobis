# VPC 생성
resource "aws_vpc" "project_vpc" {
  cidr_block = "175.0.0.0/24"

  tags = {
    Name = "project"
  }
}
# 퍼블릭 서브넷 생성 및 설정
resource "aws_subnet" "public_subnet1" {
  vpc_id = aws_vpc.project_vpc.id
  cidr_block = "175.0.0.0/28"

  availability_zone = "ap-northeast-2a"

  tags = {
    Name = "public_subnet1"
  }
}

resource "aws_subnet" "public_subnet2" {
  vpc_id = aws_vpc.project_vpc.id
  cidr_block = "175.0.0.16/28"

  availability_zone = "ap-northeast-2b"

  tags = {
    Name = "public_subnet2"
  }
}


resource "aws_subnet" "public_subnet3" {
  vpc_id = aws_vpc.project_vpc.id
  cidr_block = "175.0.0.32/28"

  availability_zone = "ap-northeast-2c"

  tags = {
    Name = "public_subnet3"
  }
}

resource "aws_subnet" "private_subnet1" {
  vpc_id = aws_vpc.project_vpc.id
  cidr_block = "175.0.0.128/28"

  availability_zone = "ap-northeast-2a"

  tags = {
    Name = "private_subnet1"
  }
}
# 프라이빗 서브넷 생성 및 설정
resource "aws_subnet" "private_subnet2" {
  vpc_id = aws_vpc.project_vpc.id
  cidr_block = "175.0.0.144/28"

  availability_zone = "ap-northeast-2b"

  tags = {
    Name = "private_subnet2"
  }
}

resource "aws_subnet" "private_subnet3" {
  vpc_id = aws_vpc.project_vpc.id
  cidr_block = "175.0.0.160/28"

  availability_zone = "ap-northeast-2c"

  tags = {
    Name = "private_subnet3"
  }
}
                      