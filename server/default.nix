{ lib
, stdenv
, pkgs
, poetry2nix
, python3
, python3Packages
, projectDir ? ./.
, pyproject ? projectDir + "/pyproject.toml"
, poetrylock ? projectDir + "/poetry.lock"
}:

let
  python = python3;
  env = poetry2nix.mkPoetryEnv {
    inherit python;
    inherit projectDir pyproject poetrylock;
  };
in {
  lib = poetry2nix.mkPoetryApplication {
    inherit python;
    inherit projectDir pyproject poetrylock;
    src = ./.;

    doCheck = false;

    meta = with lib; {
      inherit (python.meta) platforms;

      homepage = "https://github.com/martiert/bedlevel";
      license = licenses.mit;
      description = "A tool for leveling the print bed";

      maintainers = [{
        name = "Martin Ertsås";
        email = "martiert@gmail.com";
      }];
    };
  };

  shell = pkgs.mkShell {
    src = ./.;
    buildInputs = [
      python
      env
    ];
  };
}
