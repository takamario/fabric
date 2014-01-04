#!/usr/bin/env python

from fabric.api import run, sudo
from fabric.decorators import with_settings
from fabric.context_managers import shell_env  # , settings
from fabric.operations import put


@with_settings(warn_only=True)
def update_apt_pkgs():
    if sudo('dpkg -s nginx | grep "install ok installed" > /dev/null').failed:
        sudo('apt-get update')
        sudo('apt-get upgrade -y')
        sudo('apt-get dist-upgrade -y')
        sudo('apt-get autoclean')
        sudo('apt-get autoremove -y')


@with_settings(warn_only=True)
def install_apt_pkgs():
    pkgs = [
        'build-essential',
        'colordiff',
        'curl',
        'git',
        'libbz2-dev',
        'libgd-dev',
        'libmysqlclient-dev',
        'libreadline-dev',
        'libreadline6-dev',
        'libsqlite3-dev',
        'libssl-dev',
        'libxml2-dev',
        'ncurses-term',      # xterm-256color
        'openssl',
        'sysstat',           # sar
        'sysv-rc-conf',
        'tk-dev',
        'zip',
        'zlib1g-dev',
    ]
    sudo('apt-get install -y ' + ' '.join(pkgs))


def install_nginx():
    sudo('apt-get install -y nginx')


def install_redis():
    sudo('apt-get install -y redis-server')


def install_mysql():
    # Skip interactive mode
    sudo('echo mysql-server mysql-server/root_password       password test | sudo debconf-set-selections')
    sudo('echo mysql-server mysql-server/root_password_again password test | sudo debconf-set-selections')

    sudo('apt-get install -y mysql-server')


@with_settings(warn_only=True, sudo_user='takamaru')
def install_ruby():
    with shell_env(HOME='/home/takamaru', PATH="/home/takamaru/.rbenv/bin:$PATH"):
        # Install rbenv
        if sudo('test -d ~/.rbenv').failed:
            sudo('git clone https://github.com/sstephenson/rbenv.git ~/.rbenv')
        else:
            print '"rbenv" is already installed'

        if sudo('grep ".rbenv" ~/.bashrc > /dev/null').failed:
            path_str = 'PATH="$HOME\/.rbenv\/bin:$PATH"'
            sudo('echo -e "\n# rbenv" >> ~/.bashrc')
            sudo('echo "export %s" >> ~/.bashrc')
            sudo("sed -i -e 's/%s/" + path_str + "/g' ~/.bashrc")
        else:
            print '"rbenv PATH" is already written'

        if sudo('grep "rbenv init" ~/.bashrc > /dev/null').failed:
            rb_str = '"$(rbenv init -)"'
            sudo('echo "eval %s" >> ~/.bashrc')
            sudo("sed -i -e 's/%s/" + rb_str + "/g' ~/.bashrc")
        else:
            print '"rbenv" init is already written'

        # Install ruby-build
        if sudo('test -d ~/.rbenv/plugins/ruby-build').failed:
            sudo('git clone https://github.com/sstephenson/ruby-build.git ~/.rbenv/plugins/ruby-build')
        else:
            print '"ruby-build" is already installed'

        # Install Ruby
        ruby_ver = sudo("rbenv install -l | awk '{print $1}' | egrep -v 'preview|dev|rc' | egrep --color=never '^2.1.[0-9](.*)$'")    # 2.1.x
        if sudo('rbenv versions | grep --color=never "' + ruby_ver + '" > /dev/null').failed:
            sudo('rbenv install ' + ruby_ver)
        else:
            print '"ruby %s" is already installed' % ruby_ver
        sudo('rbenv global ' + ruby_ver)
        sudo('rbenv rehash')


@with_settings(warn_only=True, sudo_user='takamaru')
def install_gems():
    with shell_env(HOME='/home/takamaru', PATH="/home/takamaru/.rbenv/bin:$PATH"):
        if sudo('test -f ~/.gemrc && grep "gem:" ~/.gemrc > /dev/null').failed:
            sudo('echo "gem: --no-ri --no-rdoc -V" >> ~/.gemrc')
        else:
            print '".gemrc" already exists'

        gems = [
            'bundler',
            'pry',
            'rails',
            'rbenv-rehash',
            'rspec',
            'spring',
        ]

        not_installed = []
        installed = []
        for g in gems:
            if sudo("eval \"$(rbenv init -)\" && gem list | awk '{print $1}' | egrep '^" + g + "$' > /dev/null").failed:
                not_installed.append(g)
            else:
                installed.append(g)
        if len(installed) > 1:
            print '"%s" is already installed' % ','.join(installed)
        if len(not_installed) > 1:
            sudo('eval "$(rbenv init -)" && gem install ' + ' '.join(not_installed))

        sudo('rbenv rehash')


@with_settings(warn_only=True)
def create_user():
    if sudo('grep "takamaru" /etc/sudoers > /dev/null').failed:
        sudo("sed -i -e '/^root/a takamaru ALL=(ALL:ALL) ALL' /etc/sudoers")
    else:
        print '"takamaru" is already in sudoers'

    if run('cat /etc/passwd | grep takamaru > /dev/null').succeeded:
        print '"takamaru" already exists'
        return

    params = {
        '-c': '"Shoei Takamaru"',
        '-d': '/home/takamaru',
        '-s': '/bin/bash',
        '-m': 'takamaru',    # -m and create "takamaru" user
    }
    param_array = []
    for k, v in params.items():
        param_array.append(k + ' ' + v)

    sudo('useradd ' + ' '.join(param_array))


@with_settings(warn_only=True, sudo_user='takamaru')
def put_rc_files():
    vimrc = '.vimrc'
    if run('test -f /home/takamaru/' + vimrc).failed:
        put('~/' + vimrc, '~/' + vimrc)

        with shell_env(HOME='/home/takamaru'):
            sudo('cp ~vagrant/.vimrc ~')
            run('rm -f ~vagrant/.vimrc')
    else:
        print '"%s" already exists' % vimrc
        run('rm -f ~vagrant/.vimrc')

    gitconfig = '.gitconfig'
    if run('test -f /home/takamaru/' + gitconfig).failed:
        put('~/' + gitconfig, '~/' + gitconfig)

        with shell_env(HOME='/home/takamaru'):
            sudo('cp ~vagrant/.gitconfig ~')
            run('rm -f ~vagrant/.gitconfig')
    else:
        print '"%s" already exists' % gitconfig
        run('rm -f ~vagrant/.gitconfig')


@with_settings(warn_only=True, sudo_user='takamaru')
def install_neobundle():
    with shell_env(HOME='/home/takamaru'):
        if sudo('test -d ~/.vim/bundle').failed:
            sudo('mkdir -p ~/.vim/bundle')
        else:
            print '"~/.vim/bundle" already exists'

        if sudo('test -d ~/.vim/bundle/neobundle.vim').failed:
            sudo('git clone git://github.com/Shougo/neobundle.vim ~/.vim/bundle/neobundle.vim')
            sudo('~/.vim/bundle/neobundle.vim/bin/neoinstall')
        else:
            print '"neobundle.vim" is already installed'


@with_settings(warn_only=True, sudo_user='takamaru')
def modify_bashrc():
    with shell_env(HOME='/home/takamaru'):

        if run('grep "GIT_EDITOR=vim" ~/.bashrc > /dev/null').succeeded:
            print '".bashrc" no need to modify'
            return

        sudo('echo -e "\n# aliases" >> ~/.bashrc')
        sudo("echo \"alias ls='ls -F --color'\" >> ~/.bashrc")
        sudo("echo \"alias grep='grep --color'\" >> ~/.bashrc")
        sudo("echo \"alias egrep='egrep --color'\" >> ~/.bashrc")
        sudo("echo \"alias less='less -R'\" >> ~/.bashrc")
        sudo('echo -e "\n# git" >> ~/.bashrc')
        sudo("echo 'export GIT_EDITOR=vim' >> ~/.bashrc")
        sudo("echo 'PS1=%s' >> ~/.bashrc")
        sudo("sed -i -e \"s/PS1=%s/PS1='%s'/\" ~/.bashrc")
        sudo("sed -i -e 's/%s/\[" + r'\\\\' + "u:" + r'\\\\' + "W$(__git_ps1 \"(%s)\")]$ /' ~/.bashrc")


@with_settings(warn_only=True, sudo_user='takamaru')
def put_ssh_pubkey():
    macbook = 'takamario@Shoeis-MacBook-Air.local'

    put('~/.ssh/id_rsa.pub', '~/authorized_keys')

    if sudo('test -d ~takamaru/.ssh').failed:
        sudo('mkdir -m 700 ~takamaru/.ssh')
    else:
        print '"~takamaru/.ssh" already exists'

    if sudo('grep "' + macbook + '" ~takamaru/.ssh/authorized_keys > /dev/null').failed:
        sudo('cat ~vagrant/authorized_keys >> ~takamaru/.ssh/authorized_keys')
    else:
        print '"ssh_pubkey" is already added'


@with_settings(warn_only=True, sudo_user='takamaru')
def create_ssh_keys():
    if sudo('test -f ~takamaru/.ssh/id_rsa').succeeded:
        print '"ssh_seckey already exists"'
    else:
        if sudo('test -d ~takamaru/.ssh').failed:
            sudo('mkdir -m 700 ~takamaru/.ssh')
        else:
            print '"~takamaru/.ssh" already exists'
        sudo('ssh-keygen -t rsa -N "" -f ~takamaru/.ssh/id_rsa')


def install_middlewares():
    update_apt_pkgs()
    install_apt_pkgs()
    install_nginx()
    install_redis()
    install_mysql()
    create_user()
    install_ruby()
    install_gems()
    put_rc_files()
    modify_bashrc()
    install_neobundle()
    put_ssh_pubkey()
    create_ssh_keys()
