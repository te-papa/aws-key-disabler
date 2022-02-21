variable "region" {
  description = "aws region"
  type        = string
  default     = "us-east-1"
}

variable "email_to_admin" {
  description = "email used to send final report to"
  type        = string
  default     = "ch-infosec@vmware.com"
}

variable "email_from" {
  description = "email used by ses to send alerts to all users"
  type        = string
  default     = "bar"
}