module "static-site" {
  source = "./bucketenv"
  project = "examples-bucket"
  env = var.tag
}
