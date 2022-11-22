output "smtp_user_name" {
  description = "IAM user name of the SMTP user"
  value       = aws_iam_user.mail.name
}

output "policy_json" {
  description = "Required IAM policies"
  value       = module.secret.policy_json
}

output "secret_arn" {
  description = "ARN of the secrets manager secret containing credentials"
  value       = module.secret.arn
}

output "secret_name" {
  description = "Name of the secrets manager secret containing credentials"
  value       = module.secret.name
}
