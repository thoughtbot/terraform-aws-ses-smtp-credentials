# SES SMTP User

Provides SMTP credentials for an existing SES domain identity.

SMTP usernames and passwords for SES require creating an IAM user and access
key. This module will create a Secrets Manager secret and populate it with
rotating SMTP credentials from a dedicated IAM user.

Example:

``` terraform
module "ses_smtp" {
  source = "github.com/thoughtbot/terraform-aws-ses-smtp-credentials?ref=v0.2.0"

  # The domain corresponding to your domain identity
  domain          = "example.com"

  # The name of the secret to create
  name = "example-production-smtp"

  # Fill in details for your VPC
  subnet_ids = data.aws_subnet.private.*.id
  vpc_id     = data.aws_vpc.this.id
}
```

The outputs include `policy_json`, which is an IAM policy allowing access to the
secret. You can add this to an IAM role or policy.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.14.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 5.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 5.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_rotation"></a> [rotation](#module\_rotation) | github.com/thoughtbot/terraform-aws-secrets//secret-rotation-function | v0.8.0 |
| <a name="module_secret"></a> [secret](#module\_secret) | github.com/thoughtbot/terraform-aws-secrets//secret | v0.8.0 |

## Resources

| Name | Type |
|------|------|
| [aws_iam_policy.access_keys](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.send_mail](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role_policy_attachment.access_keys](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_user.mail](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user) | resource |
| [aws_iam_user_policy_attachment.send_mail](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user_policy_attachment) | resource |
| [aws_security_group.function](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group_rule.function_egress](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule) | resource |
| [aws_caller_identity.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.access_keys](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.send_mail](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_region.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_admin_principals"></a> [admin\_principals](#input\_admin\_principals) | Principals allowed to peform admin actions (default: current account) | `list(string)` | `null` | no |
| <a name="input_domain"></a> [domain](#input\_domain) | The domain from which emails are sent | `string` | n/a | yes |
| <a name="input_identity_account_id"></a> [identity\_account\_id](#input\_identity\_account\_id) | ID of account that is authorized to send emails (default: current account) | `string` | `null` | no |
| <a name="input_name"></a> [name](#input\_name) | Name for created resources | `string` | n/a | yes |
| <a name="input_read_principals"></a> [read\_principals](#input\_read\_principals) | Principals allowed to read the secret (default: current account) | `list(string)` | `null` | no |
| <a name="input_subnet_ids"></a> [subnet\_ids](#input\_subnet\_ids) | Subnets in which the rotation function should run | `list(string)` | `[]` | no |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags which should be applied to created resources | `map(string)` | `{}` | no |
| <a name="input_trust_tags"></a> [trust\_tags](#input\_trust\_tags) | Tags required on principals accessing the secret | `map(string)` | `{}` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC in which the rotation function should run | `string` | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_policy_json"></a> [policy\_json](#output\_policy\_json) | Required IAM policies |
| <a name="output_secret_arn"></a> [secret\_arn](#output\_secret\_arn) | ARN of the secrets manager secret containing credentials |
| <a name="output_secret_name"></a> [secret\_name](#output\_secret\_name) | Name of the secrets manager secret containing credentials |
| <a name="output_smtp_user_name"></a> [smtp\_user\_name](#output\_smtp\_user\_name) | IAM user name of the SMTP user |
<!-- END_TF_DOCS -->
