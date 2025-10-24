{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.requests
    python311Packages.beautifulsoup4
    python311Packages.lxml
    python311Packages.websocket-client
    firefox
    git
    curl
  ];
}
