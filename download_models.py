from argostranslate import package

package.update_package_index()

available = package.get_available_packages()

print("Available language pairs:")
for pkg in available:
    print(pkg.from_code, "→", pkg.to_code)

print("\nInstalling required language models...\n")

targets = [
    ("en", "ta"),
    ("ta", "en"),
    ("en", "hi"),
    ("hi", "en"),
]

installed = False

for pkg in available:
    if (pkg.from_code, pkg.to_code) in targets:
        print(f"Installing {pkg.from_code} → {pkg.to_code}")
        package.install_from_path(pkg.download())
        installed = True

if not installed:
    print("❌ Tamil/Hindi models not found in package index")
else:
    print("\n✅ Models installed successfully")
