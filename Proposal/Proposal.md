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

## Approach

The idea is to build a wrapper around `pwndbg` using the [Qt](https://doc.qt.io/qtforpython-6/) framework.
The user would need to setup `pwndbg` on their system once and then start the GUI, which invokes `gdb`.
All interaction would then only be done through the GUI, which forwards the specific commands and presents the output accordingly. 
This allows us to aggregate and customize output and simplify command input (e.g. buttons).

## Features

- [x] Multi pane setup similar to [Splitting contexts](https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context)
- [x] Resizable, scrollable panes
- [x] Allow to start a local executable
- [x] Allow attaching to an already running program
  - Functionality is implemented, but requires `sudo` which is problematic for python modules
  - Inferior communication may require changes
- [x] Include banners/header for panes
- [x] Add `fs_base` to register section
- [x] Convenience buttons (maybe hotkeys) / fields for `c`, `r`, `n`, `s`, `ni`, `si`
- [x] Add a `search` functionality
- [x] Add a context menu to `stack`/`regs` to allow copy and display information about data (e.g. offsets)
- [x] +/- buttons for adding `pwndbg` context-stack lines
- [x] New context: Heap
    - Add a new context to the ones `pwndbg` already offers (stack, backtrace, etc...) for the heap
    - Continuously show heap related information (`heap` command, `main_arena`, fastbins, smallbins)
    - Also allow to use `pwndbgs`'s `try_free`
- [x] New context: `hexdump`
    - Allow the user to actively "Watch" a number of addresses via hexdump
    - Increase / Decrease number of lines shown via GUI buttons

## Additional (possibly future) Features

- Easier inputting of payloads (e.g. via files)
- Setting breakpoint in source or disassembly via GUI
- Customize contexts arrangement
  - Pop out contexts into separate windows
  - Rearrange and move contexts around in the GUI
- Remember layout on startup
  - Sizes of splitters
  - Arrangement of contexts (custom context layout not yet supported)
- Editing of memory (e.g. registers, stack, heap) via UI (e.g. double-click on stack line)