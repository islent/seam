"""English text for the figures.

Kept as data rather than translated at render time in the layout code, so that the drawing
functions stay about geometry and the wording stays in one place. The keys are the exact
Chinese strings emitted by ``build_figures.py``; ``main()`` checks that every CJK string in
the generated figure has an entry here, so a new label cannot silently stay Chinese.
"""

EN = {
    # ---- figure 1
    "只交一次，还是每一步都在": "One handover, or one at every step",
    "现在的工具只把一个结果递给你。中间发生了什么，你看不到，也插不上手。":
        "Today's tools hand you a result. What happened in between is invisible and out of reach.",
    "现在的做法": "How it works today",
    "提交 → 等 → 结果": "submit → wait → result",
    "一次交付": "one handover",
    "提交": "submit",
    "中间看不见：没有进度，没有中间结果，也改不了任何东西":
        "invisible: no progress, no partial results, nothing you can change",
    "结果": "result",
    "跑了两个小时才知道参数填错了。": "two hours later you learn a parameter was wrong.",
    "这个项目要求的做法": "What this asks for",
    "每一步都能看，能改": "visible and writable at every step",
    "一直在场": "always present",
    "开始": "start",
    "第 120 步": "step 120",
    "改成 480": "→ 480",
    "场强": "|Ez|",
    "改分辨率 ✕": "resolution ✕",
    "时间": "time",
    "↑ 能读到": "↑ read",
    "↓ 能改的": "↓ write",
    "操作记录": "record",
    "存在一个 trace.jsonl 里": "one trace.jsonl",
    "第几条": "seq",
    "差别在于你能不能中途问一句、改一下。":
        "The difference is whether you can ask a question mid-run.",
    "上面那 9 条，每一条都能翻回去看：第几步、谁改的、改成了多少。":
        "Each of the 9 entries opens: which step, who, to what value.",

    # ---- figure 2
    "一次读、一次写，长什么样": "One read, one write",
    "程序把数递出来，界面把数改回去。同一根线，两个方向，规矩不一样。":
        "The program hands a value out; the interface hands one back. One line, two directions.",
    "界线": "boundary",
    "程序内部": "inside the program",
    "你看到的界面": "what you see",
    "每写一次快照，往后加一行": "one row appended per snapshot",
    "纯文本，不用装额外的库": "plain text, no reader needed",
    "一张场的缩略图": "a reduced frame",
    "120 像素宽，每走一步换一张": "120 px wide, one per step",
    "画成图片 / 字符画都行": "an image, or an ASCII field",
    "多久一次 · 多大 · 凭什么知道": "cadence · size · how you know",
    "读出来": "read",
    "程序每走一步瞧一眼，下一步生效": "checked each step, applied at the next",
    "改成功了": "accepted",
    "一个滑杆，拖到 900": "a slider, dragged to 900",
    "松手才提交，拖着的过程不算数": "committed on release, not while dragging",
    "范围 5 – 2000，跑着也能改": "range 5 – 2000, writable mid-run",
    "滑杆 · 5–2000 · 随时能改": "slider · 5–2000 · mid-run",
    "写回去": "write",
    "改不动": "refused",
    "这个请求根本没送进去：": "the request never got in:",
    "在门口就被挡住了。": "stopped at the boundary.",
    "一个滑杆，拖到 60": "a slider, dragged to 60",
    "它和上面那个长得一模一样。": "it looks exactly like the one above.",
    "这个参数在启动时就定死了": "this one is fixed at start-up",
    "启动后不能改": "locked after start-up",
    "被挡下": "refused",
    "能改的和不能改的，长得一模一样": "A writable control and a locked one look identical",

    # ---- figure 3
    "问三个问题，只剩四种控件": "Three questions, four controls",
    "做个界面不难，难的是不瞎猜。三个问题问完，答案只有四种 —— 这是穷举的结果。":
        "Building a surface is easy; not guessing is hard. Three questions, and the answer is one of four.",
    "① 能不能改？": "1  can it be written?",
    "有没有东西把它读回去": "does anything read it back",
    "只读，没人读它": "read-only, nothing reads it",
    "→ 只能看": "→ readout",
    "能改，程序会读回去": "writable, read back by the code",
    "→ 问第二个": "→ ask question 2",
    "说不清": "cannot tell",
    "→ 留空": "→ unresolved",
    "② 能填什么？": "2  what can it hold?",
    "它的取值长什么样": "the shape of its domain",
    "没有值，只是一个动作": "no value, just an action",
    "→ 按钮": "→ button",
    "几个选项里挑一个": "one of a few options",
    "→ 下拉": "→ select",
    "一段范围里的连续值": "a continuous range",
    "→ 滑杆": "→ slider",
    "一段话 / 一个文件 / 没范围": "text / a file / unbounded",
    "③ 什么时候能改？": "3  when can it change?",
    "启动前，还是跑着也能改": "at start-up, or while running",
    "启动前定死": "fixed at start-up",
    "→ 灰掉": "→ disabled",
    "跑着随时能改": "writable at any time",
    "→ 能拖": "→ draggable",
    "停在两步之间才能改": "only between two steps",
    "三个答案": "three answers",
    "定下控件": "settle the control",
    "不用猜": "nothing to guess",
    "只有这四种": "only these four",
    "按钮": "button",
    "一个动作，没有值要填": "an action, no value",
    "滑杆": "slider",
    "一段范围里连续调": "a continuous range",
    "下拉": "select",
    "读数": "readout",
    "只能看，不能改": "read-only",
    "数字、曲线、图": "number, curve, image",
    "三个问题有一个答不上来 → 留空，并且写在界面上":
        "One unanswered question → unresolved, and say so on the surface",
    "猜出来的滑杆比没有滑杆更糟：它让人以为自己能控制。":
        "A guessed slider is worse than no slider: it looks like control.",

    # ---- figure 4
    "什么时候能改": "When can it change",
    "同一个参数，三种情况。看起来一模一样，用起来完全不同。":
        "One parameter, three cases. Identical on screen, completely different in use.",
    "提交前": "before submit",
    "刚启动": "just started",
    "跑着": "running",
    "结束": "finished",
    "启动时定死": "fixed at start-up",
    "能改": "writable",
    "改不动了：分辨率在启动时就定了": "refused: the grid was built at start-up",
    "随时能改": "writable at any time",
    "两步之间才能改": "only between two steps",
    "没地方插": "nowhere to hook",
    "只在两步之间那一下": "only between two steps",
    "没有下一步了": "no next step",
    "改不动 —— 但会留一条记录，说明你试过":
        "refused — but recorded, so the attempt is visible",
    "能改的和不能改的，外观没有区别。": "A writable control and a locked one look the same.",

    # ---- page furniture
    "看得见的界线": "the visible seam",
}


# ---- sentences assembled from two source lines (implicit concatenation)
ASSEMBLED = {
    '所以「能不能改」必须写在界面上，不能只埋在后台。后台知道、你不不知道，结果就是你以为在调，其实什么也没发生。':
        'So it has to be shown on the control, never left inside the adapter. If only the adapter knows, you drag a dead slider and nothing happens.',
    '还有一条容易漏的：被拒绝也是一次操作，也要记下来 —— 「没试过」和「试了被挡」是两件事。':
        'One more thing is easy to miss: a refusal is a crossing too, and it is recorded — "never tried" and "tried and refused" are different facts.',
    '想要第五种控件，得先举出一个前三个问题都装不下的例子 —— 那正是这个项目最想收到的批评。':
        'A fifth control needs an example the first three questions cannot hold — and that is the report this project most wants.',
    '把「能不能改」只告诉后台、不告诉操作者，等于把一次静默失败包装成一次成功。':
        'Telling the adapter but not the operator turns a silent failure into a success.',
}
EN.update(ASSEMBLED)
