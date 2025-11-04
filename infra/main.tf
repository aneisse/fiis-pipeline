# 1. Define the provider (AWS) and the region
# Informs Terraform that we are building on AWS
provider "aws" {
  region = "sa-east-1"
  profile = "SystemAdministrator-883609937142"
}
# Reads the metadata of our .zip file from S3
data "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.fii_data_lake.bucket
  key    = "lambda_code/lambda_package.zip"

  # Ensures that it only reads AFTER the Lambda function is created
  # (or, in this case, that it depends on the bucket)
  depends_on = [aws_s3_bucket.fii_data_lake]
}

# 2. Defines the S3 Bucket (the "box" for our data)
# Main task for Week 4
resource "aws_s3_bucket" "fii_data_lake" {
  bucket = "fii-data-bucket" 
  
  tags = {
    Name        = "FII Data Lake - Raw Layer"
    Projeto     = "fii-data-science"
  }
}

# 3. Defines the "Identity" (IAM Role) that will run the Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "fii_scraper_lambda_role"

  # This is the "trust policy": it states that the AWS Lambda service
  # has permission to "assume" this identity.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Projeto = "fii-data-science"
  }
}

# 4. Defines the Permissions Policy (what the Role can do)
data "aws_iam_policy_document" "lambda_policy_doc" {
  
  # Permission 1: Write logs (essential for debugging the Lambda)
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # Permission 2: Write (PutObject) to the S3 bucket we created
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.fii_data_lake.arn}/*"] # Points to the bucket above
  }
}

# 5. Attaches the Policy (Permissions) to the Role (Identity)
resource "aws_iam_role_policy" "lambda_policy_attach" {
  name   = "fii_scraper_lambda_policy"
  role   = aws_iam_role.lambda_role.name
  policy = data.aws_iam_policy_document.lambda_policy_doc.json
}

# --- Block 6: The Lambda Function itself ---
resource "aws_lambda_function" "fii_scraper_lambda" {
  function_name = "fii_scraper_ingestion"
  package_type  = "Zip"
  handler       = "lambda_handler.lambda_handler" # file.function
  runtime       = "python3.10" # Ensure your venv uses this or a similar version
  role          = aws_iam_role.lambda_role.arn    # <-- USES THE ROLE WE ALREADY CREATED

  # Points to the .zip that Phase 2 will create
  # 1. We tell Lambda from which S3 it should read the code.
  #    We use the reference to the bucket that Terraform has already created.
  s3_bucket = aws_s3_bucket.fii_data_lake.bucket 

  # 2. Dizemos qual o "caminho" (key) exato do arquivo dentro do bucket.
  #    Este DEVE ser o mesmo caminho que você usou no Passo 1 (o comando 'aws s3 cp').
  s3_key    = "lambda_code/lambda_package.zip"

  # source_code_hash forces Terraform to detect changes in the .zip file
  source_code_hash = data.aws_s3_object.lambda_zip.etag # Using etag to track file changes

  timeout = 300 # 5 minutes (scraping can be slow)
  memory_size = 512 # Increases memory (Pandas is memory-intensive)

  # --- CRUCIAL: Pass the S3 bucket name to the Python code ---
  environment {
    variables = {
      BUCKET_S3 = aws_s3_bucket.fii_data_lake.bucket
    }
  }

  tags = {
    Projeto = "fii-data-science"
  }
}

# --- Block 7: The Scheduler (EventBridge) ---
# Triggers every day at 8 PM UTC (approx. 5 PM in Brazil, adjust the cron if desired)
resource "aws_cloudwatch_event_rule" "daily_schedule" {
  name                = "fii_scraper_daily_trigger"
  schedule_expression = "cron(0 20 * * ? *)" 
  description         = "Triggers the FII scraper daily"
}

# --- Block 8: Connects the Scheduler to the Lambda ---
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_schedule.name
  target_id = "fii_scraper_lambda"
  arn       = aws_lambda_function.fii_scraper_lambda.arn
}

# --- Block 9: Final Permission ---
# Authorizes EventBridge (the Scheduler) to invoke the Lambda function
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fii_scraper_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_schedule.arn
}

# --- Outputs ---
# Makes Terraform print the bucket name at the end of the execution
output "s3_bucket_name_output" {
  description = "The name of the S3 bucket created for the Data Lake."
  value       = aws_s3_bucket.fii_data_lake.bucket
}