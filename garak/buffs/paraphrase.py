#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

""" Buff that paraphrases a prompt. """

from collections.abc import Iterable
import copy

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transformers import PegasusForConditionalGeneration, PegasusTokenizer

import garak.attempt
from garak.buffs.base import Buff


class PegasusT5(Buff):
    """Paraphrasing buff using Pegasus model"""

    bcp47 = "en"
    uri = "https://huggingface.co/tuner007/pegasus_paraphrase"

    def __init__(self) -> None:
        super().__init__()
        self.para_model_name = "tuner007/pegasus_paraphrase"  # https://huggingface.co/tuner007/pegasus_paraphrase
        self.torch_device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_length = 60
        self.temperature = 1.5
        self.num_return_sequences = 6
        self.num_beams = self.num_return_sequences
        self.tokenizer = PegasusTokenizer.from_pretrained(self.para_model_name)
        self.para_model = PegasusForConditionalGeneration.from_pretrained(
            self.para_model_name
        ).to(self.torch_device)

    def _get_response(self, input_text):
        batch = self.tokenizer(
            [input_text],
            truncation=True,
            padding="longest",
            max_length=self.max_length,
            return_tensors="pt",
        ).to(self.torch_device)
        translated = self.para_model.generate(
            **batch,
            max_length=self.max_length,
            num_beams=self.num_beams,
            num_return_sequences=self.num_return_sequences,
            temperature=self.temperature,
        )
        tgt_text = self.tokenizer.batch_decode(translated, skip_special_tokens=True)
        return tgt_text

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        yield self._derive_new_attempt(attempt)
        paraphrases = self._get_response(attempt.prompt)
        for paraphrase in set(paraphrases):
            paraphrased_attempt = self._derive_new_attempt(attempt)
            paraphrased_attempt.prompt = paraphrase
            yield paraphrased_attempt


class Fast(Buff):
    """CPU-friendly paraphrase buff based on Humarin's T5 paraphraser"""

    bcp47 = "en"
    uri = "https://huggingface.co/humarin/chatgpt_paraphraser_on_T5_base"

    def __init__(self) -> None:
        super().__init__()
        self.para_model_name = "humarin/chatgpt_paraphraser_on_T5_base"
        self.torch_device = "cuda" if torch.cuda.is_available() else "cpu"
        self.num_beams = 5
        self.num_beam_groups = 5
        self.num_return_sequences = 5
        self.repetition_penalty = 10.0
        self.diversity_penalty = 3.0
        self.no_repeat_ngram_size = 2
        # self.temperature = 0.7
        self.max_length = 128
        self.tokenizer = AutoTokenizer.from_pretrained(self.para_model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.para_model_name).to(
            self.torch_device
        )

    def _get_response(self, input_text):
        input_ids = self.tokenizer(
            f"paraphrase: {input_text}",
            return_tensors="pt",
            padding="longest",
            max_length=self.max_length,
            truncation=True,
        ).input_ids

        outputs = self.model.generate(
            input_ids,
            # temperature=self.temperature,
            repetition_penalty=self.repetition_penalty,
            num_return_sequences=self.num_return_sequences,
            no_repeat_ngram_size=self.no_repeat_ngram_size,
            num_beams=self.num_beams,
            num_beam_groups=self.num_beam_groups,
            max_length=self.max_length,
            diversity_penalty=self.diversity_penalty,
            # do_sample = False,
        )

        res = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)

        return res

    def transform(
        self, attempt: garak.attempt.Attempt
    ) -> Iterable[garak.attempt.Attempt]:
        yield self._derive_new_attempt(attempt)
        paraphrases = self._get_response(attempt.prompt)
        for paraphrase in set(paraphrases):
            paraphrased_attempt = self._derive_new_attempt(attempt)
            paraphrased_attempt.prompt = paraphrase
            yield paraphrased_attempt
