{ pkgs, version, arch ? "amd64" }:

let
  nodejs = pkgs.nodejs_20;

  src = pkgs.lib.cleanSourceWith {
    src = ./.;
    filter = path: type:
      let
        baseName = baseNameOf path;
        parentDir = baseNameOf (dirOf path);
      in
        baseName == "package.json" ||
        baseName == "package-lock.json" ||
        baseName == "src" ||
        parentDir == "src";
  };

  app = pkgs.buildNpmPackage {
    pname = "evm-score-oracle-node";
    inherit version src nodejs;

    npmDepsHash = "sha256-fZJumOW+z11l0hPOJVw5+KBVt/tG5SuUEqCoLhJJI+o=";

    dontNpmBuild = true;
    npmInstallFlags = [ "--omit=dev" ];

    installPhase = ''
      runHook preInstall
      mkdir -p $out/app
      cp -r . $out/app
      runHook postInstall
    '';
  };

in rec {
  inherit app nodejs;

  docker = pkgs.dockerTools.buildImage {
    name = "evm-score-oracle";
    tag = "node-reproducible-${arch}";
    copyToRoot = pkgs.buildEnv {
      name = "image-root";
      paths = [ nodejs app pkgs.cacert ];
      pathsToLink = [ "/bin" "/app" ];
    };
    config = {
      WorkingDir = "/app";
      Entrypoint = [ "${nodejs}/bin/node" "/app/src/index.js" "/app/ecdsa.sec" ];
      Env = [ "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt" ];
    };
  };

  default = docker;
}
