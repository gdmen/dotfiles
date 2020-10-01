execute pathogen#infect()
syntax on
filetype plugin indent on

set number
set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab

let g:neoformat_try_formatprg = 1

augroup NeoformatAutoFormat
    autocmd!
    autocmd FileType javascript,javascript.jsx setlocal formatprg=prettier\
                                                            \--stdin\
                                                            \--print-width\ 80\
                                                            \--single-quote\
                                                            \--trailing-comma\ es5
    autocmd BufWritePre *.js,*.jsx Neoformat
augroup END
