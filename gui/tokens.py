from enum import IntEnum


class ResponseToken(IntEnum):
    """Tokens used to identify commands given to the GDB Machine Interface and decide what to do with the result.
    The first part of the token name shows who triggered the command, the second part denotes its destination"""
    # Discard result
    DELETE = 0
    # Command originated by user, add to main output widget
    USER_MAIN = 1
    # Command originated by us, add to main output widget
    GUI_MAIN_CONTEXT = 2
    GUI_DISASM_CONTEXT = 3
    GUI_CODE_CONTEXT = 4
    GUI_REGS_CONTEXT = 5
    GUI_STACK_CONTEXT = 6
    GUI_BACKTRACE_CONTEXT = 7
    GUI_HEAP_HEAP = 8
    GUI_HEAP_BINS = 9
    GUI_HEAP_TRY_MALLOC = 10
    GUI_HEAP_TRY_FREE = 11

    def __str__(self):
        return str(self.value)


Token_to_Context = {
    ResponseToken.USER_MAIN: "main",
    ResponseToken.GUI_MAIN_CONTEXT: "main",
    ResponseToken.GUI_DISASM_CONTEXT: "disasm",
    ResponseToken.GUI_CODE_CONTEXT: "code",
    ResponseToken.GUI_REGS_CONTEXT: "regs",
    ResponseToken.GUI_BACKTRACE_CONTEXT: "backtrace",
    ResponseToken.GUI_STACK_CONTEXT: "stack",
}

Context_to_Token = dict(map(reversed, Token_to_Context.items()))
