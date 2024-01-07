variable "region_name" {
  description = "Region to create the resources"
  type = string
}

variable "ec2_instance_type" {
  description = "default instance type"
  type = string
}

variable "role_name" {
  description = "role_name for fluentd and kafka-1"
  type = string
}
variable "kafka-1_ami_id" {
  description = "id for kafka-cluster"
  type = string
}
variable "kafka-2_ami_id" {
  description = "id for kafka-cluster"
  type = string
}
variable "kafka-3_ami_id" {
  description = "id for kafka-cluster"
  type = string
}
variable "bastion_ami_id" {
  description = "id for bastion host"
  type = string
}
variable "grafana_ami_id" {
  description = "id for grafana"
  type = string
}