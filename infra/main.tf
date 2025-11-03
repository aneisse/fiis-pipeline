# 1. Define o provedor (AWS) e a região
# Informa ao Terraform que estamos construindo na AWS
provider "aws" {
  region = "sa-east-1"
  profile = "SystemAdministrator-883609937142"
}
# Lê os metadados do nosso .zip no S3
data "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.fii_data_lake.bucket
  key    = "lambda_code/lambda_package.zip"

  # Garante que ele só leia DEPOIS que a função Lambda for criada
  # (ou, neste caso, que ele dependa do bucket)
  depends_on = [aws_s3_bucket.fii_data_lake]
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

# --- Bloco 6: A Função Lambda em si ---
resource "aws_lambda_function" "fii_scraper_lambda" {
  function_name = "fii_scraper_ingestion"
  package_type  = "Zip"
  handler       = "lambda_handler.lambda_handler" # arquivo.função
  runtime       = "python3.10" # Garanta que seu venv usa este ou similar
  role          = aws_iam_role.lambda_role.arn    # <-- USA A ROLE QUE JÁ CRIAMOS

  # Aponta para o .zip que a Fase 2 irá criar
  # 1. Dizemos de qual S3 o Lambda deve ler o código.
  #    Usamos a referência ao bucket que o Terraform já criou.
  s3_bucket = aws_s3_bucket.fii_data_lake.bucket 

  # 2. Dizemos qual o "caminho" (key) exato do arquivo dentro do bucket.
  #    Este DEVE ser o mesmo caminho que você usou no Passo 1 (o comando 'aws s3 cp').
  s3_key    = "lambda_code/lambda_package.zip"

  # source_code_hash força o Terraform a detectar mudanças no .zip
  source_code_hash = data.aws_s3_object.lambda_zip.etag

  timeout = 300 # 5 minutos (o scraping pode demorar)
  memory_size = 512 # Aumenta a memória (Pandas consome memória)

  # --- CRUCIAL: Passa o nome do S3 para o Python ---
  environment {
    variables = {
      BUCKET_S3 = aws_s3_bucket.fii_data_lake.bucket
    }
  }

  tags = {
    Projeto = "fii-data-science"
  }
}

# --- Bloco 7: O Agendador (EventBridge) ---
# Dispara todo dia às 20h UTC (aprox. 17h no Brasil, ajuste o cron se desejar)
resource "aws_cloudwatch_event_rule" "daily_schedule" {
  name                = "fii_scraper_daily_trigger"
  schedule_expression = "cron(0 20 * * ? *)" 
  description         = "Dispara o scraper de FIIs diariamente"
}

# --- Bloco 8: Liga o Agendador ao Lambda ---
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_schedule.name
  target_id = "fii_scraper_lambda"
  arn       = aws_lambda_function.fii_scraper_lambda.arn
}

# --- Bloco 9: Permissão final ---
# Autoriza o EventBridge (Agendador) a invocar o Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fii_scraper_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_schedule.arn
}

# --- Saídas ---
# Faz o Terraform imprimir o nome do bucket no final
output "s3_bucket_name_output" {
  description = "O nome do bucket S3 criado para o Data Lake."
  value       = aws_s3_bucket.fii_data_lake.bucket
}