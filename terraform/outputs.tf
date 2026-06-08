output "master_public_ip" {
  value = aws_instance.nodes["master"].public_ip
}

output "worker1_public_ip" {
  value = aws_instance.nodes["worker1"].public_ip
}

output "worker2_public_ip" {
  value = aws_instance.nodes["worker2"].public_ip
}

output "master_private_ip" {
  value = aws_instance.nodes["master"].private_ip
}

output "worker1_private_ip" {
  value = aws_instance.nodes["worker1"].private_ip
}

output "worker2_private_ip" {
  value = aws_instance.nodes["worker2"].private_ip
}
