# #
## Copyright (c) 2019 Matthias Tafelmeier
##
## This file is part of godon
##
## godon is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## godon is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with godon. If not, see <http://www.gnu.org/licenses/>.
##

{ config, pkgs, lib, ... }:

#let
#      flowgrind_image = pkgs.dockerTools.buildImage {
#            name = "flowgrind";
#            tag = "latest";
#      
#            fromImage = "ubuntu";
#            fromImageTag = "20.04";
#      
#            runAsRoot = ''
#               #!${pkgs.runtimeShell}
#               apt-get update && apt-get install -y flowgrind
#            '';
#      
#            config = {
#                  Cmd = [ "sleep infinity"  ];
#            };
#        };
#in

{
  imports = [ ./hardware-configuration.nix ];

  boot = {
    loader = { grub.enable = true; };
    kernelPackages = pkgs.linuxPackages_5_10;
  };

  services = {
    openssh.enable = true;
    github-runner = {
      url = "https://github.com/cherusk/godon";
      tokenFile = "/srv/gh_runner.token";
      extraLabels = [ "nixos" "osuosl" ];
    };
  };

  environment.systemPackages = let pythonModules = pythonPackages: with pythonPackages; [ pyyaml ];
  in with pkgs; [
    (python3.withPackages pythonModules)
    ansible
    bashInteractive_5
    cargo
    clang
    ctags
    curl
    docker
    docker-compose
    ethtool
    git
    git-crypt
    gnupg
    htop
    iperf3
    iproute2
    jq
    killall
    mask
    nmap
    openssh
    parted
    pciutils
    rsync
    tcpdump
    tcpflow
    traceroute
    tree
    unzip
    util-linux
    wget
    vim
  ];

  users.users.godon = {
    isNormalUser = true;
    home = "/home/godon/";
    extraGroups = [ "wheel" "docker" "libvirtd" ];
    openssh.authorizedKeys.keys = [
      "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDLt7w6tl++WJT/Bn1HsOep25KpgL867SuZAnK5ifOgd6wS0PxHGiCD/4A0RSHdHZTXMv37DGlC36rhlWJUdsncI5O1F5Ay2d626fPg+REaGi8R7Hox/qInkDs9/NS2IbZvQaYIdeDK151McagWijRFCxTEMYftpslXWKiN5ckP/KjFdUkS7fKcGwqk+UFy7ehMF42i8MUOdkZMJwy8Yc2y4FTdzlrh8VELkMxCePcU9LrvwY5sSh9j65Q5IcIBlma36JMJZQLuEWi7oEGAASehUNeMXs9WFkbyCCWdR1PjHNfbrgZUpgw71SkiQrM8+9/jcfyl5kfkn+GUECQcWBDQnbi809re1ZVmOSUrDBAoEAevFO8qHLgz0d9H0Zs/EOghyN+a4eBLB3et46F733GYGGO4AMMvRSibeyHCLINCLeV19FkHXSxD5iXTRt6WXo3vhKC/tw0XN0yNSOc1nHC+azAJxG6zOxzUzXjC9c1wxaWmGReeanlefQTHVRcMtBfm1NAOwaD0DubSTEBeRRMHfW2ZRs3nV0l73HJWh9J8+5MTpCOK7BGzC0LILMsSqpltUTLI3YmFO5Ly9RokUbcFmnn4Yu4IreTITMmn73CuLNkjZIKwucWmJkWNmWc1hrLRO12Yad/aQS+rczKcQFoNXl+bBmIAOWYJ1C6mSKG/Hw== ci_runner@gh"
    ];
  };

  virtualisation = {
    docker.enable = true;
    #  oci-containers.containers = {
    #    flowgrind = {
    #      image = "flowgrind";
    #      imageFile = flowgrind_image;
    #    };
    #  };
    vswitch.enable = true;
    libvirtd = {
      enable = true;
      onShutdown = "shutdown";
    };
  };

  nixpkgs.config.allowUnfree = true;

  system.nixos.version = "21.11";
}
