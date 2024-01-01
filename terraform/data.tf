# 이미 존재하는 IAM 역할 instance_profile 연결
data "aws_iam_instance_profile" "existing_role" {
  name = var.role_name
}