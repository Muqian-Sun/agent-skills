# Go 的坑与范式

只在读写改 Go 代码时读。条目分四类：验证方法、工具链与环境、语言与标准库、第三方库。
标「实测」的是本机跑出来的结果（macOS + Go 1.27.1），标「文档」的是 go doc / 源码原文，没标的是推断，用前先验。

## 验证方法

- **`go test -count=N` 不会重复运行 Example**。实测：同一个包里 `-count=3`，Example 跑 1 次，普通 `Test` 跑 3 次。所以"输出是否稳定"不能靠 `-count` 验，必须**多次独立启动 `go test`**（并发、网络、时间相关的主题尤其要）。
- **Example 的 `// Output:` 表达不了两种东西**（实测都判失败）：
  - **连续空行**：注释正文里连续空行会被合并成一个（`go/ast.CommentGroup.Text` 的行为）。
  - **行尾空格**：会被去掉。
  被测代码如果会输出这两种格式，要么改输出，要么清洗后再打印。
- **证明"Example 真的在被比对"用注入法**：给每个 Example 的 `// Output:` 块末尾追加一行错误期望，跑测试，确认**失败的集合 == 注入的集合**。只看"测试全绿"不能说明断言有效——漏写 `// Output:` 的 Example 根本不会被执行。
- **统计注入结果用 `go test -json` 按事件计数，不要 grep 文本**。实测踩过：Example 自身会打印嵌套 `go test` 的输出（里面有 `FAIL`、`ok`、`[build failed]` 这些行），grep 文本会把 4 个包误判成"失败 0"。`-json` 里每个 Example 有独立的 `Action: pass/fail` 事件，不受打印内容影响。
- **语义变异**（把被测逻辑改坏，确认对应 Example 变红）三条纪律：
  - **先 diff 确认注入生效**。踩过两次：正则先命中了注释里的同一串文字，代码没被改到，测试照样绿，误判成"测试抓不住"。变异要锚定代码行。
  - **变异导致编译失败的不算数**，换一种改法重做。
  - **有些规范天生变异不出来**（本地磁盘 `Close` 不会失败、Go 1.23 起不 `Stop` 的 Timer 也会被回收），如实写注释，不要硬凑一个测不出问题的演示。
- **不确定的现象不要放进 Example 断言**：数据竞争、deadlock、`select` 多路就绪时的随机选择、goroutine 调度顺序、基准测试的数字。只写注释，另写独立小程序实测，注释里贴实测原文。
- **并发主题必须 `-race`**，且多次独立运行。要演示"用了锁就没有竞争"，正确的证据是"去掉锁后 `-race` 报 DATA RACE"，不是"输出对了"。

## 工具链与环境

- **gofmt 会改文档注释的正文**：
  - 两个单引号 `''` 被改成弯引号 `”`（实测 diff）。**贴报错原文要放进缩进代码块**，代码块里的内容 gofmt 不动。
  - 紧跟在列表后面的缩进块会被当成列表项的续行重排，ASCII 图会被打乱。**列表和图之间加一行普通文字**隔开。
- **只改注释时，用去掉注释的 token 流比对确认代码没动**：`go/scanner` 以 mode 0 扫描（默认跳过注释），逐个比 `(token, 字面量)`。先改一个数字做负向验证，确认它能报出不同。
- **`GOCACHE` 默认在 `$HOME/Library/Caches/go-build`**（实测）。改了 `HOME` 跑测试会因为建不了缓存目录而直接失败，**和被测代码无关**。排查"换某个环境变量就失败"之前，先把 `GOCACHE`、`GOMODCACHE`、`GOPATH` 固定住再下结论——踩过一次，误判成"代码依赖 HOME"。
- **离线运行 go 命令**（造假模块代理、不碰真实缓存）需要这套环境变量：
  ```
  GOPROXY=file://<tmp>/proxy  GOSUMDB=off  GOMODCACHE=<tmp>/modcache
  GOPATH=<tmp>/gopath         GOFLAGS=-modcacherw
  GOTOOLCHAIN=local           GOWORK=off  GOENV=off
  GOPRIVATE=  GONOPROXY=  GONOSUMDB=
  ```
  - **`-modcacherw` 不能省**：模块缓存默认只读，临时目录删不掉。
  - 文件代理的目录结构：`<模块路径>/@v/` 下放 `list`、`<版本>.info`、`<版本>.mod`、`<版本>.zip`；zip 内路径必须以 `<模块路径>@<版本>/` 开头。
  - `go.sum` 的哈希只取决于文件内容，删掉缓存重来完全一致，可以写进 Example。
- **查 API 从哪个 Go 版本开始：`$(go env GOROOT)/api/go1.*.txt`**。格式是 `method (*Request) PathValue`、`type Request struct, Pattern`、`pkg encoding/json/v2`。**格式写错会查不到**，误以为"这个 API 不存在"——踩过一次。
- **`go vet` 能查出来的**（都实测过）：`WaitGroup.Add` 写在 goroutine 内部、`errors.As` 的目标不是指针、`json.Unmarshal` 传了非指针、时间 layout 写成 `2006-02-01`、结构体标签格式错、`copylocks`、`lostcancel`。写演示前先跑一遍 vet，有些"坑"根本进不了代码。
- **`testdata` 目录不参与编译**，`./...` 也不匹配它。里面可以放故意写错的代码。

## 语言与标准库

- **goroutine 的起始栈不是固定 2KB**。Go 1.19 起运行时按程序里 goroutine 的平均栈用量决定起始大小（runtime 源码 `adaptivestackstart = 1`、`gcComputeStartingStackSize`），2KB 只是下限（`stackMin = 2048`）。
- **`WaitGroup` 的 `Add` 必须发生在 `Wait` 之前**。等待方先跑到 `Wait` 时计数器还是 0，`Wait` 直接返回，什么都没等到。
- **`recover` 只接当前 goroutine 的 panic**。别的 goroutine 里没被接住的 panic 让整个进程退出（退出码 2），main 里的 `recover` 救不了。
- **`-race` 发现竞争时退出码 66**（实测），可用 `GORACE="exitcode=N"` 改。
- **`time.Parse` 解析不带时区的字符串得到 UTC**，按北京时间理解就差 8 小时。要用 `ParseInLocation` 并写明时区。
- **`t.Truncate(24*time.Hour)` 按 UTC 截断**，对 UTC+8 来说截到的是当天早上 8 点。按业务时区取当天零点要自己算。
- **比较时刻用 `Equal` 不用 `==`**：`==` 比较的是结构体（含 Location 指针和单调时钟），两次 `LoadLocation` 得到的是不同指针，同一时刻也判不相等。做 map key 前先 `.UTC()`。
- **Go 1.23 起未 `Stop` 的 `Timer`/`Ticker` 能被 GC 回收**。`go doc time.After` 原文："There is no reason to prefer NewTimer when After will do."（老资料里"循环里的 time.After 会泄漏"的说法已经过时。）
- **`fmt.Errorf("...: %w", err)` 里 err 为 nil 时，返回的不是 nil**，而是文字含 `%!w(<nil>)` 的错误。**先判 `err != nil` 再包装**。
- **`encoding/json` v1 与 v2 的关键差异**（Go 1.27 起 `encoding/json/v2` 默认可用，编译器的 `jsonv2` 实验开关默认打开）：字段名匹配 v1 不区分大小写、v2 区分；nil 切片和 nil map v1 编成 `null`、v2 编成 `[]` 和 `{}`；重复 key 和非法 UTF-8 v1 放过、v2 报错。老项目（Go 1.25 及以下）和 gin 用的都是 v1。
- **json 解码到 `any`，数字一律是 `float64`**，大整数丢精度（`9007199254740993` 变成 `…992`）。ID、金额用 `json.Number`（`Decoder.UseNumber`）、`int64` 字段或 `,string`。
- **`net/http`**：
  - **body 读到结尾、不 `Close` 也能复用连接**；只 `Close` 不读会多建连接（实测 200 轮里 4 轮）。`Close` 时标准库会替你读掉剩余内容，上限 256KB、50ms。
  - **非 2xx 不返回 error**，要自己检查 `StatusCode`。
  - **`http.DefaultClient` 没有超时**，生产代码要自己设 `Client.Timeout`。
- **`io.Reader` 可能同时返回 `n > 0` 和 `io.EOF`**（`compress/gzip` 就是这样）。**先处理这 n 个字节，再看 err**；拼接只能用 `buf[:n]`，用整个 `buf` 会把上一轮的残留拼进去。
- **`bufio.Scanner` 单行上限 65536 字节**（`bufio.MaxScanTokenSize`），超了报 `token too long`，要 `sc.Buffer` 调大；读完要检查 `sc.Err()`。
- **`bufio.Writer` 忘了 `Flush` 数据还在缓冲区里**，而且 `Flush` 的错误要检查。

## 第三方库

- **viper**：
  - **`Unmarshal` 看的是 `mapstructure` 标签，不是 `yaml` 标签**。只写 yaml 标签时，多数字段会悄悄变成零值且不报错。
  - **key 不区分大小写**；`Get` 系列取不到、转不了都不报错（返回零值）。
  - 只在环境变量里出现的 key，`AllKeys` 里没有，`Unmarshal` 看不到，要先 `BindEnv` 或 `SetDefault`。
  - 严格模式用 `UnmarshalExact`；yaml.v3 那边对应 `Decoder.KnownFields(true)`。
- **gin**：
  - **`[GIN-debug]` 不会混进 Example 的输出**：gin 在自己 init 时存下了原来的 `os.Stdout`，而 Example 截取输出时换的是 `os.Stdout` 这个变量。设 release 模式是为了 `go run` / `go test -v` 的输出干净。
  - **`BindJSON` 失败会自己写 400 并 Abort**，之后再写响应会得到"headers already written"。要自己控制响应就用 `ShouldBindJSON`。
  - **`Abort()` 不会让当前函数返回**，后面的代码照样执行，必须自己 `return`。
  - **`*gin.Context` 在 handler 返回后会被复用**，开 goroutine 前必须 `c.Copy()`（不复制实测 200 个 goroutine 里 199 个读到了别的请求的数据）。
  - 版本差异（看老项目会遇到）：`c.Set` 的 key 在 v1.10.0 及以前是 `string`、v1.11.0 起是 `any`；v1.7.7 的 `c.Done()` 写死返回 nil。
- **yaml.v3**：不能用 Tab 缩进（报 `found a tab character that violates indentation`）；不加引号的值会被猜类型（`0123` 是 83，`2024-01-02` 是 `time.Time`）；`time.Duration` 字段要写 `"30s"`，写 `30` 报错。
- **testify**：`Equal(t, expected, actual)` 参数顺序写反，失败信息里的 expected/actual 也是反的；`Equal` 对 `int(1)` 和 `int64(1)` 判不相等（要用 `EqualValues`）；装着 nil 指针的 error 用 `assert.Nil` 会通过、`NoError` 才会失败；mock 没设 `On` 就被调用会 panic。
