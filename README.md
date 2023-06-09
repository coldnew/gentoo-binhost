aarch64-unknown-linux-gnu
---------------------

Packages for `ARM64 (aarch64)` based cores, should worked on VirtualBox/UTM/VMWARE Fusion.

I use theses package to use Gentoo Linux on Apple Silicon with VM.

## Usage

Binhost can be enabled by adding these lines to the make.conf.

```bash
PORTAGE_BINHOST="https://raw.githubusercontent.com/coldnew/gentoo-binhost/${CHOST}"
FEATURES="${FEATURES} getbinpkg"
```

If you want to make your Gentoo only download binary from binhost, add following

```bash
ACCEPT_KEYWORDS="arm64"
PORTAGE_BINHOST="https://raw.githubusercontent.com/coldnew/gentoo-binhost/${CHOST}"
FEATURES="${FEATURES} getbinpkg"
EMERGE_DEFAULT_OPTS="${EMERGE_DEFAULT_OPTS} --getbinpkgonly --binpkg-respect-use=n --autounmask-write"
```
