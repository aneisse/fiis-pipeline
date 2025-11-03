param (
    [string]$BuildFolder = ".\build",
    [string]$ZipFile = ".\lambda_package.zip"
)

# 1. Limpa builds anteriores
Write-Host "Limpando builds antigos..."
if (Test-Path $BuildFolder) {
    Remove-Item -Recurse -Force $BuildFolder
}
if (Test-Path $ZipFile) {
    Remove-Item -Force $ZipFile
}

# 2. Cria a pasta de build
New-Item -ItemType Directory -Force -Path $BuildFolder

# 3. Instala as dependências do projeto na pasta de build
# Instala as dependências especificamente para o ambiente Lambda (Linux)
Write-Host "Instalando dependências do Python para o Lambda (manylinux2014_x86_64)..."
pip install --platform manylinux2014_x86_64 --implementation cp --python-version 3.10 --only-binary=:all: --target $BuildFolder -r .\requirements.txt

# 4. Copia o código-fonte do pacote 'fiiscraper'
Write-Host "Copiando pacote 'fiiscraper'..."
Copy-Item -Path ".\fiiscraper" -Destination "$BuildFolder\fiiscraper" -Recurse

# 5. Copia o handler do Lambda
Write-Host "Copiando handler do Lambda..."
Copy-Item -Path ".\lambda_ingestion\lambda_handler.py" -Destination $BuildFolder

# 6. Cria o arquivo .zip
Write-Host "Criando o pacote $ZipFile..."
Compress-Archive -Path "$BuildFolder\*" -DestinationPath $ZipFile -Force

# 7. Limpa a pasta temporária
Write-Host "Limpando pasta de build..."
Remove-Item -Recurse -Force $BuildFolder

Write-Host "Pacote $ZipFile criado com sucesso!"