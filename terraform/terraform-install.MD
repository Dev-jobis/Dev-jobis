# 테라폼 설치 
## OS : aws amazon linux
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
    sudo yum -y install terraform
## 테라폼 설치 확인
    terraform --version
## 테라폼 자동완성
    terraform -install-autocomplete
- shell restart
