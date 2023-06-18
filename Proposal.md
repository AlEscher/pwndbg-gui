# Pwndbg GUI

## Motivation

`pwndbg` is a command line utility that enhances `gdb` by allowing the user to more easily view data, as well as by adding various new commands.
However, with it being a command line tool it comes with various restrictions regarding usability.
[Splitting contexts](https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context) using `tmux` and `splitmind` can help by allowing multiple contexts to be displayed at the same time, however these techniques bring new issues.
Simple things such as copying multiple lines of data, viewing previous states and generally customizing the layout and sizes of the contexts are either impossible or impractical.  
Having a GUI application would allow using all of `pwndbg`'s functionality, while offering the ease of use and usability of a typical GUI interface.

### Existing alternatives


## Approach

The idea is to build a wrapper around `pwndbg` using the [Qt](https://doc.qt.io/qtforpython-6/) framework.
The user would need to setup `pwndbg` on their system once and then start the GUI, which invokes `gdb`.

## Features

- [ ] Multi pane setup similar to [Splitting contexts](https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context)
- [ ] Resizable, scrollable panes
- [ ] Allow to start a local executable, or attach to an already running one (latter requires `sudo`)
- [ ] Add `fs_base` to register section
- [ ] Convenience buttons (maybe hotkeys) / fields for `c`, `r`, `n`, `s`, `ni`, `si`, `search`
- [ ] +/- buttons for adding `pwndbg` context-stack lines
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
- 