terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "skywatch" {
  key_name   = var.key_name
  public_key = file(var.public_key_path)
}

resource "aws_security_group" "skywatch" {
  name        = "skywatch-k3s-sg"
  description = "SkyWatch K3s security group"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  ingress {
    description = "K3s API"
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "HTTP app NodePort"
    from_port   = 30080
    to_port     = 30081
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "K8s NodePort range"
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Intra-cluster traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = "SkyWatch"
  }
}

resource "aws_instance" "nodes" {
  for_each = {
    master  = "skywatch-master"
    worker1 = "skywatch-worker"
    worker2 = "skywatch-worker2"
  }

  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.skywatch.id]
  key_name                    = aws_key_pair.skywatch.key_name
  associate_public_ip_address = true

  tags = {
    Name    = each.value
    Project = "SkyWatch"
    Role    = each.key
  }
}

resource "local_file" "ansible_inventory" {
  filename = "${path.module}/../ansible/inventory.ini"
  content = templatefile("${path.module}/inventory.tmpl", {
    master_public_ip  = aws_instance.nodes["master"].public_ip
    master_private_ip = aws_instance.nodes["master"].private_ip

    worker1_public_ip  = aws_instance.nodes["worker1"].public_ip
    worker1_private_ip = aws_instance.nodes["worker1"].private_ip

    worker2_public_ip  = aws_instance.nodes["worker2"].public_ip
    worker2_private_ip = aws_instance.nodes["worker2"].private_ip

    ssh_private_key_path = var.private_key_path
  })
}
