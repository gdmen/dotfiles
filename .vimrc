execute pathogen#infect()
syntax on
filetype plugin indent on

au BufWrite * :Autoformat

set number
set tabstop=8 softtabstop=0 expandtab shiftwidth=4 smarttab

let g:autoformat_autoindent = 0
let g:autoformat_retab = 0
let g:autoformat_remove_trailing_spaces = 0
