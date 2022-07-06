def log_prompt(prompt: str, message: str):
    print("(rsprof)", prompt, message)


def info(message: str):
    log_prompt("\033[0;34mINFO\033[0m", message)


def warn(message: str):
    log_prompt("\033[0;33mWARN\033[0m", message)


def fail(message: str):
    log_prompt("\033[0;31mFAIL\033[0m", message)


def panic(message: str):
    log_prompt("\033[0;31mFAIL\033[0m", message)
    exit(0)
