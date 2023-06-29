from enum import Enum


class ResponseToken(Enum):
    DELETE = 0
    MAIN_USER = 1
    MAIN_GUI = 2
    DISASM_GUI = 3
    CODE_GUI = 4
    REGS_GUI = 5
    STACK_GUI = 6
    BACKTRACE_GUI = 7


Token_to_Context = {
    ResponseToken.MAIN_USER.value(): "main",
    ResponseToken.MAIN_GUI.value(): "main",
    ResponseToken.DISASM_GUI.value(): "disasm",
    ResponseToken.CODE_GUI.value(): "code",
    ResponseToken.REGS_GUI.value(): "regs",
    ResponseToken.BACKTRACE_GUI.value(): "backtrace",
    ResponseToken.STACK_GUI.value(): "stack",
}