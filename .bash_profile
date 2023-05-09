# Setting PATH for Python 3.8
# The original version is saved in .bash_profile.pysave
PATH="/Library/Frameworks/Python.framework/Versions/3.8/bin:${PATH}"
export PATH

export GOPATH=$(go env GOPATH)
export PATH=$PATH:${GOPATH//://bin:}/bin
export PATH="/usr/local/mysql/bin:$PATH"

# OpenVPN

alias mysql=/usr/local/mysql/bin/mysql
alias mysqladmin=/usr/local/mysql/bin/mysqladmin

eval "$(/opt/homebrew/bin/brew shellenv)"

source $(brew --prefix nvm)/nvm.sh

source /Users/garymenezes/.docker/init-bash.sh || true # Added by Docker Desktop

# Setting PATH for Python 3.10
# The original version is saved in .bash_profile.pysave
PATH="/Library/Frameworks/Python.framework/Versions/3.10/bin:${PATH}"
export PATH
