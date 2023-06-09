from transformers import T5Tokenizer, AutoModelForCausalLM
import torch

import logging
import os
import sys
from dataclasses import dataclass, field
from itertools import chain
from typing import Optional
from arguments import ModelArguments, PromptArguments

logger = logging.getLogger(__name__)
# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
# log_level = training_args.get_process_log_level()
logger.setLevel(50)
# log_level = training_args.get_process_log_level()
# logger.setLevel(log_level)

import transformers
import datasets
from transformers import (
    CONFIG_MAPPING,
    MODEL_FOR_CAUSAL_LM_MAPPING,
    AutoConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    HfArgumentParser,
    Trainer,
    TrainingArguments,
    default_data_collator,
    is_torch_tpu_available,
    set_seed,
)

from utils import get_tokenizer, get_model

def inference(
    tokenizer,
    model,
    prompt: str,
    num_return_sequences: int
):
    # prompt = "タイトル「独身女性が"
    # num = 3
    model.eval()
    # tokenizer = T5Tokenizer.from_pretrained("rinna/japanese-gpt1-medium")
    tokenizer.do_lower_case = True

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    input_ids = tokenizer.encode(
        prompt,
        return_tensors="pt",
        add_special_tokens=False
    ).to(device)
    model.to(device)

    # print('input_ids', input_ids)

    with torch.no_grad():
        output = model.generate(
            input_ids,
            max_length=500,
            min_length=500,
            do_sample=True,
            top_k=500,
            top_p=0.95,
            pad_token_id=tokenizer.pad_token_id,
            bos_token_id=tokenizer.bos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            num_return_sequences=num_return_sequences
        )
    decoded = tokenizer.batch_decode(
        output,
        skip_special_tokens=True
    )
    return decoded


def main():
    # See all possible arguments in src/transformers/training_args.py
    # or by passing the --help flag to this script.
    # We now keep distinct sets of args, for a cleaner separation of concerns.

    parser = HfArgumentParser((ModelArguments, TrainingArguments, PromptArguments))
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # If we pass only one argument to the script and it's the path to a json file,
        # let's parse it to get our arguments.
        model_args, training_args, prompt_arg = parser.parse_json_file(
            json_file=os.path.abspath(sys.argv[1])
        )
    else:
        model_args, training_args, prompt_arg = parser.parse_args_into_dataclasses()

    if training_args.should_log:
        # The default of training_args.log_level is passive, so we set log level at info here to have that default.
        transformers.utils.logging.set_verbosity_info()

    # datasets.utils.logging.set_verbosity(log_level)
    # transformers.utils.logging.set_verbosity(log_level)
    transformers.utils.logging.enable_default_handler()
    transformers.utils.logging.enable_explicit_format()

    # Log on each process the small summary:
    logger.warning(
        f"Process rank: {training_args.local_rank}, device: {training_args.device}, n_gpu: {training_args.n_gpu}"
        + f"distributed training: {bool(training_args.local_rank != -1)}, 16-bits training: {training_args.fp16}"
    )
    logger.info(f"Training/evaluation parameters {training_args}")

    # Detecting last checkpoint.
    last_checkpoint = None
    if os.path.isdir(training_args.output_dir) and training_args.do_train and not training_args.overwrite_output_dir:
        last_checkpoint = get_last_checkpoint(training_args.output_dir)
        if last_checkpoint is None and len(os.listdir(training_args.output_dir)) > 0:
            raise ValueError(
                f"Output directory ({training_args.output_dir}) already exists and is not empty. "
                "Use --overwrite_output_dir to overcome."
            )
        elif last_checkpoint is not None and training_args.resume_from_checkpoint is None:
            logger.info(
                f"Checkpoint detected, resuming training at {last_checkpoint}. To avoid this behavior, change "
                "the `--output_dir` or add `--overwrite_output_dir` to train from scratch."
            )

    model = get_model(model_args)
    tokenizer = get_tokenizer(model_args)

    # print(type(tokenizer))
    # print(type(model))
    completion = inference(
        tokenizer,
        model,
        prompt_arg.prompt,
        num_return_sequences=3
    )

    return completion
    

if __name__ == '__main__':

    completions = main()
    for i, c_loop in enumerate(completions):
        
        print(f'completion {str(i)} : ', c_loop)
