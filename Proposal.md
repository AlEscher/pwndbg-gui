# Pwndbg GUI

## Motivation

`pwndbg` is a command line utility that enhances `gdb` by allowing the user to more easily view data, as well as by adding various new commands.
However, with it being a command line tool it comes with various restrictions regarding usability.
[Splitting context](https://github.com/pwndbg/pwndbg/blob/dev/FEATURES.md#splitting--layouting-context) using `tmux` and `splitmind` can help by allowing multiple contexts to be displayed at the same time, however these techniques bring new issues.
Simple things such as copying multiple lines of data, viewing previous states and generally customizing the layout and sizes of the contexts are either impossible or impractical.  
Having a GUI application would allow using all of `pwndbg`'s functionality, while offering the ease of use and usability of a typical GUi interface.

## Approach

The idea is to build a wrapper around `pwndbg` using the [Qt](https://doc.qt.io/qtforpython-6/) framework.

## Features

- [ ] 1
- [ ] 2

## Additional Features

- 3
- 4