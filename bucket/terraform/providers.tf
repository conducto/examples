provider aws {
  version = "~> 3.0"
  region = var.aws-default-region
  access_key = var.aws-access-key-id
  secret_key = var.aws-secret-access-key
}
