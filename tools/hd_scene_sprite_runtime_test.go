package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"os"
	"path/filepath"
	"testing"
)

type hdEventFixture struct {
	Entry struct {
		ResearchID int       `json:"research_id"`
		Registers  [8]uint16 `json:"registers"`
		Segments   [4]uint16 `json:"segments"`
		Stack      []uint16  `json:"stack"`
		Record     []uint16  `json:"record"`
	}
	Flags      uint16 `json:"flags"`
	Steps      uint64 `json:"steps"`
	MemorySHA  string `json:"memory_sha256"`
	MemoryFile string `json:"memory_file"`
}

func hdEventFixtureLoad(t *testing.T, rid int, mode string) (*golem.Machine, *hdSceneRuntime, hdEventFixture) {
	t.Helper()
	root := os.Getenv("TEST_HD_EVENT_FIXTURES")
	if root == "" {
		t.Skip("需要合法原版完整 D46 繪製收據")
	}
	name := fmt.Sprintf("r97-decoder-%d-2cae0.json", rid)
	if rid >= 1060 && rid <= 1065 {
		name = fmt.Sprintf("r98-decoder-%d-2cae0.json", rid)
	}
	metadata, e := os.ReadFile(filepath.Join(root, name))
	if e != nil {
		t.Fatal(e)
	}
	expected, known := hdEventFixtureSHAs[name]
	if !known || hash(metadata) != expected[0] {
		t.Fatal("fixture metadata fingerprint")
	}
	var f hdEventFixture
	if e = json.Unmarshal(metadata, &f); e != nil {
		t.Fatal(e)
	}
	memory, e := os.ReadFile(filepath.Join(root, f.MemoryFile))
	if e != nil || hash(memory) != expected[1] || hash(memory) != f.MemorySHA {
		t.Fatal("fixture memory fingerprint", e)
	}
	m := golem.New()
	copy(m.Mem, memory)
	m.CPU.R = f.Entry.Registers
	m.CPU.Seg = f.Entry.Segments
	m.CPU.IP = 0xa
	// 局部 fixture 沒有 PIT/PIC 狀態，關閉 IRQ；正常重播另驗完整旗標與硬體狀態。
	m.CPU.Flags = f.Flags &^ 0x0200
	m.CPU.Cycles = 0
	m.Steps = f.Steps
	h := &hdRuntime{m: m}
	p := &hdSceneRuntime{h: h, pending: map[int]hdSceneCursorPair{}, publishedPending: map[int]hdSceneCursorPair{}, backing: map[uint32]hdSceneCell{}}
	for _, d := range hdSceneDefinitions {
		p.frames = append(p.frames, &hdSceneFrame{hdSceneDefinition: d})
	}
	first := true
	m.WatchWrite(0, 0xaffff, func(_ *golem.Machine, a uint32, o, v byte) {
		if p.spriteCall != nil && first && a >= hdBuildingCanvas && a < hdBuildingCanvas+64000 {
			first = false
			switch mode {
			case "missing":
				return
			case "duplicate":
				p.memoryWrite(a, o, v)
			case "wrong-writer":
				cs, ip := m.CPU.OpAddr()
				at := int(cs)*16 + int(ip) + 15
				old := m.Mem[at]
				m.Mem[at] ^= 1
				p.memoryWrite(a, o, v)
				m.Mem[at] = old
				return
			case "wrong-DS":
				old := m.CPU.Seg[golem.DS]
				m.CPU.Seg[golem.DS]++
				p.memoryWrite(a, o, v)
				m.CPU.Seg[golem.DS] = old
				return
			case "wrong-ES":
				old := m.CPU.Seg[golem.ES]
				m.CPU.Seg[golem.ES] ^= 1
				p.memoryWrite(a, o, v)
				m.CPU.Seg[golem.ES] = old
				return
			case "wrong-SI":
				old := m.CPU.R[golem.SI]
				m.CPU.R[golem.SI] = 65535
				p.memoryWrite(a, o, v)
				m.CPU.R[golem.SI] = old
				return
			case "wrong-BX":
				old := m.CPU.R[golem.BX]
				m.CPU.R[golem.BX] ^= 1
				p.memoryWrite(a, o, v)
				m.CPU.R[golem.BX] = old
				return
			case "outside-canvas":
				oldES, oldBX := m.CPU.Seg[golem.ES], m.CPU.R[golem.BX]
				outside := hdBuildingCanvas + 64000
				m.CPU.Seg[golem.ES] = uint16(outside >> 4)
				m.CPU.R[golem.BX] = uint16(outside & 15)
				p.recordSpriteWrite(outside, 0)
				m.CPU.Seg[golem.ES], m.CPU.R[golem.BX] = oldES, oldBX
			case "irq-stack":
				stack := uint32(m.CPU.Seg[golem.SS])*16 + uint32(m.CPU.R[golem.SP])
				for j := uint32(1); j <= 6; j++ {
					a := stack - j
					m.Write8(a, m.Mem[a])
				}
			case "outside":
				p.recordSpriteWrite(hdBuildingCanvas, 0)
			}
		}
		p.memoryWrite(a, o, v)
	})
	return m, p, f
}
func hdEventRun(t *testing.T, m *golem.Machine, p *hdSceneRuntime) {
	t.Helper()
	for i := 0; i < 750002; i++ {
		p.beforeSpriteInstruction()
		if p.spriteCall == nil {
			if p.spriteAccepted+p.spriteRejected != 1 {
				t.Fatal("decoder never armed", p.spriteAccepted, p.spriteRejected)
			}
			return
		}
		if e := m.Step(); e != nil {
			t.Fatal("actual original decoder", e)
		}
	}
	t.Fatal("decoder bound")
}
func TestHDEventOriginalDecoder(t *testing.T) {
	for _, rid := range []int{1060, 1061, 1063, 1064, 1070, 1071, 1072, 1489, 1491, 1495, 1549} {
		t.Run(fmt.Sprint(rid), func(t *testing.T) {
			t.Run("actual-original", func(t *testing.T) {
				m, p, _ := hdEventFixtureLoad(t, rid, "")
				hdEventRun(t, m, p)
				if p.spriteAccepted != 1 || p.spriteRejected != 0 {
					t.Fatal("complete source rejected", p.spriteAccepted, p.spriteRejected)
				}
				owned := 0
				for _, c := range p.visible {
					if c.slot != 0 {
						owned++
						if p.frames[c.slot-1].id != rid {
							t.Fatal("wrong source")
						}
					}
				}
				var selected *hdSceneFrame
				for _, f := range p.frames {
					if f.id == rid {
						selected = f
					}
				}
				if selected == nil || owned != selected.sprite.opaque || hash(selected.native) != selected.nativeSHA {
					t.Fatal("opaque source coverage", owned)
				}
			})
			for _, mode := range []string{"missing", "duplicate", "wrong-writer", "wrong-DS", "wrong-ES", "wrong-SI", "wrong-BX", "outside-canvas", "outside"} {
				t.Run(mode, func(t *testing.T) {
					m, p, _ := hdEventFixtureLoad(t, rid, mode)
					hdEventRun(t, m, p)
					if p.spriteAccepted != 0 || p.spriteRejected != 1 {
						t.Fatal("bad transaction accepted")
					}
					for _, c := range p.visible {
						if c.slot != 0 {
							t.Fatal("failed transaction retained source")
						}
					}
				})
			}
			for _, kind := range []string{"entry-code", "high-AX", "wrong-frame", "encoded-byte", "source-bank-wrap", "width", "height", "nominal2", "nominal3", "wrong-surface", "surface-alias", "left", "right", "top", "bottom", "caller"} {
				t.Run(kind, func(t *testing.T) {
					m, p, f := hdEventFixtureLoad(t, rid, "")
					c := m.CPU
					record := int(f.Entry.Stack[4])*16 + int(f.Entry.Stack[3]) + 0x36 + int(c.R[golem.AX])*12
					desc := int(c.Seg[golem.DS])*16 + int(c.R[golem.BX])
					stack := int(c.Seg[golem.SS])*16 + int(c.R[golem.SP])
					word := func(at, n int, v uint16) { binary.LittleEndian.PutUint16(m.Mem[at+n*2:], v) }
					switch kind {
					case "entry-code":
						m.Mem[0xd46*16+0xa] ^= 1
					case "high-AX":
						c.R[golem.AX] |= 0x8000
					case "wrong-frame":
						c.R[golem.AX] = 0x4000
					case "encoded-byte":
						m.Mem[int(f.Entry.Record[1])*16+int(f.Entry.Record[0])] ^= 1
					case "source-bank-wrap":
						word(record, 0, 65530)
					case "width":
						word(record, 4, f.Entry.Record[4]+1)
					case "height":
						word(record, 5, f.Entry.Record[5]+1)
					case "nominal2":
						word(record, 2, f.Entry.Record[2]+1)
					case "nominal3":
						word(record, 3, f.Entry.Record[3]+1)
					case "wrong-surface":
						word(desc, 3, 0x3c50)
					case "surface-alias":
						word(desc, 2, 16)
						word(desc, 3, 0x2cad)
					case "left":
						c.R[golem.DX] = 0xffff
					case "right":
						c.R[golem.DX] = 319
					case "top":
						word(stack, 2, 0xffff)
					case "bottom":
						word(stack, 2, 199)
					case "caller":
						word(stack, 0, 0x1555)
					}
					p.beforeSpriteInstruction()
					if p.spriteCall != nil || p.spriteAccepted != 0 {
						t.Fatal("invalid entry armed")
					}
				})
			}
			t.Run("source-mutated-after-entry", func(t *testing.T) {
				m, p, _ := hdEventFixtureLoad(t, rid, "")
				p.beforeSpriteInstruction()
				if p.spriteCall == nil {
					t.Fatal("entry")
				}
				call := p.spriteCall
				for i := 0; !(m.CPU.Seg[golem.CS] == call.retCS && m.CPU.IP == call.retIP && m.CPU.R[golem.SP] == call.sp+10); i++ {
					if i > 750000 {
						t.Fatal("actual return bound")
					}
					if e := m.Step(); e != nil {
						t.Fatal(e)
					}
				}
				if call.bad {
					t.Fatal("baseline source transaction invalid")
				}
				m.Mem[call.source] ^= 1
				p.beforeSpriteInstruction()
				if p.spriteAccepted != 0 || p.spriteRejected != 1 || p.spriteCall != nil {
					t.Fatal("post-return encoded mutation accepted")
				}

			})
			t.Run("timeout", func(t *testing.T) {
				m, p, _ := hdEventFixtureLoad(t, rid, "")
				p.beforeSpriteInstruction()
				if p.spriteCall == nil {
					t.Fatal("entry")
				}
				m.CPU.IP = 0xc
				m.Steps += 750001
				p.beforeSpriteInstruction()
				if p.spriteCall != nil || p.spriteRejected != 1 {
					t.Fatal("bound")
				}
			})
		})
	}
}
func TestHDEventUnknownWriteRevokes(t *testing.T) {
	m, p, _ := hdEventFixtureLoad(t, 1071, "")
	hdEventRun(t, m, p)
	for at, c := range p.visible {
		if c.slot == 0 {
			continue
		}
		m.CPU.Seg[golem.CS] = 0x100
		m.CPU.IP = 0
		before := append([]byte(nil), m.Mem...)
		p.memoryWrite(hdBuildingCanvas+uint32(at), c.value, c.value)
		if p.visible[at].slot != 0 || !bytes.Equal(before, m.Mem) {
			t.Fatal("same-value unknown write or DOS mutation")
		}
		return
	}
	t.Fatal("missing source")
}

var hdEventFixtureSHAs = map[string][2]string{
	"r98-decoder-1060-2cae0.json": {"2bb68400a25c5b79b535f2a8b204d864e7a73790cb0e4c047012c95c2f559f7a", "e046894abcf882f62df2648ba1cd746f219e556d57e037b09250a53028b5fabf"},
	"r98-decoder-1061-2cae0.json": {"67d7aace50a4970b19da7cc5b7eff735a19a58cc040eb79f27326bbfa55e5224", "c9641faf0d330dda0b2eae4250ac3463dceb06ccc27c2c965be1a740a7d65984"},
	"r98-decoder-1063-2cae0.json": {"99a19e754350f832dd80f236fec06261295613ff98524ea596bf9a6f2d49d4a1", "6a4093978da549632b0cb131f1d04b1be01ca18d53496dafae7fad274befd8aa"},
	"r98-decoder-1064-2cae0.json": {"c7b81d58e766b5796a50390fd5c8bf612fddd650372cd913193754a8fdf00a0b", "81ce20ecaa105a2683195b39e1afd573631e2bd2583da99c6b209847eeaeea1b"},
	"r97-decoder-1070-2cae0.json": {"61026b06aa7a7e35261a2ba4c1b43f7fbe5090fd4a149159418045415bfefa06", "c5445c7bc1bcb9c5a19811f309944a82f400787ba98cd111db1efc9eee0a3110"},
	"r97-decoder-1071-2cae0.json": {"752fbb7fb823d647106dd715b41b783d17231a9b250631c6ff95552040ea8be4", "be6a917ee2bd7b5de2fed8f360abd1b870bb40c90ad9f864ccbc2626b3b25991"},
	"r97-decoder-1072-2cae0.json": {"fba1451c73d7e9babfddf8d0ea0e96be96e284c5ee3dc0dd01faad5640bd4dec", "b2adc800d2253d27726d54b3f49e53c8a0cf598ae579e1df2e6b2d0a719a98d8"},
	"r97-decoder-1489-2cae0.json": {"8cb923179bbbe5109e2b0c9f4668dc0d72e4e962c8f579c7e3d65c730b2ded86", "c9394121e9b8947011ffa69a4486f0996753987d869a661707b90c3cc7553597"},
	"r97-decoder-1491-2cae0.json": {"52a0285b5c75370395fe944bed4fc63110c79f57809dabcad5e62211742d8993", "b25f920b2091aed589fd283c541b7a542a7e4f2aa80d674879d5f13e44b6729b"},
	"r97-decoder-1495-2cae0.json": {"1ad894b7182b7cb126d567b849d5a1d71856845588cc7fb06db71ce5206a63b9", "78ec5724804cf9882f04920aa47a8d099c386bbe65fb02e159225779bcccbaf6"},
	"r97-decoder-1549-2cae0.json": {"a36e453296c80dc19653d48192c5de3d7c86db59e5af96f9750b6971487013b0", "5a329922328cee99fea5a96bcd9f62040830fc92c1bec22ac6f8dea5e724cfd3"},
}

func TestHDEventIRQStackWrites(t *testing.T) {
	for _, rid := range []int{1060, 1061, 1063, 1064, 1070, 1071, 1072, 1489, 1491, 1495, 1549} {
		t.Run(fmt.Sprint(rid), func(t *testing.T) {
			m, p, _ := hdEventFixtureLoad(t, rid, "irq-stack")
			hdEventRun(t, m, p)
			if p.spriteAccepted != 1 || p.spriteRejected != 0 {
				t.Fatal("IRQ stack writes mistaken for D46 source overflow")
			}
		})
	}
}
