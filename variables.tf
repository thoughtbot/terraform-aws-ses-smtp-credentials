variable "admin_principals" {
  description = "Principals allowed to peform admin actions (default: current account)"
  type        = list(string)
  default     = null
}

variable "domain" {
  type        = string
  description = "The domain from which emails are sent"
}

variable "name" {
  type        = string
  description = "Name for created resources"
}

variable "tags" {
  description = "Tags which should be applied to created resources"
  default     = {}
  type        = map(string)
}

variable "identity_account_id" {
  type        = string
  description = "ID of account that is authorized to send emails (default: current account)"
  default     = null
}

variable "read_principals" {
  description = "Principals allowed to read the secret (default: current account)"
  type        = list(string)
  default     = null
}

variable "trust_tags" {
  description = "Tags required on principals accessing the secret"
  type        = map(string)
  default     = {}
}

variable "subnet_ids" {
  description = "Subnets in which the rotation function should run"
  type        = list(string)
}

variable "vpc_id" {
  description = "VPC in which the rotation function should run"
  type        = string
}
