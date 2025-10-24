{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "telegram-bot-env";
  
  buildInputs = with pkgs; [
    python3
    python3Packages.python-telegram-bot
    python3Packages.requests
  ];
}
