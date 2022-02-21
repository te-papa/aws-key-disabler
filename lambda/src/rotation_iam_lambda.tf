provider "aws" {
  region = var.region
}

data "archive_file" "lambda_zip_file" {
  type        = "zip"
  output_path = "./lambda_function.zip"
  source {
    content  = file("RotateAccessKey.py")
    filename = "RotateAccessKey.py"
  }
}

resource "aws_lambda_function" "iam_access_key_lambda" {
  description      = "Iam Access Key Rotation Lambda"
  filename         = data.archive_file.lambda_zip_file.output_path
  function_name    = "RoatateAccessKey"
  handler          = "RotateAccessKey.lambda_handler"
  runtime          = "python3.9"
  timeout          = "900"
  role             = aws_iam_role.iam_for_lambda.arn
  source_code_hash = data.archive_file.lambda_zip_file.output_base64sha256
  environment {
    variables = {
      EMAIL_TO_ADMIN = var.email_to_admin
      EMAIL_FROM     = var.email_from
    }
  }
}

resource "aws_cloudwatch_log_group" "iam_access_key_lambda_log_group" {
  name = "/aws/lambda/${aws_lambda_function.iam_access_key_lambda.function_name}"
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

data "aws_region" "current" {}

resource "aws_iam_role" "iam_for_lambda" {
  name = "secops_iam_access_key_rotation_lambda"
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Action" : "sts:AssumeRole",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Effect" : "Allow"
      }
    ]
    }
  )
}

data "aws_iam_policy_document" "iam_rotation_lambda_policy" {

  statement {
    sid = "IAMAccess"
    actions = [
      "iam:DeleteAccessKey",
      "iam:ListGroupsForUser",
      "iam:UpdateAccessKey",
      "iam:ListUsers",
      "iam:ListAccessKeys",
    ]
    resources = [
      "arn:aws:iam::${local.account_id}:user/*",
    ]
  }
  statement {
    sid = "sesaccess"
    actions = [
      "ses:SendEmail",
    ]
    resources = [
      "arn:aws:ses:${data.aws_region.current.name}:${local.account_id}:identity/*",
    ]
  }
  statement {
    sid = "LambdaBasicExecution"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${local.account_id}:log-group:*",
    ]
  }

}

resource "aws_iam_role_policy" "lambda_exec_role" {
  role   = aws_iam_role.iam_for_lambda.id
  policy = data.aws_iam_policy_document.iam_rotation_lambda_policy.json
}

resource "aws_cloudwatch_event_rule" "hourly_cron_job" {
  name                = "hourly_access_key_rotation_lambda"
  description         = "Secops IAM Access Key Rotation Lambda per hour"
  schedule_expression = "rate(60 minutes)"
  is_enabled          = true
}

resource "aws_cloudwatch_event_target" "hourly_cron_job_target" {
  arn  = aws_lambda_function.iam_access_key_lambda.arn
  rule = aws_cloudwatch_event_rule.hourly_cron_job.id
  input_transformer {
    input_template = <<JSON
    {"check_for_outdated_keys":true}
    JSON
  }
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda_hourly" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.iam_access_key_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_cron_job.arn
}

resource "aws_cloudwatch_event_rule" "weekly_cron_job" {
  name                = "weekly_access_key_rotation_lambda"
  description         = "Secops IAM Access Key Rotation Lambda per week"
  schedule_expression = "cron(0 12 ? * MON *)"
  is_enabled          = true
}

resource "aws_cloudwatch_event_target" "weekly_cron_job_target" {
  arn  = aws_lambda_function.iam_access_key_lambda.arn
  rule = aws_cloudwatch_event_rule.weekly_cron_job.id
  input_transformer {
    input_template = <<JSON
    {"check_for_outdated_keys":false}
    JSON
  }
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda_weekly" {
  statement_id  = "AllowExecutionFromCloudWatch1"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.iam_access_key_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_cron_job.arn
}

output "function_name" {
  value = aws_lambda_function.iam_access_key_lambda.function_name
}

