{
  description = "A tool for leveling the print bed";

  inputs = {
    nixpkgs.url = "github:NixOs/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix.url = "github:nix-community/poetry2nix";
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    let
      mergeEnvs = pkgs: envs:
        pkgs.mkShell (builtins.foldl' (a: v: {
          buildInputs = a.buildInputs ++ v.buildInputs;
          nativeBuildInputs = a.nativeBuildInputs ++ v.nativeBuildInputs;
          propagatedBuildInputs = a.propagatedBuildInputs
            ++ v.propagatedBuildInputs;
          propagatedNativeBuildInputs = a.propagatedNativeBuildInputs
            ++ v.propagatedNativeBuildInputs;
          shellHook = a.shellHook + "\n" + v.shellHook;
        }) (pkgs.mkShell { }) envs);
    in {
      overlay = final: prev: {
        frontend = final.callPackage ./frontend/default.nix {};
        server = final.callPackage ./server/default.nix {
          poetry2nix = prev.poetry2nix;
        };
      };
    } //
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlay ];
        };
      in rec {
        packages = {
          server = pkgs.server.lib;
          frontend = pkgs.frontend.static;
          default = packages.server;
        };

        devShells = {
          server = pkgs.server.shell;
          frontend = pkgs.frontend.shell;
          default = mergeEnvs pkgs (with devShells; [ frontend server ]);
        };
      });
}
