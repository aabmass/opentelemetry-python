package main

/*
#include <string.h>
struct CollectorInstance {
	// a 128 byte buffer to write an error message into
	char err[128];
	int handle;
};
*/
import "C"

//export OtelColContribMain
func OtelColContribMain(yaml *C.char, handle *C.struct_CollectorInstance) int {
	yamlUri := "yaml:" + C.GoString(yaml)
	if err := main2(yamlUri); err != nil {
		writeToCharBuf(handle.err[:], "Oh no")
		return 1
	}
	// return nil
	handle.handle = 123
	writeToCharBuf(handle.err[:], "Oh no")
	return 122
}

func writeToCharBuf(buf []C.char, gostring string) {
	for i, b := range append([]byte(gostring), 0) {
		if i >= len(buf) {
			return
		}
		buf[i] = C.char(b)
	}
}

func main2(string) error {
	return nil
}

func main() {}
