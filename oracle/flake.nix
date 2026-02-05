{
  description = "EVM Score Oracle - Reproducible Docker images for Node.js enclave";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/release-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;

      version = "0.1.0";

      mkTargets = system:
        let
          linuxPkgs = nixpkgs.legacyPackages.${system};
        in
        {
          amd64 = {
            platform = "linux/amd64";
            pkgs = if system == "x86_64-linux"
                   then linuxPkgs
                   else linuxPkgs.pkgsCross.gnu64;
          };
          arm64 = {
            platform = "linux/arm64";
            pkgs = if system == "aarch64-linux"
                   then linuxPkgs
                   else linuxPkgs.pkgsCross.aarch64-multiplatform;
          };
        };

      buildForTarget = system: targets: targetName: target:
        let
          nodeBuild = import ./app/build.nix {
            inherit version;
            pkgs = target.pkgs;
            arch = targetName;
          };
        in
        {
          node = nodeBuild.docker;
        };
    in
    {
      packages = forAllSystems (system:
        let
          targets = mkTargets system;
        in
        {
          node-amd64 = (buildForTarget system targets "amd64" targets.amd64).node;
          node-arm64 = (buildForTarget system targets "arm64" targets.arm64).node;
          default = (buildForTarget system targets "amd64" targets.amd64).node;
        }
      );
    };
}
