# Pwndbg GUI

## Motivation

`pwndbg` is a command line utility that enhances `gdb` by allowing the user to more easily view data, as well as by adding various new commands.
However, with it being a command line tool it comes with various restrictions regarding usability.
Especially the multitasking and customizability sufferes in text-based terminal applications since they are by design bound to the limits of terminal representation.

By default `pwndbg` prints everything to the same terminal, just pushing old output out the top. This makes the space for the different contexts of `pwndbg` extremly limited.
If you want to have a scrolling free experience you need to limit yourself to the screensize or adjust the terminal font-size.
[Splitting contexts](https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context) using `tmux` and `splitmind` can help mitigating some headaches by allowing multiple contexts to be displayed at the same time in different terminals, however these tools are still bound by terminal limitations.
Simple things such as copying multiple lines of data, viewing previous states and switching bewteen the context windows to adapt sizes of the contexts are either impossible or cumbersome.  

While `pwndbg` already simplified overused commands in gdb, there are still a lot of commands that need to be typed often and can have complex outputs like heap commands (`heap`, `bins`, etc.) or `vmmap`. 
By introducing a GUI layer ontop of `pwndbg` we can filter out, reorder and customize the gdb output.

Having a GUI application would not only allow using `pwndbg`'s functionality in a simplified, more streamlined way, but also allows for advantages a typical GUI interface has like interacting with the filesystem easily or rich media support.
A GUI is also more intuitive to use, having the user remember less commands and hiding unnecessary output.

## Existing alternatives

There are **a lot** of plugins, addons and programs that try to ease the use of `gdb`. 
However most stick to the terminal approach to visualise different contexts like [splitmind](https://github.com/jerdna-regeiz/splitmind), [GDB Dashboard](https://github.com/cyrus-and/gdb-dashboard) or [Hyperpwn](https://github.com/bet4it/hyperpwn).

We have not found a `pwndbg` specific GUI, but some standalone GUI programs for debugging with gdb like [gdbGUI](https://www.gdbgui.com/), [KDbg](https://www.kdbg.org/), or [Nemiver](https://wiki.gnome.org/Apps/Nemiver).
However in our experience they were buggy, non intuitve and tailored more towards general debugging instead of reversing/pwning.

Of course there are alternatives to `pwndbg` in general like [GEF](https://hugsy.github.io/gef/), however they suffer from similar issues as descibed above or are only integrated into more complex IDEs. ([CLion](https://www.jetbrains.com/clion/), [Eclipse](https://github.com/eclipse-cdt/), etc.)

## Approach

The idea is to build a wrapper around `pwndbg` using the [Qt](https://doc.qt.io/qtforpython-6/) framework.
The user would need to setup `pwndbg` on their system once and then start the GUI, which invokes `gdb`.
All interaction would then only be done through the GUI, which forwards the specific commands and presents the output accordingly. 
This allows us to aggregate and customize output and simplify command input (e.g. buttons).

## Features

- [ ] Multi pane setup similar to [Splitting contexts](https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context)
- [x] Resizable, scrollable panes
- [x] Allow to start a local executable, or attach to an already running one (latter requires `sudo`)
- [X] Include banners/header for panes
- [ ] ~~Add `fs_base` to register section~~ (Crashes GDB for some reason `Recursive internal problem.`)
- [ ] Convenience buttons (maybe hotkeys) / fields for `c`, `r`, `n`, `s`, `ni`, `si`, `search`
- [x] +/- buttons for adding `pwndbg` context-stack lines
- [ ] Editing of memory (e.g. registers, stack, heap) via UI (e.g. double-click on stack line)
- [ ] New context: Heap
    - Add a new context to the ones `pwndbg` already offers (stack, backtrace, etc...) for the heap
    - Continuosly show heap related information (`heap` command, `main_arena`, fastbins, smallbins)
    - Also allow to use `pwndbgs`'s `try_malloc` and `try_free`
- [ ] New context: `hexdump`
    - Allow the user to actively "Watch" a number of addresses via hexdump
    - Increase / Decrease number of lines shown via GUI buttons

## Additional (optional) Features

- Easier inputting of payloads (e.g. via files)
- setting breakpoint in source or disassembly via GUI