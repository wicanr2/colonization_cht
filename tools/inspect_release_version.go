// Inspect the actual Go string variable in ELF, PE and Mach-O release binaries.
// Run in the fixed Docker Go toolchain: go run this_file.go binary expected_version.
package main

import (
	"debug/elf"
	"debug/macho"
	"debug/pe"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"os"
)

type region struct {
	address uint64
	data    []byte
}
type result struct {
	Format, Arch, Version string
	Address               uint64
}

func inspect(format, arch string, address uint64, regions []region) result {
	read := func(p, n uint64) []byte {
		for _, s := range regions {
			if p >= s.address && p-s.address <= uint64(len(s.data)) && n <= uint64(len(s.data))-(p-s.address) {
				return s.data[p-s.address : p-s.address+n]
			}
		}
		panic(fmt.Sprintf("unmapped %s string address %#x", format, p))
	}
	h := read(address, 16)
	p, n := binary.LittleEndian.Uint64(h[:8]), binary.LittleEndian.Uint64(h[8:])
	if n == 0 || n > 64 {
		panic("invalid version string length")
	}
	return result{format, arch, string(read(p, n)), address}
}

func mach(f *macho.File) result {
	if f.Symtab == nil {
		panic("missing Mach-O symbol table")
	}
	var address uint64
	for _, s := range f.Symtab.Syms {
		if s.Name == "main.frontendReleaseVersion" || s.Name == "_main.frontendReleaseVersion" {
			address = s.Value
		}
	}
	if address == 0 {
		panic("missing Mach-O version symbol")
	}
	var regions []region
	for _, s := range f.Sections {
		if d, e := s.Data(); e == nil {
			regions = append(regions, region{s.Addr, d})
		}
	}
	return inspect("Mach-O", f.Cpu.String(), address, regions)
}

func main() {
	if len(os.Args) != 3 {
		panic("usage: binary expected_version")
	}
	path, expected := os.Args[1], os.Args[2]
	var results []result
	if f, e := elf.Open(path); e == nil {
		defer f.Close()
		symbols, e := f.Symbols()
		if e != nil {
			panic(e)
		}
		var address uint64
		for _, s := range symbols {
			if s.Name == "main.frontendReleaseVersion" {
				address = s.Value
			}
		}
		if address == 0 {
			panic("missing ELF version symbol")
		}
		var regions []region
		for _, s := range f.Sections {
			if d, e := s.Data(); e == nil {
				regions = append(regions, region{s.Addr, d})
			}
		}
		results = append(results, inspect("ELF", f.Machine.String(), address, regions))
	} else if f, e := pe.Open(path); e == nil {
		defer f.Close()
		h, ok := f.OptionalHeader.(*pe.OptionalHeader64)
		if !ok {
			panic("expected PE32+")
		}
		var address uint64
		for _, s := range f.Symbols {
			if s.Name == "main.frontendReleaseVersion" && s.SectionNumber > 0 {
				address = h.ImageBase + uint64(f.Sections[int(s.SectionNumber)-1].VirtualAddress) + uint64(s.Value)
			}
		}
		if address == 0 {
			panic("missing PE version symbol")
		}
		var regions []region
		for _, s := range f.Sections {
			d, e := s.Data()
			if e != nil {
				panic(e)
			}
			regions = append(regions, region{h.ImageBase + uint64(s.VirtualAddress), d})
		}
		results = append(results, inspect("PE", "amd64", address, regions))
	} else if f, e := macho.OpenFat(path); e == nil {
		defer f.Close()
		if len(f.Arches) != 2 {
			panic("expected two macOS architectures")
		}
		for _, a := range f.Arches {
			results = append(results, mach(a.File))
		}
	} else {
		panic("unsupported release binary")
	}
	for _, r := range results {
		if r.Version != expected {
			panic("embedded version differs: " + r.Version)
		}
	}
	if e := json.NewEncoder(os.Stdout).Encode(results); e != nil {
		panic(e)
	}
}
