data "aws_caller_identity" "current" {}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
}



module "lambda" {
  source = "./modules/lambda"
  function_name = "getvpcs"
  role_arn      = "arn:aws:iam::691200274267:role/service-role/getvpcs-role-md6th4lf"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  source_dir    = "${path.root}/modules/lambda/lambda-src/getvpcs"

}

