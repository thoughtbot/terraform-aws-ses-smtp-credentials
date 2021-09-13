resource "aws_iam_user" "mail" {
  name = var.name
  tags = var.tags
}

resource "aws_iam_user_policy_attachment" "send_mail" {
  policy_arn = aws_iam_policy.send_mail.arn
  user       = aws_iam_user.mail.name
}

resource "aws_iam_policy" "send_mail" {
  name   = "${var.name}-send-mail"
  policy = data.aws_iam_policy_document.send_mail.json
  tags   = var.tags
}

data "aws_iam_policy_document" "send_mail" {
  statement {
    actions   = ["ses:SendRawEmail"]
    resources = [local.ses_identity_arn]
  }
}

module "secret" {
  source = "../generic-secret"

  description     = "SMTP username and password for ${var.name}"
  name            = "${var.name}-credentials"
  resource_tags   = var.tags
  trust_principal = var.trust_principal
  trust_tags      = var.trust_tags

  initial_value = jsonencode({
    AWS_SES_SOURCE_ARN = local.ses_identity_arn
    SMTP_ADDRESS       = "email-smtp.${local.region}.amazonaws.com"
    SMTP_AUTH          = "plain"
    SMTP_DOMAIN        = var.domain
    SMTP_PASSWORD      = ""
    SMTP_PORT          = 587
    SMTP_REGION        = local.region
    SMTP_SECRET        = ""
    SMTP_USERNAME      = ""
  })
}

module "rotation" {
  source = "../secret-rotation-function"

  handler            = "lambda_function.lambda_handler"
  role_arn           = module.secret.rotation_role_arn
  runtime            = "python3.8"
  secret_arn         = module.secret.arn
  security_group_ids = [aws_security_group.function.id]
  source_file        = "${path.module}/rotation/lambda_function.py"
  subnet_ids         = var.subnet_ids
  variables          = { USERNAME = aws_iam_user.mail.name }
}

resource "aws_security_group" "function" {
  description = "Security group for rotation ${var.name} credentials"
  name        = "${var.name}-rotation"
  tags        = var.tags
  vpc_id      = var.vpc_id
}

resource "aws_security_group_rule" "function_egress" {
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all egress"
  from_port         = 0
  protocol          = "-1"
  security_group_id = aws_security_group.function.id
  to_port           = 0
  type              = "egress"
}

resource "aws_iam_role_policy_attachment" "access_keys" {
  policy_arn = aws_iam_policy.access_keys.arn
  role       = module.secret.rotation_role_name
}

resource "aws_iam_policy" "access_keys" {
  description = "Rotate AWS IAM access keys for SMTP"
  name        = "${var.name}-access-keys"
  policy      = data.aws_iam_policy_document.access_keys.json
  tags        = var.tags
}

data "aws_iam_policy_document" "access_keys" {
  statement {
    sid = "RotateAccessKey"
    actions = [
      "iam:CreateAccessKey",
      "iam:DeleteAccessKey",
      "iam:ListAccessKeys"
    ]
    resources = [aws_iam_user.mail.arn]
  }
}

data "aws_region" "this" {}

data "aws_caller_identity" "this" {}

locals {
  account_id       = coalesce(var.identity_account_id, data.aws_caller_identity.this.account_id)
  region           = data.aws_region.this.name
  ses_identity_arn = "arn:aws:ses:${local.region}:${local.account_id}:identity/${var.domain}"
}
