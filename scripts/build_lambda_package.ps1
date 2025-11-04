param (
    [string]$BuildFolder = ".\build",
    [string]$ZipFile = ".\lambda_package.zip"
)

# 1. Limpa builds anteriores
Write-Host "Cleaning previous builds..."
if (Test-Path $BuildFolder) {
    Remove-Item -Recurse -Force $BuildFolder
}
if (Test-Path $ZipFile) {
    Remove-Item -Force $ZipFile
}

# 2. Cria a pasta de build
New-Item -ItemType Directory -Force -Path $BuildFolder

# 3. Install project dependencies in the build folder
# Installs dependencies specifically for the Lambda environment (Linux)
Write-Host "Installing Python dependencies for Lambda (manylinux2014_x86_64)..."
pip install --platform manylinux2014_x86_64 --implementation cp --python-version 3.10 --only-binary=:all: --target $BuildFolder -r .\requirements.txt

# 4. Copia o código-fonte do pacote 'fiiscraper'
Write-Host "Copying 'fiiscraper' package..."
Copy-Item -Path ".\fiiscraper" -Destination "$BuildFolder\fiiscraper" -Recurse

# 5. Copia o handler do Lambda
Write-Host "Copying Lambda handler..."
Copy-Item -Path ".\lambda_ingestion\lambda_handler.py" -Destination $BuildFolder

# 6. Cria o arquivo .zip
Write-Host "Creating the $ZipFile package..."
Compress-Archive -Path "$BuildFolder\*" -DestinationPath $ZipFile -Force

# 7. Limpa a pasta temporária
Write-Host "Cleaning build folder..."
Remove-Item -Recurse -Force $BuildFolder

Write-Host "$ZipFile package created successfully!"