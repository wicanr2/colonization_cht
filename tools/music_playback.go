package main

// 規格046：原版PSOUND API在獨立DOS內產生播放音訊。遊戲位址只在本專案。
import (
	"encoding/binary"
	"fmt"
	"io"
	"math/bits"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	golem "github.com/wicanr2/dosgolem"
)

const soundCommandOffset = 0x0b18
const soundTickOffset = 0x0bf9
const psoundSHA = "8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87"

type nativeMusic struct {
	m                                       *golem.Machine
	d                                       *golem.DOS
	seg                                     uint16
	baseSamples, issued, nextTick, tickStep uint64
}

// 同規格037的有理數時鐘。僅第二台聲音機使用，主DOS時鐘不變。
func musicSamplesAt(s uint64, rate uint32) uint64 {
	hi, lo := bits.Mul64(s, uint64(rate)*264*17000)
	q, _ := bits.Div64(hi, lo, 165000*315000000)
	return q
}
func musicStepAt(j uint64, rate uint32) uint64 {
	hi, lo := bits.Mul64(j, 165000*315000000)
	q, r := bits.Div64(hi, lo, uint64(rate)*264*17000)
	if r != 0 {
		q++
	}
	return q
}

func newNativeMusic(root string) (p *nativeMusic, err error) {
	// 檔案讀取失敗同樣回退，不能讓播放層中止原版遊戲。
	defer func() {
		if v := recover(); v != nil {
			err = fmt.Errorf("音樂初始化：%v", v)
			if p != nil {
				p.d.Close()
			}
			p = nil
		}
	}()
	for name, want := range map[string]string{"OPENING.EXE": versions["OPENING.EXE"], "PSOUND.COL": psoundSHA} {
		if hash(read(filepath.Join(root, name))) != want {
			return nil, fmt.Errorf("音樂版本不符：%s", name)
		}
	}
	m := golem.New()
	must(m.LoadEXE(read(filepath.Join(root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, root)
	d.Install()
	p = &nativeMusic{m: m, d: d}
	success := false
	defer func() {
		if !success {
			d.Close()
		}
	}()
	m.SetSoundBlasterPro(true)
	m.EnableOPLSynth(true)
	var retCS, retIP uint16
	entered, complete := false, false
	for m.Steps < 2000000 {
		for _, o := range d.Overlays {
			if strings.EqualFold(o.Name, "PSOUND.COL") {
				p.seg = o.Seg
			}
		}
		c := m.CPU
		if p.seg != 0 && c.Seg[golem.CS] == p.seg && c.IP == 0x0ac3 && !entered {
			entered = true
			a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.SP])
			retIP, retCS = m.Read16(a), m.Read16(a+2)
		}
		if err = m.Step(); err != nil {
			return nil, err
		}
		if entered && c.Seg[golem.CS] == retCS && c.IP == retIP {
			complete = true
			break
		}
	}
	if !complete || m.PITDiv != 1960 || m.IRQ0Every != 19024 {
		return nil, fmt.Errorf("音樂驅動初始化或節拍不符")
	}
	p.tickStep = uint64(m.IRQ0Every) * 10
	p.nextTick = m.Steps + p.tickStep
	m.IRQ0Every, m.VGAFrameEvery, m.CycleClock = 0, 0, false
	if _, err = p.command(0, 0); err != nil {
		return nil, err
	}
	m.DrainAudio()
	m.OPL = nil
	p.baseSamples = musicSamplesAt(m.Steps, m.AudioRate())
	success = true
	return p, nil
}

func (p *nativeMusic) call(off uint16, args ...uint16) (uint16, error) {
	m, c := p.m, p.m.CPU
	r, seg, ip, flags := c.R, c.Seg, c.IP, c.Flags
	defer func() { c.R, c.Seg, c.IP = r, seg, ip; c.SetFlags(flags) }()
	sp := r[golem.SP] - uint16(4+len(args)*2)
	base := uint32(seg[golem.SS]) * 16
	m.Write16(base+uint32(sp), ip)
	m.Write16(base+uint32(sp+2), seg[golem.CS])
	for i, a := range args {
		m.Write16(base+uint32(sp+4+uint16(i*2)), a)
	}
	c.Seg[golem.CS], c.IP, c.R[golem.SP] = p.seg, off, sp
	c.SetFlags(flags &^ golem.IF)
	for n := 0; n < 200000; n++ {
		m.Steps++
		if err := c.Step(); err != nil {
			return 0, err
		}
		if c.Seg[golem.CS] == seg[golem.CS] && c.IP == ip {
			return c.R[golem.AX], nil
		}
	}
	return 0, fmt.Errorf("音樂API逾時 %04X:%04X", p.seg, off)
}
func (p *nativeMusic) command(cmd, param uint16) (uint16, error) {
	return p.call(soundCommandOffset, cmd, param)
}
func (p *nativeMusic) render(n uint64) ([]int16, error) {
	target := musicStepAt(p.baseSamples+p.issued+n, p.m.AudioRate())
	for p.nextTick <= target {
		if p.m.Steps < p.nextTick {
			p.m.Steps = p.nextTick
		}
		if _, err := p.call(soundTickOffset); err != nil {
			return nil, err
		}
		p.nextTick += p.tickStep
	}
	if p.m.Steps < target {
		p.m.Steps = target
	}
	out := p.m.DrainAudio()
	// API尾端可能超過這批取樣的目標。下批從實際已提供的取樣續接，
	// 避免把這些取樣當成尚未提供，造成換算後偶發缺一幀。
	p.issued += uint64(len(out) / 2)
	p.m.OPL = nil // 私用播放不保留無界追蹤。
	return out, nil
}

type musicCommand struct {
	Command, Parameter uint16
	Step               uint64
}

func validMusicCommand(c uint16) bool {
	return c <= 7 || c >= 0x20 && c <= 0x3f || c >= 0x40 && c <= 0x5d || c >= 0x8020 && c <= 0x8026
}

type musicPlayback struct {
	mu                        sync.Mutex // 播放讀取者及狀態，主DOS命令不使用這把鎖。
	queueMu                   sync.Mutex
	queue                     []musicCommand
	queueError                string
	native                    *nativeMusic
	stream, digital, fallback *audioStream
	err                       string
	commands                  uint64
	recent                    []musicCommand
	queries                   atomic.Uint64
	maxReadSeconds            float64
	closed                    bool
}

func (p *musicPlayback) enqueue(e musicCommand) {
	if e.Command == 8 {
		p.queries.Add(1)
		return
	}
	p.queueMu.Lock()
	defer p.queueMu.Unlock()
	if !validMusicCommand(e.Command) {
		p.queueError = fmt.Sprintf("未知音樂命令 %04X", e.Command)
		return
	}
	if len(p.queue) >= 1024 {
		p.queueError = "音樂命令佇列溢位"
		return
	}
	p.queue = append(p.queue, e)
}

func (p *musicPlayback) observe(m *golem.Machine, d *golem.DOS) func() {
	var overlayN int
	var seg uint16
	return func() {
		if len(d.Overlays) != overlayN {
			for _, o := range d.Overlays[overlayN:] {
				if strings.EqualFold(o.Name, "PSOUND.COL") {
					seg = o.Seg
					p.enqueue(musicCommand{Step: m.Steps})
				}
			}
			overlayN = len(d.Overlays)
		}
		c := m.CPU
		if seg == 0 || c.Seg[golem.CS] != seg || c.IP != soundCommandOffset {
			return
		}
		word := func(off uint16) uint16 {
			a := (uint32(c.Seg[golem.SS])*16 + uint32(uint16(c.R[golem.SP]+off))) & 0xfffff
			return uint16(m.Mem[a]) | uint16(m.Mem[(a+1)&0xfffff])<<8
		}
		p.enqueue(musicCommand{Command: word(4), Parameter: word(6), Step: m.Steps})
	}
}

func (p *musicPlayback) Read(b []byte) (int, error) {
	p.mu.Lock()
	defer p.mu.Unlock()
	start := time.Now()
	defer func() {
		if s := time.Since(start).Seconds(); s > p.maxReadSeconds {
			p.maxReadSeconds = s
		}
	}()
	if p.closed {
		clear(b)
		return 0, io.EOF
	}
	p.queueMu.Lock()
	q, problem := p.queue, p.queueError
	p.queue = nil
	p.queueMu.Unlock()
	if problem != "" {
		p.err = problem
	}
	if p.err == "" {
		for _, e := range q {
			if _, err := p.native.command(e.Command, e.Parameter); err != nil {
				p.err = err.Error()
				break
			}
			p.commands++
			p.recent = append(p.recent, e)
			if len(p.recent) > 64 {
				p.recent = p.recent[len(p.recent)-64:]
			}
		}
	}
	if p.err != "" {
		return p.fallback.Read(b)
	}
	// 任意大小Read分小塊，避免既有0.25秒緩衝上限丟棄本次要求的音樂。
	for off := 0; off < len(b); {
		n := min(4096, len(b)-off)
		p.stream.mu.Lock()
		available := len(p.stream.out)
		p.stream.mu.Unlock()
		if available < n {
			frames := uint64((n - available + 3) / 4)
			sourceN := (frames*uint64(p.native.m.AudioRate())+audioPlayRate-1)/audioPlayRate + 2
			samples, err := p.native.render(sourceN)
			if err != nil {
				p.err = err.Error()
				return p.fallback.Read(b)
			}
			p.stream.push(samples)
		}
		p.stream.Read(b[off : off+n])
		digital := make([]byte, n)
		p.digital.Read(digital)
		for i := 0; i+2 <= n; i += 2 {
			v := int32(int16(binary.LittleEndian.Uint16(b[off+i:]))) + int32(int16(binary.LittleEndian.Uint16(digital[i:])))
			v = max(-32768, min(32767, v))
			binary.LittleEndian.PutUint16(b[off+i:], uint16(int16(v)))
		}
		off += n
	}
	return len(b), nil
}

func (p *musicPlayback) status() map[string]any {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.stream.mu.Lock()
	defer p.stream.mu.Unlock()
	p.digital.mu.Lock()
	defer p.digital.mu.Unlock()
	return map[string]any{"mode": "independent-original-driver", "error": p.err, "commands": p.commands,
		"ignored_queries": p.queries.Load(), "recent_commands": append([]musicCommand(nil), p.recent...),
		"music_read_bytes": p.stream.ReadBytes, "music_underrun_bytes": p.stream.UnderrunBytes,
		"music_dropped_bytes": p.stream.Dropped, "music_source_frames": p.stream.srcBase,
		"digital_underrun_bytes": p.digital.UnderrunBytes, "digital_dropped_bytes": p.digital.Dropped,
		"max_read_seconds": p.maxReadSeconds}
}

func (a *frontendAudio) playbackReader() io.Reader {
	if a.music != nil {
		return a.music
	}
	return a.stream
}
func (a *frontendAudio) close() {
	if a == nil {
		return
	}
	if a.player != nil {
		a.player.Close()
	}
	if a.music != nil {
		a.music.mu.Lock()
		a.music.closed = true
		a.music.native.d.Close()
		a.music.mu.Unlock()
	}
	frontendBeforeInstruction = nil
}
