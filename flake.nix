{
  description = "VESC Express firmware";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";
    esp-dev = {
      url = "github:mirrexagon/nixpkgs-esp-dev";
      flake = false;
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      esp-dev,
    }:
    let
      forAllSystems = nixpkgs.lib.genAttrs nixpkgs.lib.systems.flakeExposed;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ self.overlays.default ];
            # ESP-IDF 5.5 uses esptool 4, which depends on python-ecdsa.
            # Firmware builds do not use its vulnerable signing operations.
            config.permittedInsecurePackages = [ "python3.13-ecdsa-0.19.2" ];
          };
        in
        {
          inherit (pkgs) vesc-express-fw;
          default = pkgs.vesc-express-fw;
        }
      );

      overlays.default = final: _prev: {
        vesc-express-fw = final.callPackage ./pkgs/vesc_express.nix {
          src = self;
          esp-idf = final.callPackage ./pkgs/esp-idf.nix { inherit esp-dev; };
        };
      };
    };
}
