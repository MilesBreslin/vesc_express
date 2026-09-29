{
  callPackage,
  esp-dev,
  lib,
  python3,
}:

callPackage "${esp-dev}/pkgs/esp-idf" {
  rev = "v5.5.5";
  sha256 = "sha256-/xVsusdmXFMLImfKryoB5ulR09AJefzoIUFmTAb3n/s=";
  # The upstream tool loader still lists Python 3.10 as a GDB runtime.
  # Nixpkgs 26.05 removed it; none of the tools selected below use GDB.
  callPackage =
    fn: args:
    callPackage fn (
      lib.intersectAttrs (builtins.functionArgs (if builtins.isFunction fn then fn else import fn)) {
        python310 = python3;
      }
      // args
    );
  toolsToInclude = [
    "riscv32-esp-elf"
    "xtensa-esp-elf"
    "esp32ulp-elf"
    "esp-rom-elfs"
  ];
}
