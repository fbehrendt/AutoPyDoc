from dataclasses import dataclass, field


@dataclass
class GptInputCodeObject:
    id: str = field(compare=True, hash=True)  #  = field(default_factory=build_id)
    code_type: str = field(compare=True, hash=True)
    name: str = field(compare=True, hash=True)
    code: str = field(hash=False)
    docstring: str | None = field(default=None, hash=False)
    context: dict[str, list[str] | str] | None = field(default=None, hash=False)
    context_docstrings: dict[str, str] | None = field(default=None, hash=False)
    exceptions: list[str] | None = field(default=None, hash=False)

    # def __post_init__(self):
    #     pass


@dataclass
class GptInputMethodObject(GptInputCodeObject):
    parameters: list[str] | None = field(default=None, compare=True, hash=True)
    missing_parameters: list | None = field(default=None, hash=False)
    return_missing: bool = field(default=False, hash=False)
    parent_class_id: str | None = field(default=None, compare=True, hash=True)
    parent_module_id: str | None = field(default=None, compare=True, hash=True)


@dataclass
class GptInputClassObject(GptInputCodeObject):
    parent_class_id: str | None = field(default=None, compare=True, hash=True)
    parent_module_id: str | None = field(default=None, compare=True, hash=True)
    inherited_from: str | None = field(default=None, compare=True, hash=True)
