# Configure AWS provider
# Configurar el proveedor de AWS
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS provider configuration
# Configuración del proveedor AWS
provider "aws" {
  region = "us-east-1"
}

# Free tier EC2 instance
# Instancia EC2 de capa gratuita
resource "aws_instance" "bunker_server" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS us-east-1
  instance_type = "t3.micro"              # Always free tier

  tags = {
    Name        = "bunker-sre-server"
    Environment = "development"
    Project     = "bunker-sre"
  }
}

# Output the public IP
# Mostrar la IP pública
output "server_ip" {
  description = "Public IP of the server"
  value       = aws_instance.bunker_server.public_ip
}
