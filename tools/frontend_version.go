package main

import (
	"encoding/json"
	"os"
	"runtime"
)

// The release build sets this constant-initialized string with Go's -X flag.
var frontendReleaseVersion = "development"

func init() {
	if len(os.Args) == 2 && (os.Args[1] == "--version" || os.Args[1] == "-version") {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]string{
			"program": "Colonization CHT", "version": frontendReleaseVersion,
			"os": runtime.GOOS, "arch": runtime.GOARCH,
		})
		os.Exit(0)
	}
}
