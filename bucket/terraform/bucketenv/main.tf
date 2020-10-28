resource "aws_s3_bucket" "staticstorage" {
  // prod: cicdexample-staticstorage
  // test: d32ac806-3ba8-42cd-81f1-d3a54a638f21-cicdexample-staticstorage
  // where d32a... is your conducto user ID
  bucket = "${var.env == "" ? "" : format("%s-", var.env)}${var.project}-staticstorage}"
  acl = "public-read"
  website {
    index_document = "index.html"
    error_document = "404.html"
  }
}
