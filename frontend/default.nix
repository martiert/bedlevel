{ pkgs, stdenv, callPackage, nodejs-14_x, nodePackages, writeShellScriptBin }:

let
  nodejs = nodejs-14_x;
  # Import & invoke the generated files from node2nix
  generated = callPackage ./nix { inherit nodejs; };

  # node2nix wrapper to update nix files on npm changes
  node2nix = writeShellScriptBin "node2nix" ''
    ${nodePackages.node2nix}/bin/node2nix \
      --development \
      -l package-lock.json \
      -c ./nix/default.nix \
      -o ./nix/node-packages.nix \
      -e ./nix/node-env.nix
  '';

in {
  # Location of the node_modules system dependencies
  inherit (generated) nodeDependencies;

  # Build recipe for the static assets
  static = stdenv.mkDerivation {
    name = "frontend";
    src = ./.;
    buildInputs = [ nodejs ];
    buildPhase = ''
      ln -s ${generated.nodeDependencies}/lib/node_modules ./node_modules
      export PATH="${generated.nodeDependencies}/bin:$PATH"
      npm run build
    '';
    installPhase = ''
      cp -r out $out/
    '';
  };

  run = pname: stdenv.mkDerivation {
    name = "run-frontend-${pname}";

    src = ./.;

    buildPhase = ''
      echo "#!${pkgs.bash}/bin/bash" > result
      echo "export NODE_PATH=\"${generated.nodeDependencies}/lib/node_modules\"" >> result
      echo "export PATH=\"${generated.shell.nodeDependencies}/bin:$PATH\"" >> result
      echo "cd frontend" >> result
      echo "rm -fr .next" >> result
      echo "${pkgs.nodejs}/bin/npm run ${pname}" >> result
      chmod a+x result
    '';
    installPhase = ''
      mkdir --parent $out/bin
      mv result $out/bin/run-frontend-${pname}
    '';
  };

  # Development shell with node2nix wrapper script
  shell = generated.shell.override {
    buildInputs = [ node2nix ];
  };
}
