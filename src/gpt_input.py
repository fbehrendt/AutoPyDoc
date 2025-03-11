from dataclasses import dataclass, field


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class GptInputMethodObject(GptInputCodeObject):
    parameters: list[str] | None = field(default=None, compare=True, hash=True)
    missing_parameters: list | None = field(default=None, hash=False)
    return_missing: bool = field(default=False, hash=False)
    parent_class_id: str | None = field(default=None, compare=True, hash=True)
    parent_module_id: str | None = field(default=None, compare=True, hash=True)


@dataclass(frozen=True)
class GptInputClassObject(GptInputCodeObject):
    parent_class_id: str | None = field(default=None, compare=True, hash=True)
    parent_module_id: str | None = field(default=None, compare=True, hash=True)
    inherited_from: str | None = field(default=None, compare=True, hash=True)
    class_ids: set = field(default_factory=set, compare=True, hash=True)
    method_ids: set = field(default_factory=set, compare=True, hash=True)
    class_attributes: dict = field(default_factory=dict, compare=True, hash=True)
    instance_attributes: dict = field(default_factory=dict, compare=True, hash=True)
    missing_class_attribute_types: dict[str, str] = field(
        default_factory=dict, compare=True, hash=True
    )
    missing_instance_attributes_types: dict[str, str] = field(
        default_factory=dict, compare=True, hash=True
    )


@dataclass(frozen=True)
class GptInputModuleObject(GptInputCodeObject):
    class_ids: set = field(default_factory=set, compare=True, hash=True)
    method_ids: set = field(default_factory=set, compare=True, hash=True)


@dataclass(frozen=True)
class GptOutput:
    id: str = field(compare=True, hash=True)
    no_change_necessary: bool = field(compare=True, hash=True)
    description: str


@dataclass(frozen=True)
class GptOutputMethod(GptOutput):
    parameter_types: dict[str, str]
    parameter_descriptions: dict[str, str]
    exception_descriptions: dict[str, str]
    return_description: str
    return_missing: bool
    return_type: str = field(default=None)


@dataclass(frozen=True)
class GptOutputClass(GptOutput):
    class_attribute_descriptions: dict[str, str]
    class_attribute_types: dict[str, str]
    instance_attribute_descriptions: dict[str, str]
    instance_attribute_types: dict[str, str]


@dataclass(frozen=True)
class GptOutputModule(GptOutput):
    exception_descriptions: dict[str, str]
