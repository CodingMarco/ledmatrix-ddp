{
  description = "Hacken mit Licht - WLED DDP";

  # To update all inputs:
  # $ nix flake update --recreate-lock-file
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    flake-compat = {
      url = "github:nix-community/flake-compat";
      flake = false;
    };
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, flake-utils, flake-compat }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in
        {
          devShells.default = pkgs.mkShell {
            buildInputs = with pkgs; [
              git
              nix
              python3
            ] ++
            (with python3Packages; [
              opencv4
              requests
            ]);
          };
        }
      );
}
