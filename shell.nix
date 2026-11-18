{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  packages = [
    pkgs.python3
    pkgs.kjv # used by Fish mode
    pkgs.ncurses
  ];
}
