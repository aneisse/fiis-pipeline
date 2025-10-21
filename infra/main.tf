# 1. Define o provedor (AWS) e a região
# Informa ao Terraform que estamos construindo na AWS
provider "aws" {
  region = "sa-east-1"
}

# 2. Define o Bucket S3 (a "caixa" para nossos dados)
# Tarefa principal da Semana 4
resource "aws_s3_bucket" "fii_data_lake" {
  bucket = "fii-data-bucket" 
  
  tags = {
    Name        = "FII Data Lake - Camada Raw"
    Projeto     = "fii-data-science"
  }
}

# 3. Define a "Identidade" (IAM Role) que o Lambda usará
resource "aws_iam_role" "lambda_role" {
  name = "fii_scraper_lambda_role"

  # Esta é a parte "confie em mim": diz que o serviço Lambda
  # da AWS tem permissão para "assumir" esta identidade.
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

# 4. Define a Política de Permissões (o que a Role pode fazer)
data "aws_iam_policy_document" "lambda_policy_doc" {
  
  # Permissão 1: Escrever logs (essencial para depurar o Lambda)
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # Permissão 2: Escrever (PutObject) no bucket S3 que criamos
  statement {
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.fii_data_lake.arn}/*"] # Aponta para o bucket acima
  }
}

# 5. Anexa a Política (Permissões) à Role (Identidade)
resource "aws_iam_role_policy" "lambda_policy_attach" {
  name   = "fii_scraper_lambda_policy"
  role   = aws_iam_role.lambda_role.name
  policy = data.aws_iam_policy_document.lambda_policy_doc.json
}

# --- Saídas ---
# Faz o Terraform imprimir o nome do bucket no final
output "s3_bucket_name_output" {
  description = "O nome do bucket S3 criado para o Data Lake."
  value       = aws_s3_bucket.fii_data_lake.bucket
}