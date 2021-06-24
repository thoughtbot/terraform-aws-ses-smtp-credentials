resource "aws_iam_user" "mail" {
  name = join("-", concat(var.namespace, [var.name]))
  tags = var.tags
}

resource "aws_iam_user_policy_attachment" "send_mail" {
  policy_arn = aws_iam_policy.send_mail.arn
  user       = aws_iam_user.mail.name
}

resource "aws_iam_policy" "send_mail" {
  name   = join("-", concat(var.namespace, [var.name, "send-mail"]))
  policy = data.aws_iam_policy_document.send_mail.json
  tags   = var.tags
}

data "aws_iam_policy_document" "send_mail" {
  statement {
    actions   = ["ses:SendRawEmail"]
    resources = [local.ses_identity_arn]
  }
}

resource "aws_iam_access_key" "mail" {
  user = aws_iam_user.mail.name
}

data "aws_region" "this" {}

data "aws_caller_identity" "this" {}

locals {
  region           = data.aws_region.this.name
  account_id       = coalesce(var.identity_account_id, data.aws_caller_identity.this.account_id)
  ses_identity_arn = "arn:aws:ses:${local.region}:${local.account_id}:identity/${var.domain}"
}
