# Git 基本使用
## 基本概念
### 版本库, 工作区, 暂存区
    + *工作区* 电脑看到的目录
    + *版本库* .git 目录, 包含了暂存区(stage) 与 版本分支
    + *暂存区* git add 命令将文件从工作区转到暂存区 (工作区 --git add--> 暂存区)
    + git commit 命令将暂存区的内容提交到版本分支 (暂存区 --git commit--> 分支)
    + HEAD 指针, 指向当前分支
## 常用命令
### 创建版本库 (命令: git init)
### 日志与状态
     git log    (查看提交历史)
     git log --pretty=oneline --abbrev-commit
     git reflog (查看命令历史)
     git status (查看当前 git 文件状态)

### 管理修改
      git diff HEAD -- filename (*查看修改*)
      git checkout -- filename  (*丢弃修改*, 撤销工作区修改, 回到 git add/commit 前状态)
      git reset HEAD filename   (*丢弃暂存区修改*)
      git rm filename (删除文件)

### 修改与提交
      git add filename
      git commit -m "commit comment"

### 版本回退
      git reset --hard HEAD^    (回退至上一个版本)
      git reset --hard commitid

## 远程仓库
### 上传项目库
      git remote add origin git@github.com:michaelliao/learngit.git
      git push -u origin master   (把当前分支推送到远程 origin, 第一次加-u 参数)
      git remote 查看远程信息 (git remote -v 查看详细信息)

### 克隆项目库
>  git clone

## 分支管理
### 分支管理基本操作
#### 创建分支并切换 git checkout -b dev
     相当于以下两条命令
     - git branch dev
     - git checkout dev
#### 查看分支 
     git branch
#### 切换回主分支 
     git checkout master
#### 分支合并 
     git merge dev  (将 dev 分支内容合并到当前分支)
#### 删除分支 
     git branch -d dev
#### 丢弃没有被合并的分支 
     git branch -D feature-vulcan

### 解决冲突
#### 查看分支合并图 
     git log --graph --pretty=oneline --abbrev-commit
#### no-fastforward 方式合并分支 
     git merge --no-ff -m "merge with no-ff" dev

### 保护工作现场

      git stash 后正常干活, 然后
      git stash list
      git stash apply, 然后 git stash drop   或者直接用 git stash pop

## 标签管理
### 创建标签 
      git tag (查看标签)
      git show tagname (查看标签信息)
      git tag tagname
      git tag tagname commitid (git log --pretty=oneline --abbrev-commit 查看)
      git tag -a tagname -m "version 0.1 released" 3628164 (-s 代替-a 可用私钥签名标签)

### 操作标签

    - git tag -d tagname (删除标签)
    - git push origin tagname   (将某个标签分支推送到远程)
    - git push origin :refs/tags/tagname  (删除远程标签)
     

------------


# Github 使用 
## 环境设置
### 账号设置
    - $ ssh-keygen -t rsa -C "your_email@youremail.com"
    - $ git config --global user.name "your name"
    - $ git config --global user.email "your_email@youremail.com"
### 上传项目库
    - $ git remote add origin git@github.com:yourName/yourRepo.git
    - $ git push origin master
### 分支管理
    - $ git checkout -b feature_x   (创建 feature_x 分支并切换过去)
    - $ git checkout master         (切换回主分支)
    - $ git branch -d feature_x     (删除临时分支)
    - $ git push origin <branch>    (将分支推送到远程仓库)
### 更新与合并
    - $ git pull  (下载远程修改)
    - $ git merge <branch>  (合并其他分支到你的当前分支)
    以下丢弃本地所有修改
    - $ git fetch origin
    - $ git reset --hard origin/master
### 拉取单个文件
    - $ git fetch
    - $ git checkout origin/master -- path/to/file
