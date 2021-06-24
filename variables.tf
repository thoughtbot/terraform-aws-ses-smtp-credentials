variable "domain" {
  type        = string
  description = "The domain from which emails are sent"
}

variable "name" {
  type        = string
  description = "Name for created resources"
}

variable "namespace" {
  type        = list(string)
  description = "Namespace to prefix resource"
  default     = []
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
