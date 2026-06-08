variable "aws_region" {
  description = "AWS region for EC2 resources"
  type        = string
  default     = "eu-west-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "AWS key pair name"
  type        = string
  default     = "skywatch-key"
}

variable "public_key_path" {
  description = "Path to SSH public key"
  type        = string
  default     = "~/.ssh/skywatch-key.pub"
}

variable "private_key_path" {
  description = "Path to SSH private key used by Ansible"
  type        = string
  default     = "~/.ssh/skywatch-key.pem"
}

variable "ssh_cidr" {
  description = "CIDR block allowed to SSH to instances"
  type        = string
  default     = "0.0.0.0/0"
}
