terraform {
  backend "s3" {
    bucket       = "sevali.statefiles"
    key          = "vpcmanager/prod/terraform.tfstate"
    region       = "eu-central-1"
    use_lockfile = true
  }
}