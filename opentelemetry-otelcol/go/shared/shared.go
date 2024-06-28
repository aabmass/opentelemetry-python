package main

/*
struct CollectorInstance {
	// c string containing the error or otherwise an empty string if successful
	char err[128];
	unsigned int handle;
};
*/
import "C"
import (
	"fmt"
	"math/rand"
)

//export NewCollector
func NewCollector(yaml *C.char) collectorInstance {
	yamlUri := "yaml:" + C.GoString(yaml)
	return newCollectorInstance(main2(yamlUri))
}

//export ShutdownCollector
func ShutdownCollector(c collectorInstance) collectorInstance {
	fmt.Printf("Stopping collector handle ID: %v\n", c.handle)
	return c
}

type collectorInstance C.struct_CollectorInstance

func newCollectorInstance(err error) collectorInstance {
	ret := collectorInstance{
		handle: C.uint(rand.Uint32()),
	}
	ret.setError(err)
	return ret
}

func (c *collectorInstance) setError(err error) {
	if err != nil {
		writeToCharBuf(c.err[:], err.Error())
	}
}

func writeToCharBuf(buf []C.char, gostring string) {
	var (
		i int
		b byte
	)
	for i, b = range []byte(gostring) {
		if i == len(buf)-1 {
			break
		}
		buf[i] = C.char(b)
	}
	// null terminate
	buf[i+1] = 0
}

func main2(string) error {
	return nil
}

func main() {}
