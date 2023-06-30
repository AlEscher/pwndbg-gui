# pwndbg-gui

## Setup

- Install and setup [pwndbg](https://github.com/pwndbg/pwndbg/tree/44d75e3bd6d9741daf87c933275369fcfeaeebe7#how)
- Optionally add any settings you want in `~/.gdbinit`
- Run `python start.py`
  - This will create a virtual environment and install the needed dependencies
  - On Debian/Ubuntu systems, you may need to previously install `python3-venv`
  - If you want to attach to running programs, GDB needs to be started with sudo. To do this, run `python start.py --sudo` and enter your sudo password when prompted

## Features

- Resizable and collapsible panes
- Heap context
  - Continuously show heap related information such as allocated chunks and freed bins
  - Give easy access to `pwndbg`'s `try_free` command
- Watch context
  - Add multiple addresses to a watch context to continuously monitor the data in a hexdump format
- Keyboard shortcuts
  - Shortcuts for GDB commands as well as GUI features
  - Shortcuts are either displayed next to the action in a menu (e.g. `Ctrl + N`) or shown by an underlined letter (pressing `Alt + <LETTER>` will activate the button / menu)
- Input byte literals
  - When inputting to the inferior process (denoted by the label next to the main pane's input field) you can supply a python `bytes` literal
  - E.g.: Writing b"Hello\x00World\n" will interpret the input as a `bytes` literal and evaluate it accordingly
- All existing GDB / `pwndbg` commands can still be executed via the Main input widget

## Preview

TODO: Screenshots

## Motivation

`pwndbg` is a command line utility that enhances `gdb` by allowing the user to more easily view data, as well as by adding various new commands.
However, with it being a command line tool it comes with various restrictions regarding usability.
Especially the multitasking and customizability suffers in text-based terminal applications since they are by design bound to the limits of terminal representation.

By default `pwndbg` prints everything to the same terminal. This makes the space for the different contexts of `pwndbg` limited.
If you want to have a scrolling free experience you need to limit yourself to the screensize or adjust the terminal font-size.
[Splitting contexts](https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context) using `tmux` and `splitmind` can help mitigating some headaches by allowing multiple contexts to be displayed at the same time in different terminals, however these tools are still bound by terminal limitations.
Simple things such as copying multiple lines of data, viewing previous states and switching between the context windows to adapt sizes of the contexts are either impossible or cumbersome.  

While `pwndbg` already simplified overused commands in gdb, there are still a lot of commands that need to be typed often and can have complex outputs like heap commands (`heap`, `bins`, etc.) or `vmmap`. 
By introducing a GUI layer on top of `pwndbg` we can filter out, reorder and customize the gdb output.

Having a GUI application would not only allow using `pwndbg`'s functionality in a simplified, more streamlined way, but also allows for advantages a typical GUI interface has like interacting with the filesystem easily or rich media support.
A GUI is also more intuitive to use, having the user remember fewer commands and hiding unnecessary output.
