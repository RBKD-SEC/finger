package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	root := os.Getenv("FINGER_ROOT")
	if root == "" {
		var err error
		root, err = os.Getwd()
		if err != nil {
			fmt.Fprintf(os.Stderr, "getcwd: %v\n", err)
			os.Exit(1)
		}
	}

	catalogPath := filepath.Join(root, "capabilities", "catalog-v1.json")
	schemaPath := filepath.Join(root, "capabilities", "schema", "catalog-v1.schema.json")

	for _, p := range []string{catalogPath, schemaPath} {
		if _, err := os.Stat(p); err != nil {
			fmt.Fprintf(os.Stderr, "missing %s: %v\n", p, err)
			os.Exit(1)
		}
	}

	data, err := os.ReadFile(catalogPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "read catalog: %v\n", err)
		os.Exit(1)
	}

	var catalog map[string]interface{}
	if err := json.Unmarshal(data, &catalog); err != nil {
		fmt.Fprintf(os.Stderr, "parse catalog: %v\n", err)
		os.Exit(1)
	}

	sv, ok := catalog["schema_version"].(float64)
	if !ok || sv != 1 {
		fmt.Fprintf(os.Stderr, "unexpected schema_version: %v\n", catalog["schema_version"])
		os.Exit(1)
	}
	if catalog["repository"] != "finger" {
		fmt.Fprintf(os.Stderr, "unexpected repository: %v\n", catalog["repository"])
		os.Exit(1)
	}

	fmt.Println("OK: consumer smoke passed")
}
