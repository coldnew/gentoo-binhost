x86_64-pc-linux-gnu
-------------------
Packages for `64bit X86` based cores, can worked on VirtualBox.

## CPU_FLAGS_X86

```bash
CPU_FLAGS_X86="aes avx avx2 mmx mmxext pclmul popcnt sse sse2 sse3 sse4_1 sse4_2 ssse3"
```

## Usage

Binhost can be enabled by adding these lines to the make.conf.

```bash
PORTAGE_BINHOST="https://raw.githubusercontent.com/coldnew/gentoo-binhost/${CHOST}"
FEATURES="${FEATURES} getbinpkg"
```

If you want to make your Gentoo only download binary from binhost, add following

```bash
ACCEPT_KEYWORDS="~amd64"
PORTAGE_BINHOST="https://raw.githubusercontent.com/coldnew/gentoo-binhost/${CHOST}"
FEATURES="${FEATURES} getbinpkg"
EMERGE_DEFAULT_OPTS="${EMERGE_DEFAULT_OPTS} --getbinpkgonly --binpkg-respect-use=n --autounmask-write"
```
