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

{
  boot = {
    loader = { grub.enable = true; };
    kernelPackages = pkgs.linuxPackages_5_10;
  };

  services = { openssh.enable = true; };
  networking.firewall.enable = false;

  systemd.services.firewall-stopper = {
    enable = true;
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" ];
    description = "Mitigate frail firewall disable";
    serviceConfig = {
      Type = "simple";
      ExecStart = "systemctl mask --now firewall.service";
    };
  };

  environment.systemPackages = with pkgs; [
    python3
    bashInteractive_5
    curl
    docker
    docker-compose
    ethtool
    gnupg
    htop
    iproute2
    iperf3
    jq
    killall
    nmap
    openssh
    pciutils
    rsync
    tcpdump
    tcpflow
    traceroute
    tree
    util-linux
    wget
    vim
  ];

  users.users.godon_robot = {
    isNormalUser = true;
    home = "/home/test/";
    extraGroups = [ "wheel" ];
    openssh.authorizedKeys.keys = [
      "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDl7d237EJ1hRzVrAMXkhPILHt39AkEcO3l1ktKQUENgACEeNXSUb3ofDBqA0pIGMD+U0Q0+EqyMcxqjJQ5gvu8/O8zVcO1OKO6b9UaWeqrThsjvDCdEiMyml6CKtPJWCHEyo6jXm75lUFeihp0AmWmsSijZcSShNy+EOEBYdRZ56wYZCkD2awKtZB4ui58KP94RYaqHV55u+oTz0WEuFUln69JvVNTDauqv2Iv4VHpewnms7DzQGa/voWtU9oUCRReQJPWZV56Lw2OXxxjIeUaVQNy7ygpFhkERJyjAXtBLUhBDSqA6LE7daT8f2QW6T/4ZM6IB+g70+Q2i+srjlvc6lxBRVb6YSEtyUIxMHQ07/WGedB9KS6RZTiD96+RPRaLsf05Q4k1XL/KVOFtHjf9vM0sFbYw9Q4ExSjtHesLkKMvqHqfx4g60Ws5jLhSaoUqoLofj6njlEp46paUKQDFhBAJHC1Y4O/bSR9PYemGZHPGsBYJRA7Mj7GSF01FxjU= godon-robot@osuosl"
    ];
  };

  virtualisation = {
    docker.enable = true;
    oci-containers = {
      containers = {
        prometheus-ss-exporter = {
          autoStart = true;
          image = "ghcr.io/cherusk/prometheus_ss_exporter:1.0.0";
          environment = {
            PORT = "8090";
            CONFIG_FILE = "/prometheus-ss-exporter/example/config.yml";
          };
          ports = [ "8090:8090" ];
          extraOptions = [ "--network=host" "--pid=host" "--privileged" ];
        };
      };
    };
  };

  security = {
    sudo.wheelNeedsPassword = false; # for automatic use
    polkit = { enable = true; };
  };

  nixpkgs.config.allowUnfree = true;

  system.nixos.version = "22.05";
}
