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
          