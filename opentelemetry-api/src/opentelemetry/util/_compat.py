# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

import functools
import inspect
import keyword
import logging
import sys
from abc import ABC
from collections.abc import Callable, Iterator, Mapping
from typing import Any

_logger = logging.getLogger(__name__)

if sys.version_info >= (3, 14):
    from annotationlib import Format

    def _signature(fn: Callable[..., Any]) -> inspect.Signature:
        # PEP 649: inspect.signature() evaluates deferred annotations by
        # default, which raises NameError for names that only exist under
        # TYPE_CHECKING. Only parameter names, kinds and defaults are needed.
        return inspect.signature(fn, annotation_format=Format.FORWARDREF)  # pylint: disable=unexpected-keyword-arg

else:

    def _signature(fn: Callable[..., Any]) -> inspect.Signature:
        return inspect.signature(fn)


def _validate_identifier(name: str) -> None:
    if not name.isidentifier() or keyword.iskeyword(name):
        raise ValueError(f"Invalid parameter identifier: {name!r}")


def _build_wrapper_parts(
    sub_params: Mapping[str, inspect.Parameter],
    sub_fn: Callable[..., Any],
) -> tuple[list[str], list[Any], list[str], list[str]]:
    outer_arg_names: list[str] = ["_sub_fn"]
    outer_arg_values: list[Any] = [sub_fn]
    def_parts: list[str] = []
    call_pos_parts: list[str] = []
    call_kw_parts: list[str] = []
    saw_kw_only = False
    pos_only_count = sum(1 for param in sub_params.values() if param.kind is inspect.Parameter.POSITIONAL_ONLY)
    seen_pos_only = 0

    for name, param in sub_params.items():
        _validate_identifier(name)

        if param.kind is inspect.Parameter.POSITIONAL_ONLY:
            seen_pos_only += 1
            call_pos_parts.append(name)
        elif param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
            call_pos_parts.append(name)
        elif param.kind is inspect.Parameter.VAR_POSITIONAL:
            call_pos_parts.append(f"*{name}")
        elif param.kind is inspect.Parameter.KEYWORD_ONLY:
            if not saw_kw_only:
                def_parts.append("*")
                saw_kw_only = True
            call_kw_parts.append(f"{name}={name}")

        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            def_parts.append(f"*{name}")
            saw_kw_only = True
        elif param.default is not inspect.Parameter.empty:
            default_var = f"_d_{name}"
            outer_arg_names.append(default_var)
            outer_arg_values.append(param.default)
            def_parts.append(f"{name}={default_var}")
        else:
            def_parts.append(name)

        if param.kind is inspect.Parameter.POSITIONAL_ONLY and seen_pos_only == pos_only_count:
            def_parts.append("/")

    varkw_name = "_kwargs"
    while varkw_name in sub_params:
        varkw_name = f"_{varkw_name}"
    def_parts.append(f"**{varkw_name}")

    return outer_arg_names, outer_arg_values, def_parts, call_pos_parts + call_kw_parts


def make_signature_compat_wrapper(
    sub_fn: Callable[..., Any],
    *,
    qualname: str | None = None,
) -> Callable[..., Any] | None:
    """Create a fast forwarding wrapper if ``sub_fn`` does not accept ``**kwargs``.

    Generates a wrapper with ``sub_fn``'s exact signature plus a trailing ``**_kwargs``
    parameter that forwards all declared positional and keyword arguments directly
    to ``sub_fn`` via CPython's ``vectorcall`` fast path.

    Returns ``None`` if ``sub_fn`` already accepts ``**kwargs``, incurring zero
    runtime overhead.
    """
    sub_params = _signature(sub_fn).parameters
    if any(param.kind is inspect.Parameter.VAR_KEYWORD for param in sub_params.values()):
        return None

    fn_name = getattr(sub_fn, "__name__", "_compat_fn")
    _validate_identifier(fn_name)

    outer_arg_names, outer_arg_values, def_parts, call_parts = _build_wrapper_parts(sub_params, sub_fn)
    target_qualname = qualname or getattr(sub_fn, "__qualname__", fn_name)
    src = (
        f"def __create_compat_fn__({', '.join(outer_arg_names)}):\n"
        f"    def {fn_name}({', '.join(def_parts)}):\n"
        f"        return _sub_fn({', '.join(call_parts)})\n"
        f"    return {fn_name}\n"
    )
    namespace: dict[str, Any] = {}
    exec(compile(src, f"<compat {target_qualname}>", "exec"), {"__builtins__": {}}, namespace)  # noqa: S102  # pylint: disable=exec-used
    wrapper: Callable[..., Any] = namespace["__create_compat_fn__"](*outer_arg_values)
    functools.update_wrapper(wrapper, sub_fn)
    return wrapper


def _compat_bases(cls: type) -> list[type]:
    """Ancestors of ``cls`` (nearest first) that take part in signature compatibility."""
    return [base for base in cls.__mro__[1:] if base is not SignatureCompatABC and issubclass(base, SignatureCompatABC)]


def _adaptable_methods(cls: type) -> Iterator[tuple[str, Callable[..., Any]]]:
    """Yield ``(name, implementation)`` for public ABC methods ``cls`` may need adapted.

    Walks the public methods declared by the compatibility-aware ancestors of
    ``cls`` and resolves the implementation ``cls`` actually uses, so that
    overrides inherited from plain mixins are adapted too. Implementations
    inherited from a compatibility-aware ancestor were already handled when that
    ancestor was defined.
    """
    compat_bases = _compat_bases(cls)
    seen: set[str] = set()
    for base in compat_bases:
        for name in base.__dict__:
            if name in seen or name.startswith("_") or not inspect.isfunction(base.__dict__[name]):
                continue
            seen.add(name)

            owner = cls
            for klass in cls.__mro__:
                if name in klass.__dict__:
                    owner = klass
                    break
            if owner is not cls and owner in compat_bases:
                continue
            sub_fn = owner.__dict__[name]
            if not inspect.isfunction(sub_fn) or getattr(sub_fn, "__isabstractmethod__", False):
                continue

            yield name, sub_fn


class SignatureCompatABC(ABC):
    """ABC base class that keeps subclass method signatures forward-compatible.

    When a subclass implements a public method of the base without accepting
    ``**kwargs``, the method is replaced on the subclass with a generated wrapper
    that accepts ``sub_fn``'s exact signature plus ``**_kwargs`` and forwards the
    declared parameters directly. Subclasses that accept ``**kwargs`` are left
    untouched.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        for name, sub_fn in _adaptable_methods(cls):
            qualname = f"{cls.__qualname__}.{name}"
            try:
                wrapper = make_signature_compat_wrapper(sub_fn, qualname=qualname)
            except Exception:  # pylint: disable=broad-exception-caught
                # Best effort: never let the shim itself break defining a subclass.
                _logger.debug("Not adapting %s", qualname, exc_info=True)
                continue
            if wrapper is not None:
                setattr(cls, name, wrapper)
