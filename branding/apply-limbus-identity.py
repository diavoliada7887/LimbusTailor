from pathlib import Path

ROOT = Path.cwd()
CONFIG = ROOT / "config.h.in"
APP_CMAKE = ROOT / "src/app/CMakeLists.txt"
WIN_RC = ROOT / "src/app/resources/win32/resources.rc"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


# Give the fork its own Qt / QSettings identity instead of inheriting
# Scan Tailor Universal's application namespace.
config = CONFIG.read_text(encoding="utf-8")
config = replace_once(
    config,
    '#define APPLICATION_NAME "Scan Tailor Universal"\n'
    '#define ORGANIZATION_NAME APPLICATION_NAME\n'
    '#define ORGANIZATION_DOMAIN "github.com/trufanov-nok/scantailor-universal"',
    '#define APPLICATION_NAME "LimbusTailor"\n'
    '#define ORGANIZATION_NAME "Arkhivum"\n'
    '#define ORGANIZATION_DOMAIN "arkhivum.local"',
    "application identity",
)
CONFIG.write_text(config, encoding="utf-8")


# Keep the historical CMake target name internally so all upstream build logic,
# translations and dependencies continue to work, but emit LimbusTailor.exe.
cmake = APP_CMAKE.read_text(encoding="utf-8")
cmake = replace_once(
    cmake,
    "ENDIF()\n\nTARGET_LINK_LIBRARIES(\n        scantailor-universal",
    "ENDIF()\n\nSET_TARGET_PROPERTIES(scantailor-universal PROPERTIES OUTPUT_NAME \"LimbusTailor\")\n\nTARGET_LINK_LIBRARIES(\n        scantailor-universal",
    "Windows executable output name",
)
APP_CMAKE.write_text(cmake, encoding="utf-8")


# Give the Windows PE file a clean, explicit LimbusTailor product identity.
# Upstream only embeds an icon in this resource file.
WIN_RC.write_text(
    r'''#include <windows.h>

IDI_ICON1 ICON DISCARDABLE "icon.ico"

VS_VERSION_INFO VERSIONINFO
 FILEVERSION 0,2,13,0
 PRODUCTVERSION 0,2,13,0
 FILEFLAGSMASK 0x3fL
 FILEFLAGS 0x0L
 FILEOS 0x40004L
 FILETYPE 0x1L
 FILESUBTYPE 0x0L
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "040904b0"
        BEGIN
            VALUE "CompanyName", "Arkhivum\0"
            VALUE "FileDescription", "LimbusTailor archive image post-processing\0"
            VALUE "FileVersion", "0.2.13.0\0"
            VALUE "InternalName", "LimbusTailor\0"
            VALUE "OriginalFilename", "LimbusTailor.exe\0"
            VALUE "ProductName", "LimbusTailor\0"
            VALUE "ProductVersion", "0.2.13.0\0"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x0409, 1200
    END
END
''',
    encoding="utf-8",
)

print("Applied native LimbusTailor application, executable and Windows PE identity")
