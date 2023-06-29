from enum import Enum


class ResponseToken(Enum):
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


Token_to_Context = {
    ResponseToken.USER_MAIN.value(): "main",
    ResponseToken.GUI_MAIN_CONTEXT.value(): "main",
    ResponseToken.GUI_DISASM_CONTEXT.value(): "disasm",
    ResponseToken.GUI_CODE_CONTEXT.value(): "code",
    ResponseToken.GUI_REGS_CONTEXT.value(): "regs",
    ResponseToken.GUI_BACKTRACE_CONTEXT.value(): "backtrace",
    ResponseToken.GUI_STACK_CONTEXT.value(): "stack",
}