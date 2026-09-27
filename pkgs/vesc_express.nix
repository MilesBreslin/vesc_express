{
  src,
  # Exact HW_NAME values, or "all" for every board in main/hwconf.
  fwBoards ? [ "VESC Express T" ],
  esp-idf,
  fetchurl,
  lib,
  stdenvNoCC,
}:

assert lib.assertMsg (
  fwBoards == "all"
  || (builtins.isList fwBoards && fwBoards != [ ] && builtins.all builtins.isString fwBoards)
) "fwBoards must be a nonempty list of HW_NAME values or \"all\"";

let
  pins = builtins.fromJSON (builtins.readFile ./components.json);
in
stdenvNoCC.mkDerivation {
  pname = "vesc-express-fw";
  version = src.shortRev or src.dirtyShortRev or "unknown";
  inherit src;

  # CMake derives the project name (and binary filename) from this directory.
  postUnpack = ''
    if [ "$sourceRoot" != vesc_express ]; then
      mv "$sourceRoot" vesc_express
      sourceRoot=vesc_express
    fi
  '';

  nativeBuildInputs = [ esp-idf ];
  dontUseCmakeConfigure = true;
  dontUseNinjaBuild = true;
  dontUseNinjaInstall = true;
  dontUseNinjaCheck = true;
  dontFixup = true;

  GIT_COMMIT_HASH = src.shortRev or src.dirtyShortRev or "unknown";
  GIT_BRANCH_NAME = src.ref or "unknown";
  boardsJSON = builtins.toJSON fwBoards;
  componentPins = ./components.json;
  componentSourcesJSON = builtins.toJSON (lib.mapAttrs (_: fetchurl) pins.sources);
  # Normally exported by ESP-IDF's activate.py. esp_wifi_remote uses this
  # major/minor version to select its Kconfig definitions on P4 boards.
  ESP_IDF_VERSION = lib.versions.majorMinor pins.idfVersion;
  IDF_COMPONENT_CHECK_NEW_VERSION = "0";
  PYTHONDONTWRITEBYTECODE = "1";

  buildPhase = ''
    runHook preBuild
    export IDF_COMPONENT_CACHE_PATH="$TMPDIR/component-cache"
    export XDG_CACHE_HOME="$TMPDIR/cache"
    export XDG_CONFIG_HOME="$TMPDIR/config"
    python ${./build-firmware.py}
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall
    mkdir -p "$out"
    cp -r build_output/. "$out/"
    runHook postInstall
  '';

  passthru = { inherit esp-idf; };
}
