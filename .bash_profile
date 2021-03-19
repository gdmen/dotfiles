# Setting PATH for Python 3.8
# The original version is saved in .bash_profile.pysave
PATH="/Library/Frameworks/Python.framework/Versions/3.8/bin:${PATH}"
export PATH

export GOPATH=$(go env GOPATH)
export PATH=$PATH:${GOPATH//://bin:}/bin
export PATH="/usr/local/mysql/bin:$PATH"

alias mysql=/usr/local/mysql/bin/mysql
alias mysqladmin=/usr/local/mysql/bin/mysqladmin
