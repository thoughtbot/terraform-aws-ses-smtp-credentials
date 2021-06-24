output "policies" {
  description = "Required IAM policies"
  value       = []
}

output "secret_data" {
  description = "Kubernetes secret data"

  value = {
    AWS_SES_SOURCE_ARN = local.ses_identity_arn
    SMTP_ADDRESS       = "email-smtp.${data.aws_region.this.name}.amazonaws.com"
    SMTP_AUTH          = "plain"
    SMTP_DOMAIN        = var.domain
    SMTP_PASSWORD      = aws_iam_access_key.mail.ses_smtp_password_v4
    SMTP_PORT          = 587
    SMTP_USERNAME      = aws_iam_access_key.mail.id
  }
}
