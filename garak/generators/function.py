#!/usr/bin/env python3
"""function-based generator

Call a given function to use as a generator; specify this as either the 
model name on the command line, or as the parameter to the constructor.
"""


import importlib
from typing import List

from garak.generators.base import Generator


class Single(Generator):
    """pass a module#function to be called as generator, with format function(prompt:str, **kwargs)->str"""

    uri = "https://github.com/leondz/garak/issues/137"
    generator_family_name = "function"
    supports_multiple_generations = False

    def __init__(self, name="", **kwargs):  # name="", generations=self.generations):
        gen_module_name, gen_function_name = name.split("#")
        if "generations" in kwargs:
            self.generations = kwargs["generations"]
            del kwargs["generations"]

        self.kwargs = kwargs

        gen_module = importlib.import_module(gen_module_name)
        self.generator = getattr(gen_module, gen_function_name)

        super().__init__(name, generations=self.generations)

    def _call_model(self, prompt: str) -> str:
        return self.generator(prompt, **self.kwargs)


class Multiple(Single):
    """pass a module#function to be called as generator, with format function(prompt:str, generations:int, **kwargs)->List[str]"""

    supports_multiple_generations = True

    def _call_model(self, prompt) -> List[str]:
        return self.generator(prompt, generations=self.generations, **self.kwargs)


default_class = "Single"
