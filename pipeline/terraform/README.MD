# 테라폼 실행 순서
## terraform install 
### OS : aws amazon linux
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
    sudo yum -y install terraform
### 테라폼 설치 확인
    terraform --version
### 테라폼 자동완성
    terraform -install-autocomplete
- shell restart
## terraform 실행
    terraform init
    terraform plan
    terraform apply
## terraform resource 삭제
    terraform destory
