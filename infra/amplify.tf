///////////////// DEV APP
resource "aws_amplify_app" "vpcmanager_dev_app" {
  name    = "vpcmanager-dev"

  custom_rule {
                source = "/<*>"
                status = "404-200"
                target = "/index.html"
              }
             
environment_variables = {
    "API_BASE_URL" = "https://irvsre31tj.execute-api.eu-central-1.amazonaws.com"
    "APP_ENV" = "dev"
  }

region = "eu-central-1"
repository = "https://github.com/constantinsever/vpcmanager"
}



/////////////////////PROD APP

resource "aws_amplify_app" "vpcmanager_prod_app" {
  name    = "vpcmanager-prod"

  custom_rule {
                source = "/<*>"
                status = "404-200"
                target = "/index.html"
              }
             
environment_variables = {
    "API_BASE_URL" = "https://73pjc5yqn1.execute-api.eu-central-1.amazonaws.com"
    "APP_ENV" = "prod"
  }

region = "eu-central-1"
repository = "https://github.com/constantinsever/vpcmanager"
}




////////////  LAMBDA FUNCTIONS

# resource "aws_lambda_function" "getvpcs" {
#   function_name = "getvpcs"
#   role          = "arn:aws:iam::691200274267:role/service-role/getvpcs-role-md6th4lf"
#   handler       = "lambda_function.lambda_handler"
#   runtime       = "python3.12"
#   memory_size   = 256

#   environment {
#     variables = {
#       TABLE_NAME = "vpcmanager-prod"
#       env        = "prod"
#     }
#   }
#  timeout         = 10 

#   # Temporary dummy file, only needed so Terraform config validates
#   filename         = "lambda.zip"
#   source_code_hash = filebase64sha256("lambda.zip")
# }


////////////////// test cu modules/lambda/main.tf



