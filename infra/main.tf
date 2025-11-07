# 1. AWS Provider and S3 Object Data Source
# Defines the AWS provider and region.
provider "aws" {
  region = "sa-east-1"
  profile = "SystemAdministrator-883609937142"
}

# Reads the metadata of the Lambda deployment package from S3.
data "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.fii_data_lake.bucket
  key    = "lambda_code/lambda_package.zip"

  # Ensures that this data source is read only after the S3 bucket has been created.
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

# 5. IAM Role Policy Attachment
resource "aws_iam_role_policy" "lambda_policy_attach" {
  name   = "fii_scraper_lambda_policy"
  role   = aws_iam_role.lambda_role.name
  policy = data.aws_iam_policy_document.lambda_policy_doc.json
}

# Attaches AWS managed policy that allows Lambda to
# create network interfaces in the VPC.
resource "aws_iam_role_policy_attachment" "vpc_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}


# 6 The Lambda Function itself
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

  # 2. We specify the exact file path (key) within the bucket.
  #    This MUST be the same path used in the 'aws s3 cp' command.
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

  # This makes the Lambda run in your private subnet.
  vpc_config {
    subnet_ids         = [aws_subnet.private.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  # Dependency:
  # Ensures that the NAT Gateway (which provides internet access)
  # is ready BEFORE creating the Lambda.
  depends_on = [
    aws_nat_gateway.nat_gw
  ]

  tags = {
    Projeto = "fii-data-science"
  }
}

# 7. EventBridge Scheduler
# Triggers every day at 8 PM UTC (5 PM in Brazil, adjust if needed).
resource "aws_cloudwatch_event_rule" "daily_schedule" {
  name                = "fii_scraper_daily_trigger"
  schedule_expression = "cron(0 20 * * ? *)" 
  description         = "Triggers the FII scraper daily"
}

# 8. EventBridge Target
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_schedule.name
  target_id = "fii_scraper_lambda"
  arn       = aws_lambda_function.fii_scraper_lambda.arn
}

# 9. Lambda Permission for EventBridge
# Authorizes EventBridge to invoke the Lambda function.
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fii_scraper_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_schedule.arn
}

# 10. Region Variable
# (Good practice for network resources)
variable "aws_region" {
  description = "Região da AWS para os recursos"
  default     = "sa-east-1" # Mude se estiver usando outra região
}

# 11. VPC Network Resource
# The main container for your private network.
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "fii-pipeline-vpc"
  }
}

# 12. Public and Private Subnets
# The PUBLIC Subnet (where the NAT Gateway will be).
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a" # Ex: us-east-1a
  map_public_ip_on_launch = true # Importante para o NAT

  tags = {
    Name = "fii-public-subnet"
  }
}

# The PRIVATE Subnet (where your Lambda will run).
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b" # Ex: us-east-1b

  tags = {
    Name = "fii-private-subnet"
  }
}

# 13. Internet Connectivity
# Internet Gateway (IGW) - Allows the public subnet to access the internet.
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "fii-igw"
  }
}

# Elastic IP (EIP) - The fixed static IP that will be the "face" of your Lambda.
resource "aws_eip" "nat_eip" {
  domain = "vpc"
  tags = {
    Name = "fii-nat-eip"
  }
}

# NAT Gateway - The "translator" that uses the static IP.
# !! THIS IS THE RESOURCE THAT INCURS A COST OF ~$35/month !!
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "fii-nat-gateway"
  }

  depends_on = [aws_internet_gateway.igw]
}

# 14. Routing
# PUBLIC Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  # Route 0.0.0.0/0 (internet) -> points to the Internet Gateway (IGW).
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "fii-public-rt"
  }
}

# PRIVATE Route Table
resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.main.id

  # Route 0.0.0.0/0 (internet) -> points to the NAT GATEWAY.
  # This is the MAGIC: all traffic from the Lambda to the internet
  # will be routed to the NAT Gateway, exiting through the static IP.
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gw.id
  }

  tags = {
    Name = "fii-private-rt"
  }
}

# 15. Route Table Associations
# Associates the public route table with the public subnet.
resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public_rt.id
}

# Associates the private route table with the private subnet.
resource "aws_route_table_association" "private_assoc" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private_rt.id
}

# 16. Lambda Security Group (Firewall)
resource "aws_security_group" "lambda_sg" {
  name        = "fii-lambda-sg"
  description = "Allows all outbound (egress) traffic from the Lambda"
  vpc_id      = aws_vpc.main.id

  # Egress Rule: Allows the Lambda to access the internet
  # (e.g., for web scraping over HTTPS port 443).
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # Todos os protocolos
    cidr_blocks = ["0.0.0.0/0"]
  }

  # No ingress rules are needed
  # as nothing needs to "call" the Lambda via the network.

  tags = {
    Name = "fii-lambda-sg"
  }
}

# --- Outputs ---
# Makes Terraform print the bucket name at the end of the execution
output "s3_bucket_name_output" {
  description = "The name of the S3 bucket created for the Data Lake."
  value       = aws_s3_bucket.fii_data_lake.bucket
}