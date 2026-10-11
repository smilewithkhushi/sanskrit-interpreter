"""Build an installable VS Code extension without external dependencies."""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
PACKAGE = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / f"{PACKAGE['name']}-{PACKAGE['version']}.vsix"


def main():
    manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id={quoteattr(PACKAGE['name'])} Version={quoteattr(PACKAGE['version'])} Publisher={quoteattr(PACKAGE['publisher'])} />
    <DisplayName>{escape(PACKAGE['displayName'])}</DisplayName>
    <Description xml:space="preserve">{escape(PACKAGE['description'])}</Description>
    <Categories>Programming Languages</Categories>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value={quoteattr(PACKAGE['engines']['vscode'])} />
    </Properties>
  </Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code" /></Installation>
  <Dependencies />
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true" />
    <Asset Type="Microsoft.VisualStudio.Code.Readme" Path="extension/README.md" Addressable="true" />
  </Assets>
</PackageManifest>'''
    content_types = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="vsixmanifest" ContentType="text/xml" />
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="md" ContentType="text/markdown" />
  <Default Extension="js" ContentType="text/javascript" />
  <Default Extension="py" ContentType="text/x-python" />
</Types>'''
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        archive.writestr("extension.vsixmanifest", manifest)
        archive.writestr("[Content_Types].xml", content_types)
        for relative in ("package.json", "README.md", "language-configuration.json", "syntaxes/sanskrit-interpreter.tmLanguage.json", "extension.js", "server.py"):
            archive.write(ROOT / relative, "extension/" + relative)
        for relative in ("__init__.py", "interpreter.py", "converter.py"):
            archive.write(ROOT.parent / "sanskrit_interpreter" / relative, "extension/sanskrit_interpreter/" + relative)
    print(OUTPUT)


if __name__ == "__main__":
    main()
