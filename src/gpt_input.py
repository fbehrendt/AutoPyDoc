from dataclasses import dataclass, field


@dataclass(frozen=True)
class GptInputCodeObject:
    id: int = field(compare=True, hash=True)  #  = field(default_factory=build_id)
    code_type: str = field(compare=True, hash=True)
    name: str = field(compare=True, hash=True)
    code: str = field(hash=False)
    docstring: str | None = field(default=None, hash=False)
    context: dict[str, list[int] | int] | None = field(default=None, hash=False)
    context_objects: dict | None = field(default=None, hash=False)


@dataclass(frozen=True)
class GptInputMethodObject(GptInputCodeObject):
    parameters: list[str] | None = field(default=None, compare=True, hash=True)
    missing_parameters: list[str] | None = field(default=None, hash=False)
    return_missing: bool = field(default=False, hash=False)
    parent_class_id: int | None = field(default=None, compare=True, hash=True)
    parent_module_id: int | None = field(default=None, compare=True, hash=True)
    parent_method_id: int | None = field(default=None, compare=True, hash=True)
    exceptions: set | None = field(default=None, compare=True, hash=True)


@dataclass(frozen=True)
class GptInputClassObject(GptInputCodeObject):
    parent_method_id: int | None = field(default=None, compare=True, hash=True)
    parent_class_id: int | None = field(default=None, compare=True, hash=True)
    parent_module_id: int | None = field(default=None, compare=True, hash=True)
    inherited_from: int | None = field(default=None, compare=True, hash=True)
    class_ids: set = field(default_factory=set, compare=True, hash=True)
    method_ids: set = field(default_factory=set, compare=True, hash=True)
    class_attributes: dict = field(default_factory=dict, compare=True, hash=True)
    instance_attributes: dict = field(default_factory=dict, compare=True, hash=True)
    missing_class_attribute_types: dict[str, str] = field(  # TODO why is this a dict?
        default_factory=dict, compare=True, hash=True
    )
    missing_instance_attributes_types: dict[str, str] = field(  # TODO why is this a dict?
        default_factory=dict, compare=True, hash=True
    )


@dataclass(frozen=True)
class GptInputModuleObject(GptInputCodeObject):
    class_ids: set = field(default_factory=set, compare=True, hash=True)
    method_ids: set = field(default_factory=set, compare=True, hash=True)
    exceptions: set | None = field(default=None, compare=True, hash=True)


@dataclass(frozen=True)
class GptOutput:
    id: int = field(compare=True, hash=True)
    no_change_necessary: bool = field(compare=True, hash=True)
    description: str | bool = field(compare=False, hash=False)


@dataclass(frozen=True)
class GptOutputMethod(GptOutput):
    parameter_types: dict[str, str | bool] = field(compare=False, hash=False)
    parameter_descriptions: dict[str, str | bool] = field(compare=False, hash=False)
    exception_descriptions: dict[str, str | bool] = field(compare=False, hash=False)
    return_description: str | bool = field(compare=False, hash=False)
    return_type: str | bool | None = field(default=None, compare=False, hash=False)


@dataclass(frozen=True)
class GptOutputClass(GptOutput):
    class_attribute_descriptions: dict[str, str | bool] = field(compare=False, hash=False)
    class_attribute_types: dict[str, str | bool] = field(compare=False, hash=False)
    instance_attribute_descriptions: dict[str, str | bool] = field(compare=False, hash=False)
    instance_attribute_types: dict[str, str | bool] = field(compare=False, hash=False)


@dataclass(frozen=True)
class GptOutputModule(GptOutput):
    exception_descriptions: dict[str, str | bool] = field(compare=False, hash=False)
